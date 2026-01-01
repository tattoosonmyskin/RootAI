#!/usr/bin/env python3
"""
RootAI CLI - Command Line Interface for RootAI v3.0

Usage:
    rootai reason "What is justice in Islamic philosophy?"
    rootai benchmark --questions 100
    rootai index --build --roots 10000
    rootai server --port 8080
"""

import sys
import argparse
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.root_reasoner import RootReasoner
from core.graph_sharding import GraphSharding, create_sample_index


def cmd_reason(args):
    """Execute reasoning query."""
    print("Initializing RootAI v3.0...")
    
    # Initialize reasoner
    reasoner = RootReasoner(
        model_name=args.model,
        use_gpu=args.gpu
    )
    
    # Load or create index
    if args.index and Path(args.index).exists():
        reasoner.load_graph_index(args.index)
    else:
        sharder = create_sample_index(n_roots=1000, dimension=768)
        reasoner.set_graph_sharder(sharder)
    
    # Run reasoning
    print(f"\nQuery: {args.query}")
    print("\nProcessing...\n")
    
    result = reasoner.reason(
        query=args.query,
        k=args.k,
        max_new_tokens=args.max_tokens
    )
    
    # Display results
    print("=" * 60)
    print("ANSWER:")
    print("=" * 60)
    print(result['answer'])
    print()
    
    if args.verbose and result.get('roots'):
        print("\nROOT ANALYSIS:")
        print("-" * 60)
        for i, root in enumerate(result['roots'], 1):
            print(f"{i}. {root['word']} → {root['root']} ({root.get('pos', 'UNKNOWN')})")
        print()
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Results saved to {args.output}")


def cmd_benchmark(args):
    """Run benchmark evaluation."""
    from benchmarks.semantic_mmlu import SemanticMMLU
    
    print("Initializing benchmark...")
    
    reasoner = RootReasoner(
        model_name=args.model,
        use_gpu=args.gpu
    )
    
    if not args.no_index:
        sharder = create_sample_index(n_roots=1000, dimension=768)
        reasoner.set_graph_sharder(sharder)
    
    benchmark = SemanticMMLU(reasoner)
    result = benchmark.run_benchmark(max_questions=args.questions)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump({
                'accuracy': result.accuracy,
                'total': result.total_questions,
                'correct': result.correct,
                'by_category': result.by_category
            }, f, indent=2)
        print(f"\nResults saved to {args.output}")


def cmd_index(args):
    """Build or manage graph index."""
    if args.build:
        print(f"Building graph index with {args.roots} roots...")
        sharder = create_sample_index(
            n_roots=args.roots,
            dimension=args.dimension
        )
        
        if args.output:
            sharder.save_index(args.output)
            print(f"Index saved to {args.output}")
    
    elif args.info and args.input:
        print(f"Loading index from {args.input}...")
        sharder = GraphSharding(dimension=args.dimension)
        sharder.load_index(args.input)
        
        print(f"\nIndex Information:")
        print(f"  Total roots: {sharder.index.ntotal}")
        print(f"  Dimension: {sharder.dimension}")
        print(f"  Index type: {sharder.index_type}")


def cmd_server(args):
    """Start API server."""
    import uvicorn
    
    print(f"Starting RootAI API server on port {args.port}...")
    
    uvicorn.run(
        "api.fastapi_app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="RootAI v3.0 - Root-based semantic reasoning CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Reason command
    reason_parser = subparsers.add_parser('reason', help='Execute reasoning query')
    reason_parser.add_argument('query', help='Query to reason about')
    reason_parser.add_argument('--model', default='google/t5-v1_1-base', help='T5 model name')
    reason_parser.add_argument('--index', help='Path to graph index')
    reason_parser.add_argument('--k', type=int, default=5, help='Number of roots to retrieve')
    reason_parser.add_argument('--max-tokens', type=int, default=200, help='Max tokens to generate')
    reason_parser.add_argument('--gpu', action='store_true', help='Use GPU acceleration')
    reason_parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    reason_parser.add_argument('--output', help='Output file for results (JSON)')
    
    # Benchmark command
    bench_parser = subparsers.add_parser('benchmark', help='Run benchmark evaluation')
    bench_parser.add_argument('--questions', type=int, default=100, help='Number of questions')
    bench_parser.add_argument('--model', default='google/t5-v1_1-base', help='T5 model name')
    bench_parser.add_argument('--gpu', action='store_true', help='Use GPU acceleration')
    bench_parser.add_argument('--no-index', action='store_true', help='Skip graph indexing')
    bench_parser.add_argument('--output', help='Output file for results (JSON)')
    
    # Index command
    index_parser = subparsers.add_parser('index', help='Build or manage graph index')
    index_parser.add_argument('--build', action='store_true', help='Build new index')
    index_parser.add_argument('--info', action='store_true', help='Show index information')
    index_parser.add_argument('--input', help='Input index file')
    index_parser.add_argument('--output', help='Output index file')
    index_parser.add_argument('--roots', type=int, default=10000, help='Number of roots')
    index_parser.add_argument('--dimension', type=int, default=768, help='Embedding dimension')
    
    # Server command
    server_parser = subparsers.add_parser('server', help='Start API server')
    server_parser.add_argument('--host', default='0.0.0.0', help='Host address')
    server_parser.add_argument('--port', type=int, default=8080, help='Port number')
    server_parser.add_argument('--reload', action='store_true', help='Auto-reload on changes')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    if args.command == 'reason':
        cmd_reason(args)
    elif args.command == 'benchmark':
        cmd_benchmark(args)
    elif args.command == 'index':
        cmd_index(args)
    elif args.command == 'server':
        cmd_server(args)


if __name__ == '__main__':
    main()
