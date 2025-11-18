# JOLT Examples

This directory contains example JOLT files demonstrating various features.

## Basic Examples

### 1. Simple Object (simple.jolt)
```jolt
user {
  id: 1
  name: Alice
  email: alice@example.com
  active: true
}
```

### 2. Nested Structure (nested.jolt)
```jolt
company {
  name: Acme Corp
  founded: 2020
  
  headquarters {
    address: 123 Main St
    city: San Francisco
    state: CA
    country: USA
  }
  
  ceo {
    name: John Doe
    email: john@acme.com
  }
}
```

### 3. Arrays (arrays.jolt)
```jolt
data {
  numbers[5]: 1,2,3,4,5
  names[3]: Alice,Bob,Charlie
  mixed[4]: 1, "two", 3.0, true
}
```

### 4. Table Format (table.jolt)
```jolt
employees[4] {
  id, name, department, salary:
  1, Alice Johnson, Engineering, 120000
  2, Bob Smith, Marketing, 95000
  3, Charlie Brown, Sales, 85000
  4, Diana Prince, HR, 78000
}
```

## Real-World Examples

### 5. API Response (api_response.jolt)
```jolt
response {
  status: 200
  timestamp: "2024-11-18T10:30:00Z"
  
  data {
    users[3] {
      id, username, email, verified:
      101, alice_wonder, alice@example.com, true
      102, bob_builder, bob@example.com, true
      103, charlie_chocolate, charlie@example.com, false
    }
  }
  
  pagination {
    page: 1
    per_page: 3
    total: 150
    has_more: true
  }
}
```

### 6. Configuration File (config.jolt)
```jolt
app_config {
  name: MyApp
  version: 2.1.0
  debug: false
  
  database {
    host: localhost
    port: 5432
    name: myapp_db
    pool_size: 10
    timeout: 30
  }
  
  cache {
    enabled: true
    ttl: 3600
    backend: redis
    
    redis {
      host: localhost
      port: 6379
      db: 0
    }
  }
  
  features[5]: auth,api,dashboard,analytics,notifications
  
  logging {
    level: info
    format: json
    outputs[2]: stdout,file
  }
}
```

### 7. LLM Prompt (llm_prompt.jolt)
```jolt
prompt {
  model: gpt-4
  temperature: 0.7
  max_tokens: 500
  
  system: "You are a helpful assistant that provides concise answers."
  
  messages[3] {
    role, content:
    user, "What is machine learning?"
    assistant, "Machine learning is a subset of AI..."
    user, "Can you explain supervised learning?"
  }
  
  examples[2] {
    input, output:
    "Classify: It's a beautiful day", positive
    "Classify: This is terrible", negative
  }
}
```

### 8. Supply Chain Data (supply_chain.jolt)
```jolt
scenario {
  id: 7
  name: Port Delay Simulation
  created: "2024-11-18T10:00:00Z"
  
  supplier {
    id: 92
    name: Hankyu Steel Corporation
    country: JP
    reliability: 0.95
    
    delays[3]: 7,12,3
    
    location {
      port: Kobe
      coordinates {
        lat: 34.6901
        lon: 135.1955
      }
    }
  }
  
  events[5] {
    timestamp, type, severity, impact_days:
    1021, delay, high, 7
    1033, delay, medium, 12
    1089, resolution, low, 0
    1120, delay, critical, 15
    1150, resolution, low, 0
  }
  
  metrics {
    total_delay_days: 34
    cost_impact: 250000
    affected_orders: 45
    recovery_time: 30
  }
  
  mitigation[3]: "Find alternative supplier","Increase buffer stock","Expedite shipping"
}
```

### 9. Test Data (test_data.jolt)
```jolt
test_suite {
  name: User Registration Tests
  version: 1.0
  
  test_cases[4] {
    id, name, expected_result:
    1, "Valid registration", pass
    2, "Duplicate email", fail
    3, "Invalid email format", fail
    4, "Missing required field", fail
  }
  
  environment {
    platform: linux
    python_version: 3.11
    database: postgresql
    test_db: test_myapp
  }
  
  fixtures {
    users[2] {
      email, password, verified:
      "test1@example.com", "password123", true
      "test2@example.com", "password456", false
    }
  }
}
```

### 10. Data Analytics (analytics.jolt)
```jolt
analytics_report {
  period: "2024-Q3"
  generated: "2024-10-01T09:00:00Z"
  
  metrics {
    total_revenue: 1250000.50
    total_orders: 3421
    average_order_value: 365.27
    customer_count: 892
    conversion_rate: 0.042
  }
  
  top_products[5] {
    id, name, units_sold, revenue:
    101, "Widget Pro", 543, 162900
    205, "Gadget Plus", 421, 126300
    337, "Tool Elite", 389, 116700
    412, "Device Max", 298, 89400
    509, "Kit Premium", 276, 82800
  }
  
  regions[4] {
    name, orders, revenue, growth:
    "North America", 1523, 556225.75, 0.15
    "Europe", 1102, 402730.50, 0.22
    "Asia Pacific", 621, 226984.00, 0.31
    "Other", 175, 64060.25, 0.08
  }
  
  trends {
    traffic_sources[3]: organic,direct,social
    peak_hours[3]: 10,14,20
    top_categories[4]: "Electronics","Home","Sports","Fashion"
  }
}
```

## Usage

### Python
```python
from jolt import jolt_to_json
from pathlib import Path

# Load and parse any example
jolt_text = Path("examples/simple.jolt").read_text()
data = jolt_to_json(jolt_text)
print(data)
```

### CLI
```bash
# Convert to JSON
jolt convert examples/simple.jolt --pretty

# Convert back to JOLT
jolt convert examples/api_response.json -o output.jolt

# With optimization
jolt convert examples/config.json --optimize -o config.jolt
```

## Tips

1. **Use tables** for uniform object arrays - saves tons of tokens!
2. **Omit quotes** when possible - keys and simple values don't need them
3. **Named blocks** make structure clear and save braces
4. **Explicit array lengths** help parsers and save brackets
5. **Nest naturally** - JOLT handles deep nesting efficiently

Happy JOLT-ing! 🚀
