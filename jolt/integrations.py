"""
JOLT Framework Integrations
Making JOLT work everywhere - like a Swiss Army knife for data formats
"""
from __future__ import annotations
from typing import Any, Dict, Optional, Type, Union, Callable, List
from io import StringIO
import json
import logging
from functools import wraps

logger = logging.getLogger(__name__)

# ============= FastAPI Integration =============
try:
    from fastapi import FastAPI, Request, Response, HTTPException
    from fastapi.responses import PlainTextResponse
    from pydantic import BaseModel
    
    class JoltRequest(BaseModel):
        """Request model for JOLT data"""
        jolt: str
        
    class JoltResponse(PlainTextResponse):
        """Response that returns JOLT formatted data"""
        media_type = "application/jolt"
        
        def __init__(self, 
                    content: Any,
                    encoder: Optional[Callable] = None,
                    **kwargs):
            if encoder:
                jolt_content = encoder(content)
            else:
                from jolt.encoder import json_to_jolt
                jolt_content = json_to_jolt(content)
            super().__init__(content=jolt_content, **kwargs)
    
    def setup_fastapi_jolt(app: FastAPI, 
                          encoder: Optional[Callable] = None,
                          decoder: Optional[Callable] = None):
        """
        Setup JOLT support for FastAPI app
        
        Args:
            app: FastAPI application
            encoder: Custom JOLT encoder
            decoder: Custom JOLT decoder
        """
        if not encoder:
            from jolt.encoder import json_to_jolt
            encoder = json_to_jolt
        
        if not decoder:
            from jolt.decoder import jolt_to_json
            decoder = jolt_to_json
        
        @app.middleware("http")
        async def jolt_middleware(request: Request, call_next):
            """Handle JOLT content type in requests"""
            if request.headers.get("content-type") == "application/jolt":
                body = await request.body()
                try:
                    json_data = decoder(body.decode())
                    # Monkey-patch the request to use JSON data
                    request._body = json.dumps(json_data).encode()
                    request._headers = request.headers.mutablecopy()
                    request._headers["content-type"] = "application/json"
                except Exception as e:
                    logger.error(f"Failed to decode JOLT: {e}")
                    return Response(content="Invalid JOLT format", status_code=400)
            
            response = await call_next(request)
            
            # Convert JSON responses to JOLT if requested
            if request.headers.get("accept") == "application/jolt":
                if response.headers.get("content-type", "").startswith("application/json"):
                    body = b""
                    async for chunk in response.body_iterator:
                        body += chunk
                    try:
                        json_data = json.loads(body)
                        jolt_data = encoder(json_data)
                        return Response(
                            content=jolt_data,
                            media_type="application/jolt",
                            status_code=response.status_code
                        )
                    except Exception as e:
                        logger.error(f"Failed to encode to JOLT: {e}")
            
            return response
        
        logger.info("JOLT support enabled for FastAPI")
    
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


# ============= Flask Integration =============
try:
    from flask import Flask, request, jsonify, Response
    from werkzeug.exceptions import BadRequest
    
    def setup_flask_jolt(app: Flask,
                        encoder: Optional[Callable] = None,
                        decoder: Optional[Callable] = None):
        """
        Setup JOLT support for Flask app
        
        Args:
            app: Flask application
            encoder: Custom JOLT encoder
            decoder: Custom JOLT decoder
        """
        if not encoder:
            from jolt.encoder import json_to_jolt
            encoder = json_to_jolt
        
        if not decoder:
            from jolt.decoder import jolt_to_json
            decoder = jolt_to_json
        
        def jolt_required(f):
            """Decorator to parse JOLT request body"""
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if request.content_type == "application/jolt":
                    try:
                        data = decoder(request.get_data(as_text=True))
                        request.json = data
                    except Exception as e:
                        raise BadRequest(f"Invalid JOLT format: {e}")
                return f(*args, **kwargs)
            return decorated_function
        
        def joltify(data: Any) -> Response:
            """Convert data to JOLT response"""
            jolt_data = encoder(data)
            return Response(jolt_data, mimetype="application/jolt")
        
        # Add to Flask app context
        app.jolt_required = jolt_required
        app.joltify = joltify
        
        logger.info("JOLT support enabled for Flask")
    
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False


# ============= LangChain Integration =============
try:
    from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
    from langchain.schema.output_parser import BaseOutputParser
    from langchain.prompts import PromptTemplate
    from langchain.callbacks.base import BaseCallbackHandler
    
    class JoltOutputParser(BaseOutputParser):
        """Parse JOLT formatted LLM output"""
        
        def __init__(self, decoder: Optional[Callable] = None):
            if not decoder:
                from jolt.decoder import jolt_to_json
                decoder = jolt_to_json
            self.decoder = decoder
        
        def parse(self, text: str) -> Any:
            """Parse JOLT text to Python object"""
            # Extract JOLT block if wrapped in markdown
            if "```jolt" in text:
                start = text.find("```jolt") + 7
                end = text.find("```", start)
                text = text[start:end].strip()
            elif "```" in text:
                start = text.find("```") + 3
                end = text.find("```", start)
                text = text[start:end].strip()
            
            return self.decoder(text)
        
        def get_format_instructions(self) -> str:
            return (
                "Your response should be formatted in JOLT "
                "(JSON-Optimized Lightweight Tokens) format. "
                "Use minimal syntax without quotes for keys, "
                "explicit array lengths like [3], and table format "
                "for uniform objects."
            )
    
    class JoltPromptTemplate(PromptTemplate):
        """Prompt template with JOLT examples"""
        
        def __init__(self, 
                    encoder: Optional[Callable] = None,
                    **kwargs):
            super().__init__(**kwargs)
            if not encoder:
                from jolt.encoder import json_to_jolt
                encoder = json_to_jolt
            self.encoder = encoder
        
        def format_jolt_example(self, data: Any) -> str:
            """Format data as JOLT example in prompt"""
            return self.encoder(data)
    
    class JoltCallbackHandler(BaseCallbackHandler):
        """Track token usage with JOLT optimization"""
        
        def __init__(self):
            self.token_usage = {
                "json_tokens": 0,
                "jolt_tokens": 0,
                "saved_tokens": 0
            }
        
        def on_llm_start(self, serialized: Dict[str, Any], 
                        prompts: List[str], **kwargs) -> None:
            """Track tokens in prompts"""
            for prompt in prompts:
                # Estimate tokens (simplified)
                if "```jolt" in prompt:
                    self.token_usage["jolt_tokens"] += len(prompt) // 4
                elif "```json" in prompt:
                    self.token_usage["json_tokens"] += len(prompt) // 4
        
        def get_summary(self) -> Dict[str, Any]:
            """Get token usage summary"""
            self.token_usage["saved_tokens"] = (
                self.token_usage["json_tokens"] - 
                self.token_usage["jolt_tokens"]
            )
            return self.token_usage
    
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False


# ============= Pandas Integration =============
try:
    import pandas as pd
    import numpy as np
    
    def dataframe_to_jolt(df: pd.DataFrame, 
                         table_name: str = "data",
                         encoder: Optional[Callable] = None) -> str:
        """
        Convert pandas DataFrame to JOLT format
        
        Args:
            df: DataFrame to convert
            table_name: Name for the table in JOLT
            encoder: Custom JOLT encoder
            
        Returns:
            JOLT formatted string
        """
        if not encoder:
            from jolt.encoder import json_to_jolt
            encoder = json_to_jolt
        
        # Convert DataFrame to dict format optimized for JOLT tables
        records = df.to_dict('records')
        data = {table_name: records}
        
        return encoder(data, root_name="dataframe")
    
    def jolt_to_dataframe(jolt_str: str,
                         decoder: Optional[Callable] = None) -> pd.DataFrame:
        """
        Convert JOLT format to pandas DataFrame
        
        Args:
            jolt_str: JOLT formatted string
            decoder: Custom JOLT decoder
            
        Returns:
            pandas DataFrame
        """
        if not decoder:
            from jolt.decoder import jolt_to_json
            decoder = jolt_to_json
        
        data = decoder(jolt_str)
        
        # Find the first array/table in the data
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list) and value and isinstance(value[0], dict):
                    return pd.DataFrame(value)
        elif isinstance(data, list):
            return pd.DataFrame(data)
        
        # Fallback: normalize nested structure
        return pd.json_normalize(data)
    
    # Extend pandas DataFrame with JOLT methods
    pd.DataFrame.to_jolt = lambda self, **kwargs: dataframe_to_jolt(self, **kwargs)
    
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


# ============= SQLAlchemy Integration =============
try:
    from sqlalchemy import TypeDecorator, Text
    from sqlalchemy.ext.mutable import MutableDict
    
    class JoltType(TypeDecorator):
        """SQLAlchemy type for storing JOLT data"""
        
        impl = Text
        cache_ok = True
        
        def __init__(self, 
                    encoder: Optional[Callable] = None,
                    decoder: Optional[Callable] = None):
            super().__init__()
            
            if not encoder:
                from jolt.encoder import json_to_jolt
                encoder = json_to_jolt
            if not decoder:
                from jolt.decoder import jolt_to_json
                decoder = jolt_to_json
            
            self.encoder = encoder
            self.decoder = decoder
        
        def process_bind_param(self, value, dialect):
            """Convert Python object to JOLT for database storage"""
            if value is not None:
                return self.encoder(value)
            return value
        
        def process_result_value(self, value, dialect):
            """Convert JOLT from database to Python object"""
            if value is not None:
                return self.decoder(value)
            return value
    
    # Make it mutable for ORM tracking
    MutableDict.associate_with(JoltType)
    
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False


# ============= Redis Integration =============
try:
    import redis
    
    class JoltRedis(redis.Redis):
        """Redis client with JOLT support"""
        
        def __init__(self, 
                    encoder: Optional[Callable] = None,
                    decoder: Optional[Callable] = None,
                    *args, **kwargs):
            super().__init__(*args, **kwargs)
            
            if not encoder:
                from jolt.encoder import json_to_jolt
                encoder = json_to_jolt
            if not decoder:
                from jolt.decoder import jolt_to_json
                decoder = jolt_to_json
            
            self.jolt_encoder = encoder
            self.jolt_decoder = decoder
        
        def jolt_set(self, name: str, value: Any, **kwargs) -> bool:
            """Set value as JOLT in Redis"""
            jolt_data = self.jolt_encoder(value)
            return self.set(name, jolt_data, **kwargs)
        
        def jolt_get(self, name: str) -> Any:
            """Get and decode JOLT value from Redis"""
            value = self.get(name)
            if value:
                return self.jolt_decoder(value.decode())
            return None
        
        def jolt_mset(self, mapping: Dict[str, Any], **kwargs) -> bool:
            """Set multiple values as JOLT"""
            jolt_mapping = {
                key: self.jolt_encoder(value)
                for key, value in mapping.items()
            }
            return self.mset(jolt_mapping, **kwargs)
        
        def jolt_mget(self, keys: List[str]) -> List[Any]:
            """Get multiple JOLT values"""
            values = self.mget(keys)
            return [
                self.jolt_decoder(v.decode()) if v else None
                for v in values
            ]
    
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


# ============= Integration Status =============
def get_available_integrations() -> Dict[str, bool]:
    """Get status of available integrations"""
    return {
        "fastapi": HAS_FASTAPI,
        "flask": HAS_FLASK,
        "langchain": HAS_LANGCHAIN,
        "pandas": HAS_PANDAS,
        "sqlalchemy": HAS_SQLALCHEMY,
        "redis": HAS_REDIS
    }


def print_integration_status():
    """Print status of all integrations"""
    integrations = get_available_integrations()
    print("JOLT Framework Integration Status:")
    print("-" * 40)
    for name, available in integrations.items():
        status = "✓ Available" if available else "✗ Not installed"
        print(f"{name.capitalize():<15} {status}")
    print("-" * 40)
    
    # Provide installation instructions
    missing = [name for name, available in integrations.items() if not available]
    if missing:
        print("\nTo enable missing integrations, install:")
        if "fastapi" in missing:
            print("  pip install fastapi")
        if "flask" in missing:
            print("  pip install flask")
        if "langchain" in missing:
            print("  pip install langchain")
        if "pandas" in missing:
            print("  pip install pandas")
        if "sqlalchemy" in missing:
            print("  pip install sqlalchemy")
        if "redis" in missing:
            print("  pip install redis")
