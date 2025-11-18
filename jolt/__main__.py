#!/usr/bin/env python3
"""
JOLT CLI - Simple command-line interface
For quick conversions and testing
"""
import argparse
import json
import sys
from pathlib import Path

from jolt import json_to_jolt, jolt_to_json, JoltSyntaxError, JoltOptimizer, __version__


def main(argv=None):
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="jolt",
        description="JOLT - JSON-Optimized Lightweight Tokens CLI",
        epilog="For more information, visit: https://github.com/dopplercockpit/JOLT"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"JOLT v{__version__}"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert between JSON and JOLT')
    convert_parser.add_argument('input', help='Input file (- for stdin)')
    convert_parser.add_argument('-o', '--output', default='-', help='Output file (- for stdout)')
    convert_parser.add_argument('-f', '--format', choices=['json', 'jolt', 'auto'], 
                               default='auto', help='Input format (default: auto-detect)')
    convert_parser.add_argument('--root', help='Root block name for JOLT output')
    convert_parser.add_argument('--optimize', action='store_true', help='Apply optimizations')
    convert_parser.add_argument('--pretty', action='store_true', help='Pretty print JSON output')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run quick sanity test')
    
    args = parser.parse_args(argv)
    
    if not args.command:
        parser.print_help()
        return 0
    
    if args.command == 'test':
        return run_test()
    elif args.command == 'convert':
        return run_convert(args)
    
    return 0


def run_test():
    """Run quick sanity test"""
    from jolt import quick_test
    print(f"JOLT v{__version__} - Quick Test")
    print("=" * 50)
    success = quick_test()
    print("=" * 50)
    if success:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


def run_convert(args):
    """Run convert command"""
    # Load input
    if args.input == '-':
        content = sys.stdin.read()
    else:
        try:
            content = Path(args.input).read_text(encoding='utf-8')
        except FileNotFoundError:
            print(f"Error: File not found: {args.input}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return 1
    
    # Auto-detect format
    if args.format == 'auto':
        content_stripped = content.strip()
        if content_stripped.startswith('{') or content_stripped.startswith('['):
            args.format = 'json'
        else:
            args.format = 'jolt'
    
    try:
        if args.format == 'json':
            # JSON to JOLT
            data = json.loads(content)
            
            # Apply optimization if requested
            if args.optimize:
                optimizer = JoltOptimizer(enable_abbreviations=True)
                data, stats = optimizer.optimize(data)
                print(f"# Optimization: {stats.tokens_saved} tokens saved", file=sys.stderr)
            
            output = json_to_jolt(data, root_name=args.root)
        else:
            # JOLT to JSON
            data = jolt_to_json(content)
            
            if args.pretty:
                output = json.dumps(data, indent=2)
            else:
                output = json.dumps(data, separators=(',', ':'))
        
        # Write output
        if args.output == '-':
            print(output)
        else:
            Path(args.output).write_text(output, encoding='utf-8')
            print(f"✓ Converted {args.format.upper()} → {'JOLT' if args.format == 'json' else 'JSON'}", 
                  file=sys.stderr)
            print(f"  Output: {args.output}", file=sys.stderr)
        
        return 0
        
    except json.JSONDecodeError as e:
        print(f"JSON Error: {e}", file=sys.stderr)
        return 1
    except JoltSyntaxError as e:
        print(f"{e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
