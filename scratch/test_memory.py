import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.memory_manager import get_memory_manager

def test_memory():
    print("Testing MemoryManager...")
    try:
        # Get manager for a test agent
        mm = get_memory_manager("test_agent")
        
        # 1. Add some test data
        doc_id = mm.add(
            document="NeuroDesk is an AI multi-agent system for digital marketing.",
            metadata={"source": "test_script"}
        )
        print(f"✅ Added document with ID: {doc_id}")
        
        # 2. Query the data
        results = mm.query("What is NeuroDesk?")
        print(f"✅ Query results: {results.get('documents')}")
        
        # 3. Get all
        all_docs = mm.get_all()
        print(f"✅ Total documents in memory: {len(all_docs)}")
        
        # 4. Get stats
        stats = mm.get_stats()
        print(f"✅ Stats: {stats}")
        
        # 5. Cleanup
        mm.clear()
        print("✅ Memory cleared.")
        
        print("\nAll tests passed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_memory()
