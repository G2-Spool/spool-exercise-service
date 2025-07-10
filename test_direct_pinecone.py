"""Direct Pinecone integration test - bypasses content service."""

import asyncio
import os
from pinecone import Pinecone
from openai import AsyncOpenAI
from app.core.config import settings


async def test_direct_pinecone():
    """Test direct Pinecone connection and search."""
    print("Testing Direct Pinecone Integration")
    print("=" * 40)
    
    # Check environment variables
    print(f"\n🔧 Configuration:")
    print(f"PINECONE_API_KEY: {'✓ Set' if settings.PINECONE_API_KEY else '✗ Missing'}")
    print(f"PINECONE_INDEX_NAME: {settings.PINECONE_INDEX_NAME}")
    print(f"PINECONE_ENVIRONMENT: {settings.PINECONE_ENVIRONMENT}")
    print(f"ENABLE_VECTOR_CONTEXT: {settings.ENABLE_VECTOR_CONTEXT}")
    print(f"OPENAI_API_KEY: {'✓ Set' if settings.OPENAI_API_KEY else '✗ Missing'}")
    
    if not settings.PINECONE_API_KEY or not settings.OPENAI_API_KEY:
        print("\n❌ Missing required API keys. Please check your .env file.")
        return
    
    try:
        # Test 1: Pinecone Connection
        print(f"\n1. Testing Pinecone Connection...")
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        
        # List indexes
        indexes = pc.list_indexes()
        print(f"✓ Pinecone connected successfully")
        print(f"Available indexes: {[idx.name for idx in indexes]}")
        
        # Check if our index exists
        index_name = settings.PINECONE_INDEX_NAME
        index_exists = any(idx.name == index_name for idx in indexes)
        print(f"Index '{index_name}' exists: {'✓ Yes' if index_exists else '✗ No'}")
        
        if not index_exists:
            print(f"❌ Index '{index_name}' not found. Available indexes: {[idx.name for idx in indexes]}")
            return
        
        # Test 2: Index Connection
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
        openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        test_text = "quadratic equations problem solving"
        response = await openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=test_text
        )
        embedding = response.data[0].embedding
        print(f"✓ Generated embedding for test text")
        print(f"Embedding dimension: {len(embedding)}")
        
        # Test 4: Vector Search
        print(f"\n4. Testing Vector Search...")
        query_response = index.query(
            vector=embedding,
            top_k=3,
            include_metadata=True
        )
        
        print(f"✓ Vector search completed")
        print(f"Results found: {len(query_response.matches)}")
        
        for i, match in enumerate(query_response.matches):
            print(f"\nResult {i+1}:")
            print(f"  Score: {match.score:.4f}")
            print(f"  ID: {match.id}")
            if match.metadata:
                print(f"  Content: {match.metadata.get('text', 'N/A')[:100]}...")
                print(f"  Book: {match.metadata.get('book', 'N/A')}")
                print(f"  Subject: {match.metadata.get('subject', 'N/A')}")
        
        print(f"\n🎉 Direct Pinecone integration test successful!")
        
    except Exception as e:
        print(f"\n❌ Direct Pinecone test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_direct_pinecone()) 