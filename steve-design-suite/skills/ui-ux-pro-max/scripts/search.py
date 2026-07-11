#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steve Design Search - CLI for UI/UX design intelligence
Usage: python search.py "<query>" [--domain <domain>] [--stack <stack>] [--max-results 3]

Domains: style, color, chart, landing, product, ux, typography
Stacks: html-tailwind, react, nextjs, vue, svelte, swiftui, react-native, flutter, shadcn
"""

import argparse
import sys
from core import CSV_CONFIG, AVAILABLE_STACKS, MAX_RESULTS, search, search_stack


def configure_utf8_output():
    """Keep Unicode output reliable on Windows and redirected terminals."""
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure:
        reconfigure(encoding="utf-8", errors="replace")


def format_output(result):
    """Format results for Steve's consumption"""
    if "error" in result:
        return f"Error: {result['error']}"

    output = []
    if result.get("stack"):
        output.append(f"## Stack Guidelines: {result['stack']}")
    else:
        output.append(f"## Design Reference: {result['domain']}")

    output.append(f"**Query:** {result['query']} | **Found:** {result['count']} results\n")

    for i, row in enumerate(result['results'], 1):
        output.append(f"### Result {i}")
        for key, value in row.items():
            value_str = str(value)
            if len(value_str) > 300:
                value_str = value_str[:300] + "..."
            output.append(f"- **{key}:** {value_str}")
        output.append("")

    return "\n".join(output)


if __name__ == "__main__":
    configure_utf8_output()
    parser = argparse.ArgumentParser(description="Steve Design Search")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--domain", "-d", choices=list(CSV_CONFIG.keys()), help="Search domain")
    parser.add_argument("--stack", "-s", choices=AVAILABLE_STACKS, help="Stack-specific search")
    parser.add_argument("--max-results", "-n", type=int, default=MAX_RESULTS, help="Max results (default: 3)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.stack:
        result = search_stack(args.query, args.stack, args.max_results)
    else:
        result = search(args.query, args.domain, args.max_results)

    if args.json:
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(format_output(result))
