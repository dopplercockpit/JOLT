#!/usr/bin/env python3
"""
JOLT CLI - Advanced command-line interface
Your terminal's best friend for working with JOLT data
"""
import argparse
import json
import sys
import os
from pathlib import Path
from typing import Any, Optional
import time

from jolt.encoder import json_to_jolt
from jolt.decoder import jolt_to_json
from jolt.schema import JoltSchema, create_schema_from_sample
from jolt.optimizer import JoltOptimizer, OptimizationStats
from jolt.streaming import JoltStreamParser, stream_jolt_to_json
from jolt.benchmark import JoltBenchmark, TokenCounter


def load_file(path: str) -> str:
    """Load file content"""
    if path == '-':
        return sys.stdin.read()
    return Path(path).read_text(encoding='utf-8')


def save_file(path: str, content: str) -> None:
    """Save content to file"""
    if path == '-':
        sys.stdout.write(content)
        if not content.endswith('\n'):
            sys.stdout.write('\n')
    else:
        Path(path).write_text(content, encoding='utf-8')


def cmd_convert(args):
    """Convert between JSON and JOLT formats"""
    content = load_file(args.input)
    
    if args.format == 'auto':
        # Auto-detect format
        if content.strip().startswith('{') or content.strip().startswith('['):
            args.format = 'json'
        else:
            args.format = 'jolt'
    
    try:
        if args.format == 'json':
            # JSON to JOLT
            data = json.loads(content)
            
            # Apply optimization if requested
            if args.optimize:
                optimizer = JoltOptimizer(
                    enable_abbreviations=not args.no_abbreviations,
                    enable_pattern_detection=True,
                    enable_value_pooling=True
                )
                data, stats = optimizer.optimize(data)
                if args.verbose:
                    print(f"# Optimization: {stats}", file=sys.stderr)
            
            output = json_to_jolt(data, root_name=args.root)
            
        else:
            # JOLT to JSON
            data = jolt_to_json(content, wrap_root=args.wrap_root)
            
            if args.pretty:
                output = json.dumps(data, indent=2)
            else:
                output = json.dumps(data, separators=(',', ':'))
        
        save_file(args.output, output)
        
        if args.verbose:
            print(f"# Converted {args.format} -> {'JOLT' if args.format == 'json' else 'JSON'}", file=sys.stderr)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_validate(args):
    """Validate JOLT data against schema"""
    # Load data
    data_content = load_file(args.input)
    
    try:
        # Parse JOLT data
        if args.input.endswith('.jolt') or not (
            data_content.strip().startswith('{') or 
            data_content.strip().startswith('[')
        ):
            data = jolt_to_json(data_content)
        else:
            data = json.loads(data_content)
        
        # Load or generate schema
        if args.schema:
            schema_content = load_file(args.schema)
            schema_data = json.loads(schema_content)
            schema = JoltSchema(schema_data, strict=not args.no_strict)
        else:
            # Generate schema from data
            schema = create_schema_from_sample(data)
            if args.save_schema:
                schema_json = json.dumps(schema.root.__dict__, indent=2, default=str)
                save_file(args.save_schema, schema_json)
                print(f"Schema saved to: {args.save_schema}", file=sys.stderr)
        
        # Validate
        errors = schema.validate(data)
        
        if errors:
            print(f"Validation failed with {len(errors)} error(s):", file=sys.stderr)
            for error in errors[:args.max_errors]:
                print(f"  - {error}", file=sys.stderr)
            if len(errors) > args.max_errors:
                print(f"  ... and {len(errors) - args.max_errors} more", file=sys.stderr)
            sys.exit(1)
        else:
            print("✓ Validation successful", file=sys.stderr)
            
            if args.verbose:
                # Print schema summary
                print("\nSchema Summary:", file=sys.stderr)
                print(schema.to_jolt_schema_format(), file=sys.stderr)
                
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_optimize(args):
    """Optimize JSON/JOLT data"""
    content = load_file(args.input)
    
    try:
        # Parse input
        if content.strip().startswith('{') or content.strip().startswith('['):
            data = json.loads(content)
        else:
            data = jolt_to_json(content)
        
        # Create optimizer with custom settings
        custom_abbrevs = {}
        if args.abbreviations:
            for abbr in args.abbreviations:
                if '=' in abbr:
                    key, value = abbr.split('=', 1)
                    custom_abbrevs[key] = value
        
        optimizer = JoltOptimizer(
            enable_abbreviations=not args.no_abbreviations,
            enable_type_inference=not args.no_type_inference,
            enable_pattern_detection=not args.no_patterns,
            enable_value_pooling=not args.no_pooling,
            enable_sparse_arrays=not args.no_sparse,
            custom_abbreviations=custom_abbrevs
        )
        
        # Optimize
        optimized_data, stats = optimizer.optimize(data, context=args.context)
        
        # Output
        if args.format == 'jolt':
            output = json_to_jolt(optimized_data, root_name=args.root)
        else:
            output = json.dumps(optimized_data, 
                              indent=2 if args.pretty else None,
                              separators=(',', ':') if not args.pretty else None)
        
        save_file(args.output, output)
        
        # Print statistics
        if not args.quiet:
            print(f"\n{stats}", file=sys.stderr)
            
            if args.verbose:
                print("\nOptimizations applied:", file=sys.stderr)
                for technique, count in stats.optimizations_applied.items():
                    print(f"  - {technique}: {count}", file=sys.stderr)
                    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_benchmark(args):
    """Benchmark JOLT performance"""
    try:
        # Create benchmark suite
        bench = JoltBenchmark(
            jolt_encoder=lambda x: json_to_jolt(x),
            jolt_decoder=lambda x: jolt_to_json(x),
            token_model=args.model
        )
        
        if args.input:
            # Benchmark specific file
            content = load_file(args.input)
            if content.strip().startswith('{') or content.strip().startswith('['):
                data = json.loads(content)
            else:
                data = jolt_to_json(content)
            
            result = bench.benchmark_single(
                data, 
                test_name=Path(args.input).stem if args.input != '-' else 'stdin',
                iterations=args.iterations
            )
            
            print(f"\nBenchmark Results for {result.name}:")
            print(f"  Size: {result.size_bytes} bytes ({result.compression_ratio:.1%} of JSON)")
            print(f"  Tokens: {result.token_count} ({result.token_reduction:.1%} reduction)")
            print(f"  Encode: {result.encode_time_ms:.2f}ms")
            print(f"  Decode: {result.decode_time_ms:.2f}ms")
            print(f"  Correct: {'✓' if result.correctness else '✗'}")
            
            if args.verbose:
                profile = bench.profile_token_distribution(data)
                print("\nToken Distribution Analysis:")
                print(f"  JSON structural overhead: {profile['json']['structural_ratio']:.1%}")
                print(f"  JOLT structural overhead: {profile['jolt']['structural_ratio']:.1%}")
                print(f"  Structural reduction: {profile['improvement']['structural_reduction']:.1%}")
                
        else:
            # Run standard benchmark suite
            suite = bench.benchmark_suite(args.suite, iterations=args.iterations)
            
            if args.format == 'markdown':
                print(suite.to_markdown())
            else:
                print(f"\nBenchmark Suite: {args.suite}")
                print(f"Timestamp: {suite.timestamp}")
                print(f"\nSummary:")
                for key, value in suite.summary.items():
                    if isinstance(value, float):
                        if 'reduction' in key:
                            print(f"  {key}: {value:.1%}")
                        else:
                            print(f"  {key}: {value:.2f}")
                    else:
                        print(f"  {key}: {value}")
                
                if args.verbose:
                    print(f"\nDetailed Results:")
                    for result in suite.results:
                        print(f"\n  {result.name}:")
                        print(f"    Tokens: {result.token_count} ({result.token_reduction:.1%} saved)")
                        print(f"    Size: {result.size_bytes}B ({result.compression_ratio:.1%})")
                        print(f"    Speed: {result.encode_time_ms:.2f}ms / {result.decode_time_ms:.2f}ms")
                        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_stream(args):
    """Stream process JOLT data"""
    try:
        # Open input stream
        if args.input == '-':
            stream = sys.stdin
        else:
            stream = open(args.input, 'r', encoding='utf-8')
        
        # Create parser
        parser = JoltStreamParser(stream, buffer_size=args.buffer_size)
        
        if args.mode == 'events':
            # Output stream events
            for event in parser.parse_stream():
                if args.verbose or event.type.value in ['KEY', 'VALUE']:
                    path_str = '.'.join(event.path) if event.path else 'root'
                    print(f"{event.type.value:<15} {path_str:<30} {event.data}")
                    
        elif args.mode == 'filter':
            # Filter based on path
            if not args.filter:
                print("Error: --filter required for filter mode", file=sys.stderr)
                sys.exit(1)
            
            def path_matches(path):
                path_str = '.'.join(path)
                return any(f in path_str for f in args.filter)
            
            from jolt.streaming import filter_jolt_stream, JoltStreamBuilder
            builder = JoltStreamBuilder()
            
            for event in filter_jolt_stream(stream, path_matches):
                result = builder.process_event(event)
                if result:
                    output = json.dumps(result, indent=2 if args.pretty else None)
                    print(output)
                    
        else:  # json mode
            # Convert to JSON
            result = stream_jolt_to_json(stream)
            output = json.dumps(result, indent=2 if args.pretty else None)
            print(output)
        
        if args.input != '-':
            stream.close()
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    """Show statistics about JOLT data"""
    content = load_file(args.input)
    
    try:
        # Parse input
        if content.strip().startswith('{') or content.strip().startswith('['):
            data = json.loads(content)
            input_format = "JSON"
        else:
            data = jolt_to_json(content)
            input_format = "JOLT"
        
        # Calculate statistics
        counter = TokenCounter(model=args.model)
        
        json_str = json.dumps(data, separators=(',', ':'))
        json_pretty = json.dumps(data, indent=2)
        jolt_str = json_to_jolt(data)
        
        # Optimize version
        optimizer = JoltOptimizer()
        optimized_data, opt_stats = optimizer.optimize(data)
        jolt_optimized = json_to_jolt(optimized_data)
        
        print(f"\nStatistics for {args.input}:")
        print(f"Input format: {input_format}")
        print(f"\nSize comparison:")
        print(f"  JSON (compact):    {len(json_str):,} bytes")
        print(f"  JSON (pretty):     {len(json_pretty):,} bytes")
        print(f"  JOLT:              {len(jolt_str):,} bytes ({len(jolt_str)/len(json_str):.1%})")
        print(f"  JOLT (optimized):  {len(jolt_optimized):,} bytes ({len(jolt_optimized)/len(json_str):.1%})")
        
        print(f"\nToken comparison (model: {args.model}):")
        print(f"  JSON (compact):    {counter.count_tokens(json_str):,} tokens")
        print(f"  JSON (pretty):     {counter.count_tokens(json_pretty):,} tokens")
        print(f"  JOLT:              {counter.count_tokens(jolt_str):,} tokens")
        print(f"  JOLT (optimized):  {counter.count_tokens(jolt_optimized):,} tokens")
        
        print(f"\nSavings:")
        json_tokens = counter.count_tokens(json_str)
        jolt_tokens = counter.count_tokens(jolt_str)
        jolt_opt_tokens = counter.count_tokens(jolt_optimized)
        
        print(f"  JOLT vs JSON:      {json_tokens - jolt_tokens:,} tokens ({(1 - jolt_tokens/json_tokens):.1%})")
        print(f"  Optimized vs JSON: {json_tokens - jolt_opt_tokens:,} tokens ({(1 - jolt_opt_tokens/json_tokens):.1%})")
        
        if args.verbose:
            print(f"\nStructure analysis:")
            # Count different element types
            def count_elements(obj, counts=None):
                if counts is None:
                    counts = {'objects': 0, 'arrays': 0, 'strings': 0, 'numbers': 0, 'bools': 0, 'nulls': 0}
                
                if isinstance(obj, dict):
                    counts['objects'] += 1
                    for value in obj.values():
                        count_elements(value, counts)
                elif isinstance(obj, list):
                    counts['arrays'] += 1
                    for item in obj:
                        count_elements(item, counts)
                elif isinstance(obj, str):
                    counts['strings'] += 1
                elif isinstance(obj, (int, float)):
                    counts['numbers'] += 1
                elif isinstance(obj, bool):
                    counts['bools'] += 1
                elif obj is None:
                    counts['nulls'] += 1
                
                return counts
            
            counts = count_elements(data)
            for elem_type, count in counts.items():
                print(f"    {elem_type}: {count}")
                
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog='jolt',
        description='JOLT - JSON-Optimized Lightweight Tokens CLI'
    )
    
    # Global options
    parser.add_argument('--version', action='version', version='JOLT v0.2.0')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert between JSON and JOLT')
    convert_parser.add_argument('input', help='Input file (- for stdin)')
    convert_parser.add_argument('-o', '--output', default='-', help='Output file (- for stdout)')
    convert_parser.add_argument('-f', '--format', choices=['json', 'jolt', 'auto'], 
                               default='auto', help='Input format')
    convert_parser.add_argument('--root', help='Root block name for JOLT output')
    convert_parser.add_argument('--wrap-root', action='store_true', 
                               help='Wrap result in root object when converting to JSON')
    convert_parser.add_argument('--pretty', action='store_true', help='Pretty print JSON output')
    convert_parser.add_argument('--optimize', action='store_true', help='Apply optimizations')
    convert_parser.add_argument('--no-abbreviations', action='store_true', 
                               help='Disable key abbreviations')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate JOLT data against schema')
    validate_parser.add_argument('input', help='Data file to validate')
    validate_parser.add_argument('-s', '--schema', help='Schema file (JSON format)')
    validate_parser.add_argument('--save-schema', help='Save generated schema to file')
    validate_parser.add_argument('--no-strict', action='store_true', 
                                help='Allow additional properties')
    validate_parser.add_argument('--max-errors', type=int, default=10, 
                                help='Maximum errors to display')
    
    # Optimize command
    optimize_parser = subparsers.add_parser('optimize', help='Optimize JSON/JOLT data')
    optimize_parser.add_argument('input', help='Input file')
    optimize_parser.add_argument('-o', '--output', default='-', help='Output file')
    optimize_parser.add_argument('-f', '--format', choices=['json', 'jolt'], 
                                default='jolt', help='Output format')
    optimize_parser.add_argument('--root', help='Root name for JOLT output')
    optimize_parser.add_argument('--context', help='Context hint for optimization')
    optimize_parser.add_argument('--abbreviations', nargs='+', 
                                help='Custom abbreviations (key=abbr)')
    optimize_parser.add_argument('--pretty', action='store_true', help='Pretty print output')
    optimize_parser.add_argument('--no-abbreviations', action='store_true')
    optimize_parser.add_argument('--no-type-inference', action='store_true')
    optimize_parser.add_argument('--no-patterns', action='store_true')
    optimize_parser.add_argument('--no-pooling', action='store_true')
    optimize_parser.add_argument('--no-sparse', action='store_true')
    
    # Benchmark command
    benchmark_parser = subparsers.add_parser('benchmark', help='Benchmark JOLT performance')
    benchmark_parser.add_argument('-i', '--input', help='Input file to benchmark')
    benchmark_parser.add_argument('-s', '--suite', default='basic', 
                                 choices=['basic', 'complex', 'edge_cases'],
                                 help='Benchmark suite to run')
    benchmark_parser.add_argument('--iterations', type=int, default=10, 
                                 help='Number of iterations')
    benchmark_parser.add_argument('-f', '--format', choices=['text', 'markdown'], 
                                 default='text', help='Output format')
    benchmark_parser.add_argument('--model', default='gpt-4', 
                                 help='Model for token counting')
    
    # Stream command
    stream_parser = subparsers.add_parser('stream', help='Stream process JOLT data')
    stream_parser.add_argument('input', help='Input file (- for stdin)')
    stream_parser.add_argument('-m', '--mode', choices=['json', 'events', 'filter'],
                              default='json', help='Processing mode')
    stream_parser.add_argument('--filter', nargs='+', help='Path filters for filter mode')
    stream_parser.add_argument('--buffer-size', type=int, default=4096, 
                              help='Stream buffer size')
    stream_parser.add_argument('--pretty', action='store_true', help='Pretty print output')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show statistics about JOLT data')
    stats_parser.add_argument('input', help='Input file')
    stats_parser.add_argument('--model', default='gpt-4', help='Model for token counting')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    if args.command == 'convert':
        cmd_convert(args)
    elif args.command == 'validate':
        cmd_validate(args)
    elif args.command == 'optimize':
        cmd_optimize(args)
    elif args.command == 'benchmark':
        cmd_benchmark(args)
    elif args.command == 'stream':
        cmd_stream(args)
    elif args.command == 'stats':
        cmd_stats(args)


if __name__ == '__main__':
    main()
