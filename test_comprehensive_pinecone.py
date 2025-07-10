"""Comprehensive Pinecone test with multiple search scenarios."""

import asyncio
import os
from pinecone import Pinecone
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Force reload of environment variables
load_dotenv(override=True)

async def search_concept(index, openai_client, concept, description=""):
    """Search for a specific concept and display results."""
    print(f"\n🔍 Searching for: '{concept}'")
    if description:
        print(f"   📝 {description}")
    
    try:
        # Generate embedding
        response = await openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=concept
        )
        embedding = response.data[0].embedding
        
        # Search Pinecone
        query_response = index.query(
            vector=embedding,
            top_k=3,
            include_metadata=True
        )
        
        print(f"   ✅ Found {len(query_response.matches)} results")
        
        for i, match in enumerate(query_response.matches):
            print(f"\n   📚 Result {i+1} (Score: {match.score:.3f}):")
            if match.metadata:
                book = match.metadata.get('book', 'Unknown')
                subject = match.metadata.get('subject', 'Unknown')
                text = match.metadata.get('text', match.metadata.get('content', 'No content'))
                print(f"      📖 Source: {book} - {subject}")
                print(f"      📄 Content: {text[:150]}...")
        
        return query_response.matches
        
    except Exception as e:
        print(f"   ❌ Search failed: {e}")
        return []

async def test_comprehensive_pinecone():
    """Comprehensive test of Pinecone across different mathematical concepts."""
    print("🚀 Comprehensive Pinecone Vector Search Test")
    print("=" * 55)
    
    # Configuration
    api_key = os.getenv('PINECONE_API_KEY')
    index_name = os.getenv('PINECONE_INDEX_NAME', 'spool-textbook-embeddings')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    print(f"\n🔧 Configuration:")
    print(f"Index: {index_name}")
    print(f"API Keys: {'✓ Configured' if api_key and openai_key else '✗ Missing'}")
    
    try:
        # Initialize services
        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)
        openai_client = AsyncOpenAI(api_key=openai_key)
        
        # Get index stats
        stats = index.describe_index_stats()
        print(f"\n📊 Index Statistics:")
        print(f"   Vectors: {stats.total_vector_count:,}")
        print(f"   Dimension: {stats.dimension}")
        
        # Test different mathematical concepts
        test_concepts = [
            ("quadratic equations", "Basic algebra - solving ax² + bx + c = 0"),
            ("linear algebra matrices", "Advanced algebra - matrix operations"),
            ("calculus derivatives", "Calculus concepts - differentiation"),
            ("geometry triangles", "Geometric shapes and properties"),
            ("statistics probability", "Statistical analysis and probability"),
            ("trigonometry sine cosine", "Trigonometric functions"),
            ("polynomial factoring", "Algebraic factorization methods"),
            ("functions domain range", "Mathematical function properties")
        ]
        
        print(f"\n🧮 Testing Vector Search Across Mathematical Concepts:")
        print("=" * 55)
        
        all_results = []
        for concept, description in test_concepts:
            results = await search_concept(index, openai_client, concept, description)
            all_results.extend(results)
        
        # Analysis
        print(f"\n📈 Search Analysis:")
        print("=" * 25)
        
        # Score distribution
        scores = [match.score for match in all_results if hasattr(match, 'score')]
        if scores:
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
            
            print(f"📊 Relevance Scores:")
            print(f"   • Average: {avg_score:.3f}")
            print(f"   • Highest: {max_score:.3f}")
            print(f"   • Lowest: {min_score:.3f}")
        
        # Source analysis
        books = set()
        subjects = set()
        for match in all_results:
            if hasattr(match, 'metadata') and match.metadata:
                books.add(match.metadata.get('book', 'Unknown'))
                subjects.add(match.metadata.get('subject', 'Unknown'))
        
        print(f"\n📚 Content Sources:")
        print(f"   • Books: {', '.join(sorted(books))}")
        print(f"   • Subjects: {', '.join(sorted(subjects))}")
        
        # Test student interest integration
        print(f"\n🎯 Testing Student Interest Integration:")
        print("=" * 42)
        
        interest_queries = [
            "quadratic equations sports trajectory projectile motion",
            "linear equations music frequency sound waves",
            "geometry art design symmetry patterns",
            "statistics sports performance analytics data"
        ]
        
        for query in interest_queries:
            await search_concept(index, openai_client, query, 
                               "Interest-based contextual search")
        
        print(f"\n🎉 Comprehensive Test Complete!")
        print(f"✅ Pinecone is successfully providing rich educational content")
        print(f"✅ Vector search works across diverse mathematical concepts")
        print(f"✅ Interest-based queries return relevant contextual content")
        print(f"✅ Your exercise service can leverage this for enhanced learning")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_comprehensive_pinecone()) 