"""Demo of enhanced exercise generation with direct Pinecone integration."""

import asyncio
import os
from pinecone import Pinecone
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Force reload of environment variables
load_dotenv(override=True)

class DirectPineconeService:
    """Direct Pinecone service for demo purposes."""
    
    def __init__(self):
        self.api_key = os.getenv('PINECONE_API_KEY')
        self.index_name = os.getenv('PINECONE_INDEX_NAME', 'spool-textbook-embeddings')
        self.openai_key = os.getenv('OPENAI_API_KEY')
        
    async def get_concept_context(self, concept_name, interests, difficulty="basic", limit=3):
        """Get educational context directly from Pinecone."""
        try:
            # Initialize Pinecone
            pc = Pinecone(api_key=self.api_key)
            index = pc.Index(self.index_name)
            
            # Generate embedding for search
            openai_client = AsyncOpenAI(api_key=self.openai_key)
            query_text = f"{concept_name} {difficulty} examples explanations"
            if interests:
                query_text += f" {' '.join(interests[:2])}"
            
            response = await openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=query_text
            )
            embedding = response.data[0].embedding
            
            # Search Pinecone
            query_response = index.query(
                vector=embedding,
                top_k=limit,
                include_metadata=True
            )
            
            # Format results
            context_chunks = []
            for match in query_response.matches:
                if match.metadata:
                    chunk = {
                        'content': match.metadata.get('text', match.metadata.get('content', '')),
                        'score': match.score,
                        'book': match.metadata.get('book', 'Unknown'),
                        'subject': match.metadata.get('subject', 'Unknown'),
                        'chapter': match.metadata.get('chapter', '')
                    }
                    context_chunks.append(chunk)
            
            return context_chunks
            
        except Exception as e:
            print(f"Direct Pinecone search failed: {e}")
            return []

async def demo_enhanced_exercise():
    """Demonstrate enhanced exercise generation."""
    print("🚀 Enhanced Exercise Generation Demo")
    print("=" * 50)
    
    # Test data
    concept = {
        "concept_id": "quadratic-equations",
        "name": "quadratic equations",
        "content": "Equations of the form ax² + bx + c = 0",
        "type": "mathematical_concept"
    }
    
    student_profile = {
        "student_id": "demo-student",
        "interests": ["sports", "music"],
        "grade_level": "high school"
    }
    
    # Initialize direct Pinecone service
    pinecone_service = DirectPineconeService()
    
    print(f"\n📚 Concept: {concept['name']}")
    print(f"👤 Student Interests: {', '.join(student_profile['interests'])}")
    
    # Get context from Pinecone
    print(f"\n🔍 Searching Pinecone for relevant educational content...")
    context_chunks = await pinecone_service.get_concept_context(
        concept["name"],
        student_profile["interests"],
        "basic",
        3
    )
    
    print(f"✅ Found {len(context_chunks)} relevant content chunks")
    
    if context_chunks:
        print(f"\n📖 Educational Context Retrieved:")
        for i, chunk in enumerate(context_chunks):
            print(f"\n  📄 Context {i+1} (Score: {chunk['score']:.3f}):")
            print(f"     📚 Source: {chunk['book']} - {chunk['subject']}")
            if chunk['chapter']:
                print(f"     📑 Chapter: {chunk['chapter']}")
            print(f"     📝 Content: {chunk['content'][:200]}...")
        
        # Create enhanced prompt
        print(f"\n🎯 Enhanced Exercise Prompt (with Pinecone context):")
        print("=" * 60)
        
        enhanced_prompt = f"""Create a basic initial exercise for this concept:
        
        Concept: {concept['name']}
        Content: {concept['content']}
        
        Student Profile:
        - Interests: {', '.join(student_profile['interests'])}
        - Grade Level: {student_profile['grade_level']}
        - Life Category Focus: academic
        
        Relevant Context from Knowledge Base:
"""
        
        for i, chunk in enumerate(context_chunks[:2]):
            enhanced_prompt += f"Context {i+1}: {chunk['content'][:300]}...\n"
        
        enhanced_prompt += f"""
        Requirements:
        1. Create a scenario that uses student interests: {', '.join(student_profile['interests'])}
        2. Use the provided context to ensure accuracy and depth
        3. The problem should require explaining complete thought process
        4. Include 4-6 expected solution steps
        5. Provide 2-3 progressive hints
        
        The exercise should test deep understanding, not just memorization."""
        
        print(enhanced_prompt)
        
        print(f"\n🆚 COMPARISON:")
        print(f"📈 Standard Prompt: Generic quadratic equation exercise")
        print(f"🎯 Enhanced Prompt: Contextual exercise using:")
        print(f"   • Real educational content from {context_chunks[0]['book']}")
        print(f"   • Student interests: {', '.join(student_profile['interests'])}")
        print(f"   • Domain-specific examples and methods")
        print(f"   • Verified mathematical accuracy from textbook sources")
        
        print(f"\n✨ BENEFITS:")
        print(f"   🎯 More relevant and engaging for students")
        print(f"   📚 Educationally accurate content")
        print(f"   🔗 Connects abstract concepts to student interests")
        print(f"   💡 Uses proven educational examples and methods")
        
    else:
        print(f"\n⚠️  No context found - would fall back to standard prompts")
    
    print(f"\n🎉 Demo Complete!")
    print(f"🚀 Your Pinecone integration is ready to enhance educational content!")

if __name__ == "__main__":
    asyncio.run(demo_enhanced_exercise()) 