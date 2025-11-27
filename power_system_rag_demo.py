"""
Power System RAG Demo
====================

This script demonstrates the complete RAG system for power system analysis.

Usage:
    python power_system_rag_demo.py --index    # Index the database
    python power_system_rag_demo.py --query "What is the voltage at bus 5?"

Author: Power System Analysis Team
Date: September 2025
"""

import asyncio
import argparse
import logging
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the RAG system
from power_system_rag_core import PowerSystemRAG

# Demo configuration
DEFAULT_DB_PATH = "data.db"
DEFAULT_STORAGE_DIR = "rag_demo_storage"

class PowerSystemRAGDemo:
    """Demo class for the RAG system"""
    
    def __init__(self, db_path: str = DEFAULT_DB_PATH, storage_dir: str = DEFAULT_STORAGE_DIR):
        """Initialize demo"""
        self.db_path = db_path
        self.storage_dir = storage_dir
        
        # Initialize RAG system
        self.rag_system = PowerSystemRAG(
            db_path=db_path,
            embedding_model="all-MiniLM-L6-v2",  # Fast local model
            vector_db_backend="auto",
            persist_directory=storage_dir
        )
        
        logger.info(f"RAG Demo initialized with database: {db_path}")
    
    async def index_database(self):
        """Index the database for RAG"""
        print("🔄 Starting database indexing...")
        print("This may take several minutes for large databases...")
        
        success = await self.rag_system.index_database()
        
        if success:
            print("✅ Database indexing complete!")
            
            # Show stats
            stats = self.rag_system.get_system_stats()
            print(f"📊 Indexed {stats.get('total_documents', 0)} document chunks")
            print(f"📊 Embedding dimension: {stats.get('embedding_dimension', 'unknown')}")
            print(f"📊 Vector backend: {stats.get('selected_backend', 'unknown')}")
        else:
            print("❌ Database indexing failed!")
            return False
        
        return True
    
    async def query_system(self, question: str, case_id: str = None):
        """Query the RAG system"""
        print(f"\n🔍 Processing question: {question}")
        
        if case_id:
            print(f"   📋 Case filter: {case_id}")
        
        try:
            response = await self.rag_system.query(
                question=question,
                case_id=case_id,
                max_results=5,
                include_sources=True
            )
            
            # Display results
            self._display_response(response)
            
            return response
            
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return None
    
    def _display_response(self, response: dict):
        """Display the RAG response in a formatted way"""
        print("\n" + "="*80)
        print("📝 RAG RESPONSE")
        print("="*80)
        
        # Main answer
        answer = response.get('answer', 'No answer provided')
        print(f"\n💡 Answer:")
        print(f"   {answer}")
        
        # Confidence
        confidence = response.get('confidence', 0.0)
        confidence_emoji = "🟢" if confidence > 0.7 else "🟡" if confidence > 0.4 else "🔴"
        print(f"\n{confidence_emoji} Confidence: {confidence:.2%}")
        
        # Validation notes
        validation_notes = response.get('validation_notes', [])
        if validation_notes:
            print(f"\n⚠️  Validation Notes:")
            for note in validation_notes:
                print(f"   - {note}")
        
        # Sources
        sources = response.get('sources', [])
        if sources:
            print(f"\n📚 Sources ({len(sources)}):")
            for i, source in enumerate(sources, 1):
                score = source.get('score', 0)
                preview = source.get('content_preview', '')[:100]
                metadata = source.get('metadata', {})
                
                print(f"\n   {i}. Score: {score:.3f}")
                print(f"      ID: {source.get('id', 'unknown')}")
                print(f"      Case: {metadata.get('case_id', 'unknown')}")
                print(f"      Source: {metadata.get('source_file', 'unknown')}")
                print(f"      Preview: {preview}...")
        
        # Metadata
        metadata = response.get('metadata', {})
        print(f"\n📈 Metadata:")
        print(f"   Sources used: {metadata.get('num_sources', 0)}")
        print(f"   Avg source score: {metadata.get('avg_source_score', 0):.3f}")
        
        print("\n" + "="*80)
    
    async def run_demo_queries(self):
        """Run a set of demo queries"""
        demo_queries = [
            "What buses have voltage violations?",
            "Show me the power flow on transmission lines",
            "What is the thermal loading of branch 1-2?",
            "Analyze the voltage profile in the system",
            "What are the DLR benefits compared to SLR?",
            "Show contingency analysis results",
            "What is the generation at bus 1?",
            "Are there any overloaded lines in the system?"
        ]
        
        print("\n🚀 Running demo queries...")
        
        for i, query in enumerate(demo_queries, 1):
            print(f"\n--- Demo Query {i}/{len(demo_queries)} ---")
            await self.query_system(query)
            
            # Small delay for readability
            await asyncio.sleep(1)
        
        print("\n✅ Demo queries complete!")
    
    def show_system_stats(self):
        """Show comprehensive system statistics"""
        print("\n" + "="*80)
        print("📊 SYSTEM STATISTICS")
        print("="*80)
        
        stats = self.rag_system.get_system_stats()
        
        print(f"\n🗄️  Database:")
        print(f"   Path: {stats.get('database_path', 'unknown')}")
        print(f"   Indexed: {'✅ Yes' if stats.get('is_indexed', False) else '❌ No'}")
        print(f"   Total documents: {stats.get('total_documents', 0)}")
        
        print(f"\n🔢 Embeddings:")
        embeddings_stats = stats.get('embeddings', {})
        print(f"   Cached embeddings: {embeddings_stats.get('total_cached', 0)}")
        print(f"   Cache size: {embeddings_stats.get('cache_size_mb', 0):.1f} MB")
        
        print(f"\n🔍 Retrieval:")
        retrieval_stats = stats.get('retrieval', {})
        print(f"   Has re-ranker: {'✅ Yes' if retrieval_stats.get('has_reranker', False) else '❌ No'}")
        print(f"   Initial k: {retrieval_stats.get('initial_k', 'unknown')}")
        print(f"   Final k: {retrieval_stats.get('final_k', 'unknown')}")
        
        print(f"\n💾 Vector Database:")
        print(f"   Backend: {stats.get('selected_backend', 'unknown')}")
        print(f"   Embedding dimension: {stats.get('embedding_dimension', 'unknown')}")
        
        if stats.get('indexing_date'):
            print(f"\n📅 Last indexed: {stats['indexing_date']}")
        
        print("\n" + "="*80)

async def main():
    """Main demo function"""
    parser = argparse.ArgumentParser(description="Power System RAG Demo")
    parser.add_argument('--index', action='store_true', help='Index the database')
    parser.add_argument('--query', type=str, help='Query the system')
    parser.add_argument('--case-id', type=str, help='Case ID filter for queries')
    parser.add_argument('--demo', action='store_true', help='Run demo queries')
    parser.add_argument('--stats', action='store_true', help='Show system statistics')
    parser.add_argument('--db-path', type=str, default=DEFAULT_DB_PATH, help='Database path')
    parser.add_argument('--storage-dir', type=str, default=DEFAULT_STORAGE_DIR, help='Storage directory')
    
    args = parser.parse_args()
    
    # Check if database exists
    if not Path(args.db_path).exists():
        print(f"❌ Database not found: {args.db_path}")
        print("Please ensure the database file exists.")
        return
    
    # Initialize demo
    print("🚀 Initializing Power System RAG Demo...")
    demo = PowerSystemRAGDemo(db_path=args.db_path, storage_dir=args.storage_dir)
    
    # Handle different actions
    if args.index:
        await demo.index_database()
    
    elif args.query:
        await demo.query_system(args.query, args.case_id)
    
    elif args.demo:
        await demo.run_demo_queries()
    
    elif args.stats:
        demo.show_system_stats()
    
    else:
        # Interactive mode
        print("\n🎯 Interactive Mode")
        print("Available commands:")
        print("  'index' - Index the database")
        print("  'stats' - Show system statistics") 
        print("  'demo' - Run demo queries")
        print("  'quit' - Exit")
        print("  Or just type your question!")
        
        while True:
            try:
                user_input = input("\n>>> ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                elif user_input.lower() == 'index':
                    await demo.index_database()
                elif user_input.lower() == 'stats':
                    demo.show_system_stats()
                elif user_input.lower() == 'demo':
                    await demo.run_demo_queries()
                elif user_input:
                    await demo.query_system(user_input, args.case_id)
                
            except KeyboardInterrupt:
                break
            except EOFError:
                print("\n👋 Exiting interactive mode...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    print("\n👋 Demo complete!")

if __name__ == "__main__":
    # Check for essential packages
    essential_packages = ['numpy', 'pandas']
    optional_packages = ['sentence_transformers', 'chromadb', 'transformers']
    
    missing_essential = []
    missing_optional = []
    
    for pkg in essential_packages:
        try:
            __import__(pkg)
        except ImportError:
            missing_essential.append(pkg)
    
    for pkg in optional_packages:
        try:
            __import__(pkg)
        except ImportError:
            missing_optional.append(pkg)
    
    if missing_essential:
        print(f"❌ Missing essential packages: {', '.join(missing_essential)}")
        print("Please install them with: pip install " + ' '.join(missing_essential))
        exit(1)
    
    if missing_optional:
        print(f"⚠️  Missing optional packages: {', '.join(missing_optional)}")
        print("For full functionality, install with: pip install -r requirements_rag_minimal.txt")
        print("The system will work with reduced functionality.\n")
    
    # Run the demo
    asyncio.run(main())