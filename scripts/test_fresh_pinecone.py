"""Fresh Pinecone test with configuration reload."""

import asyncio
import os
from pinecone import Pinecone
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Force reload of environment variables
load_dotenv(override=True)

async def test_fresh_pinecone():
    """Test Pinecone with fresh configuration."""
    print("Testing Pinecone with Fresh Configuration")
    print("=" * 45)
    
    # Get configuration directly from environment
    api_key = os.getenv('PINECONE_API_KEY')
    index_name = os.getenv('PINECONE_INDEX_NAME', 'spool-textbook-embeddings')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    print(f"\n🔧 Fresh Configuration:")
    print(f"PINECONE_API_KEY: {'✓ Set' if api_key else '✗ Missing'}")
    print(f"PINECONE_INDEX_NAME: {index_name}")
    print(f"OPENAI_API_KEY: {'✓ Set' if openai_key else '✗ Missing'}")
    
    if not api_key or not openai_key:
        print("\n❌ Missing required API keys.")
        return
    
    try:
        # Test 1: Pinecone Connection
        print(f"\n1. Testing Pinecone Connection...")
        pc = Pinecone(api_key=api_key)
        
        # List indexes
        indexes = pc.list_indexes()
        print(f"✓ Pinecone connected successfully")
        print(f"Available indexes: {[idx.name for idx in indexes]}")
        
        # Check if our index exists
        index_exists = any(idx.name == index_name for idx in indexes)
        print(f"Index '{index_name}' exists: {'✓ Yes' if index_exists else '✗ No'}")
        
        if not index_exists:
            print(f"❌ Index '{index_name}' not found.")
            return
        
        # Test 2: Index Operations
        print(f"\n2. Testing Index Operations...")
        index = pc.Index(index_name)
        
        # Get index stats
        stats = index.describe_index_stats()
        print(f"✓ Connected to index '{index_name}'")
        print(f"Vector count: {stats.total_vector_count}")
        print(f"Index dimension: {stats.dimension}")
        
        if stats.total_vector_count == 0:
            print("⚠️  Index is empty - no vectors to search")
            return
        
        # Test 3: OpenAI Embedding
        print(f"\n3. Testing OpenAI Embedding...")
        openai_client = AsyncOpenAI(api_key=openai_key)
        
        test_text = "quadratic equations algebra mathematics"
        response = await openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=test_text
        )
        embedding = response.data[0].embedding
        print(f"✓ Generated embedding for: '{test_text}'")
        print(f"Embedding dimension: {len(embedding)}")
        
        # Test 4: Vector Search
        print(f"\n4. Testing Vector Search...")
        query_response = index.query(
            vector=embedding,
            top_k=5,
            include_metadata=True
        )
        
        print(f"✓ Vector search completed")
        print(f"Results found: {len(query_response.matches)}")
        
        for i, match in enumerate(query_response.matches):
            print(f"\n📚 Result {i+1}:")
            print(f"  📊 Relevance Score: {match.score:.4f}")
            print(f"  🆔 Vector ID: {match.id}")
            
            if match.metadata:
                # Display metadata information
                text = match.metadata.get('text', match.metadata.get('content', 'No content'))
                book = match.metadata.get('book', match.metadata.get('title', 'Unknown'))
                subject = match.metadata.get('subject', 'Unknown')
                chapter = match.metadata.get('chapter', '')
                
                print(f"  📖 Book: {book}")
                print(f"  📚 Subject: {subject}")
                if chapter:
                    print(f"  📑 Chapter: {chapter}")
                print(f"  📄 Content: {text[:150]}...")
        
        print(f"\n🎉 SUCCESS! Pinecone integration is working perfectly!")
        print(f"✅ Vector search returned {len(query_response.matches)} relevant educational content chunks")
        print(f"✅ This content can now enhance exercise generation, evaluation, and remediation")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_fresh_pinecone()) 