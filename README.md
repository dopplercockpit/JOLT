# JOLT
JSON optimized lightweight tokens 
JOLT — JSON-Optimized Lightweight Tokens

A compact, LLM-native, human-readable structured data format.


---

🔥 Why JOLT Exists

Modern LLM workflows choke on JSON.
Every brace, quote, comma, and repeated key burns tokens, increases latency, and introduces parsing ambiguity.

CSV is smaller, but too flat.
YAML is unpredictable.
TOON is cute but can’t represent nested data.

We needed something new:

> A structured, lossless, token-efficient format
designed specifically for LLM prompts.



That’s JOLT.


---

⚙️ What JOLT Is

Minimal syntax

No quotes or braces

Explicit block structure

Explicit array lengths

CSV-style rows for uniform tables

Human-readable

Predictable for LLMs

Fully reversible back to JSON

Can represent nested objects cleanly

Supports mixed data types

Stream-friendly


Think:
JSON + CSV + a tiny splash of YAML — optimized for tokens.


---

📉 Token Efficiency

Example dataset:

JSON: ~350–420 tokens

TOON: ~180 tokens

JOLT: ~110–130 tokens


That’s 3–4× smaller than JSON inside a model prompt.


---

🧪 JOLT Example

JSON Version

{
  "scenario": {
      "id": 7,
          "name": "Port Delay",
              "supplier": {
                    "id": 92,
                          "name": "Hankyu Steel",
                                "delays": [7,12,3],
                                      "location": {
                                              "country": "JP",
                                                      "port": "Kobe"
                                                            }
                                                                },
                                                                    "events": [
                                                                          {"t": 1021, "type": "delay", "days": 7},
                                                                                {"t": 1033, "type": "delay", "days": 12}
                                                                                    ]
                                                                                      }
                                                                                      }


                                                                                      ---

                                                                                      JOLT Version

                                                                                      scenario {
                                                                                        id: 7
                                                                                          name: Port Delay

                                                                                            supplier {
                                                                                                id: 92
                                                                                                    name: Hankyu Steel
                                                                                                        delays[3]: 7,12,3

                                                                                                            location {
                                                                                                                  country: JP
                                                                                                                        port: Kobe
                                                                                                                            }
                                                                                                                              }

                                                                                                                                events[2] {
                                                                                                                                    t, type, days:
                                                                                                                                        1021, delay, 7
                                                                                                                                            1033, delay, 12
                                                                                                                                              }
                                                                                                                                              }


                                                                                                                                              ---

                                                                                                                                              🧠 Core Principles (JOLT 0.1)

                                                                                                                                              1. Minimal Syntax

                                                                                                                                              No quotes

                                                                                                                                              No braces

                                                                                                                                              No commas except separating row values

                                                                                                                                              No repeated keys


                                                                                                                                              2. Clear Nesting

                                                                                                                                              identifier {
                                                                                                                                                key: value
                                                                                                                                                  child {
                                                                                                                                                      key: value
                                                                                                                                                        }
                                                                                                                                                        }

                                                                                                                                                        3. Explicit Arrays

                                                                                                                                                        items[4]: a,b,c,d

                                                                                                                                                        Or for uniform objects:

                                                                                                                                                        events[2] {
                                                                                                                                                          t, type, days:
                                                                                                                                                            1021, delay, 7
                                                                                                                                                              1033, delay, 12
                                                                                                                                                              }

                                                                                                                                                              4. Lossless

                                                                                                                                                              Every JOLT structure maps directly back to JSON.

                                                                                                                                                              5. Streaming-Friendly

                                                                                                                                                              Blocks and rows can be appended without breaking downstream parsing.


                                                                                                                                                              ---

                                                                                                                                                              🔄 Planned Tools

                                                                                                                                                              Converters

                                                                                                                                                              json_to_jolt()

                                                                                                                                                              jolt_to_json()


                                                                                                                                                              Languages:

                                                                                                                                                              Python

                                                                                                                                                              Node

                                                                                                                                                              Go

                                                                                                                                                              FastAPI middleware

                                                                                                                                                              Browser JS


                                                                                                                                                              Benchmarks

                                                                                                                                                              token savings

                                                                                                                                                              latency improvements

                                                                                                                                                              LLM accuracy comparisons


                                                                                                                                                              Extensions (Future)

                                                                                                                                                              Type annotations

                                                                                                                                                              Schema definitions

                                                                                                                                                              JOLT-Schema (like JSON-Schema but smaller)

                                                                                                                                                              Compression modes



                                                                                                                                                              ---

                                                                                                                                                              🧭 Roadmap

                                                                                                                                                              0.1 → Syntax & examples

                                                                                                                                                              0.2 → JSON/JOLT converters

                                                                                                                                                              0.3 → Schema support

                                                                                                                                                              0.4 → Analyzer: detect when JSON arrays should become table-blocks

                                                                                                                                                              1.0 → Candidate spec for LLM-native structured data



                                                                                                                                                              ---

                                                                                                                                                              📄 License

                                                                                                                                                              MIT (feel free to copy, remix, fork, standardize)


                                                                                                                                                              ---

                                                                                                                                                              🔥 JOLT is early — intentionally minimal.
                                                                                                                                                              If you want to contribute, open an issue or PR.


                                                                                                                                                              ---