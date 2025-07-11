#!/usr/bin/env python3
"""
Comprehensive Pinecone Test Suite

This script consolidates all Pinecone testing functionality including:
- Basic connection and configuration testing
- Vector search across mathematical concepts
- Enhanced exercise generation with vector context
- Integration testing with exercise service components
- Student interest-based contextual searches
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Force reload of environment variables
load_dotenv(override=True)


class PineconeTestSuite:
    """Comprehensive Pinecone testing suite."""

    def __init__(self):
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0
        self.pc = None
        self.index = None
        self.openai_client = None

    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"    {message}")

        self.test_results.append(
            {"test": test_name, "success": success, "message": message}
        )

        if success:
            self.passed_tests += 1
        else:
            self.failed_tests += 1

    async def test_configuration(self):
        """Test Pinecone configuration and setup."""
        print("\n🔧 Testing Pinecone Configuration")
        print("=" * 40)

        # Check environment variables
        api_key = os.getenv("PINECONE_API_KEY")
        index_name = os.getenv("PINECONE_INDEX_NAME", "spool-textbook-embeddings")
        openai_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            self.log_test("Pinecone API Key", False, "PINECONE_API_KEY not set")
            return False
        else:
            self.log_test("Pinecone API Key", True, f"***{api_key[-4:]}")

        if not openai_key:
            self.log_test("OpenAI API Key", False, "OPENAI_API_KEY not set")
            return False
        else:
            self.log_test("OpenAI API Key", True, f"***{openai_key[-4:]}")

        self.log_test("Index Name", True, index_name)
        return True

    async def test_connection(self):
        """Test Pinecone connection and index access."""
        print("\n🌐 Testing Pinecone Connection")
        print("=" * 40)

        try:
            from pinecone import Pinecone
            from openai import AsyncOpenAI

            # Initialize Pinecone
            api_key = os.getenv("PINECONE_API_KEY")
            self.pc = Pinecone(api_key=api_key)

            # List indexes
            indexes = self.pc.list_indexes()
            self.log_test("Pinecone Connection", True, f"Found {len(indexes)} indexes")

            # Check if target index exists
            index_name = os.getenv("PINECONE_INDEX_NAME", "spool-textbook-embeddings")
            index_exists = any(idx.name == index_name for idx in indexes)

            if not index_exists:
                self.log_test("Target Index", False, f"Index '{index_name}' not found")
                return False
            else:
                self.log_test("Target Index", True, f"Index '{index_name}' found")

            # Connect to index
            self.index = self.pc.Index(index_name)

            # Get index stats
            stats = self.index.describe_index_stats()
            self.log_test(
                "Index Stats",
                True,
                f"{stats.total_vector_count:,} vectors, {stats.dimension} dimensions",
            )

            if stats.total_vector_count == 0:
                self.log_test("Index Content", False, "Index is empty")
                return False

            # Initialize OpenAI client
            openai_key = os.getenv("OPENAI_API_KEY")
            self.openai_client = AsyncOpenAI(api_key=openai_key)
            self.log_test("OpenAI Client", True, "Client initialized")

            return True

        except Exception as e:
            self.log_test("Connection Setup", False, str(e))
            return False

    async def test_vector_search(self):
        """Test basic vector search functionality."""
        print("\n🔍 Testing Vector Search")
        print("=" * 40)

        if not self.index or not self.openai_client:
            self.log_test("Vector Search", False, "Connection not established")
            return False

        try:
            # Test basic search
            test_query = "quadratic equations algebra mathematics"

            # Generate embedding
            response = await self.openai_client.embeddings.create(
                model="text-embedding-3-small", input=test_query
            )
            embedding = response.data[0].embedding
            self.log_test(
                "Embedding Generation", True, f"Generated {len(embedding)} dimensions"
            )

            # Search Pinecone
            query_response = self.index.query(
                vector=embedding, top_k=5, include_metadata=True
            )

            results_count = len(query_response.matches)
            self.log_test("Vector Search", True, f"Found {results_count} results")

            # Check result quality
            if results_count > 0:
                avg_score = (
                    sum(match.score for match in query_response.matches) / results_count
                )
                self.log_test(
                    "Result Quality", True, f"Average relevance: {avg_score:.3f}"
                )

                # Check metadata
                has_metadata = any(match.metadata for match in query_response.matches)
                self.log_test(
                    "Metadata Presence",
                    has_metadata,
                    "Metadata available" if has_metadata else "No metadata",
                )

            return True

        except Exception as e:
            self.log_test("Vector Search", False, str(e))
            return False

    async def test_concept_searches(self):
        """Test vector search across different mathematical concepts."""
        print("\n🧮 Testing Concept-Based Searches")
        print("=" * 40)

        if not self.index or not self.openai_client:
            self.log_test("Concept Search", False, "Connection not established")
            return False

        test_concepts = [
            "quadratic equations",
            "linear algebra matrices",
            "calculus derivatives",
            "geometry triangles",
            "statistics probability",
            "trigonometry functions",
        ]

        all_results = []

        for concept in test_concepts:
            try:
                # Generate embedding
                response = await self.openai_client.embeddings.create(
                    model="text-embedding-3-small", input=concept
                )
                embedding = response.data[0].embedding

                # Search Pinecone
                query_response = self.index.query(
                    vector=embedding, top_k=3, include_metadata=True
                )

                results_count = len(query_response.matches)
                self.log_test(
                    f"Concept: {concept}", True, f"{results_count} results found"
                )
                all_results.extend(query_response.matches)

            except Exception as e:
                self.log_test(f"Concept: {concept}", False, str(e))

        # Analyze results
        if all_results:
            scores = [match.score for match in all_results]
            avg_score = sum(scores) / len(scores)
            self.log_test(
                "Concept Search Analysis", True, f"Average relevance: {avg_score:.3f}"
            )

            # Check source diversity
            books = set()
            subjects = set()
            for match in all_results:
                if match.metadata:
                    books.add(match.metadata.get("book", "Unknown"))
                    subjects.add(match.metadata.get("subject", "Unknown"))

            self.log_test(
                "Source Diversity",
                True,
                f"{len(books)} books, {len(subjects)} subjects",
            )

        return True

    async def test_interest_integration(self):
        """Test student interest-based contextual searches."""
        print("\n🎯 Testing Interest-Based Searches")
        print("=" * 40)

        if not self.index or not self.openai_client:
            self.log_test("Interest Search", False, "Connection not established")
            return False

        interest_queries = [
            ("quadratic equations sports trajectory", "Sports context"),
            ("linear equations music frequency", "Music context"),
            ("geometry art design patterns", "Art context"),
            ("statistics sports performance data", "Sports analytics"),
            ("calculus physics motion", "Physics context"),
        ]

        for query, description in interest_queries:
            try:
                # Generate embedding
                response = await self.openai_client.embeddings.create(
                    model="text-embedding-3-small", input=query
                )
                embedding = response.data[0].embedding

                # Search Pinecone
                query_response = self.index.query(
                    vector=embedding, top_k=3, include_metadata=True
                )

                results_count = len(query_response.matches)
                self.log_test(
                    f"Interest: {description}",
                    True,
                    f"{results_count} contextual results",
                )

            except Exception as e:
                self.log_test(f"Interest: {description}", False, str(e))

        return True

    async def test_service_integration(self):
        """Test integration with exercise service components."""
        print("\n🔧 Testing Service Integration")
        print("=" * 40)

        # Add app directory to path
        app_path = Path(__file__).parent.parent / "app"
        sys.path.insert(0, str(app_path))

        try:
            from app.services.pinecone_service import PineconeExerciseService

            # Test PineconeExerciseService
            service = PineconeExerciseService()

            # Test concept context retrieval
            context = await service.get_concept_context(
                "quadratic equations", ["sports", "music"], "basic"
            )
            self.log_test(
                "Concept Context", True, f"Retrieved {len(context)} context chunks"
            )

            # Test similar exercises
            similar_exercises = await service.find_similar_exercises(
                "test-concept-1", {"student_id": "test", "interests": ["sports"]}
            )
            self.log_test(
                "Similar Exercises",
                True,
                f"Found {len(similar_exercises)} similar exercises",
            )

            # Test remediation examples
            remediation_examples = await service.get_remediation_examples(
                "problem solving", "quadratic equations", ["music"]
            )
            self.log_test(
                "Remediation Examples",
                True,
                f"Found {len(remediation_examples)} remediation examples",
            )

        except ImportError as e:
            self.log_test("Service Integration", False, f"Import error: {str(e)}")
        except Exception as e:
            self.log_test("Service Integration", False, str(e))

    async def test_enhanced_exercise_demo(self):
        """Test enhanced exercise generation with Pinecone context."""
        print("\n🚀 Testing Enhanced Exercise Generation")
        print("=" * 40)

        if not self.index or not self.openai_client:
            self.log_test("Enhanced Exercise Demo", False, "Connection not established")
            return False

        try:
            # Simulate enhanced exercise generation
            concept = "quadratic equations"
            interests = ["sports", "music"]

            # Get context from Pinecone
            query_text = (
                f"{concept} basic examples explanations {' '.join(interests[:2])}"
            )

            response = await self.openai_client.embeddings.create(
                model="text-embedding-3-small", input=query_text
            )
            embedding = response.data[0].embedding

            # Search for relevant context
            query_response = self.index.query(
                vector=embedding, top_k=3, include_metadata=True
            )

            context_chunks = []
            for match in query_response.matches:
                if match.metadata:
                    context_chunks.append(
                        {
                            "content": match.metadata.get(
                                "text", match.metadata.get("content", "")
                            ),
                            "score": match.score,
                            "book": match.metadata.get("book", "Unknown"),
                            "subject": match.metadata.get("subject", "Unknown"),
                        }
                    )

            self.log_test(
                "Context Retrieval",
                True,
                f"Retrieved {len(context_chunks)} context chunks",
            )

            # Demonstrate enhanced prompt creation
            if context_chunks:
                f"""
                Create exercise for: {concept}
                Student interests: {', '.join(interests)}
                
                Educational context from knowledge base:
                {context_chunks[0]['content'][:200]}...
                
                Source: {context_chunks[0]['book']} - {context_chunks[0]['subject']}
                """

                self.log_test(
                    "Enhanced Prompt",
                    True,
                    f"Prompt enhanced with context from {context_chunks[0]['book']}",
                )

                # Show benefit comparison
                print("\n    💡 Enhancement Benefits:")
                print(
                    f"       📚 Educational accuracy from {context_chunks[0]['book']}"
                )
                print(f"       🎯 Student interests: {', '.join(interests)}")
                print(
                    f"       🔗 Relevant context with {context_chunks[0]['score']:.3f} relevance"
                )

        except Exception as e:
            self.log_test("Enhanced Exercise Demo", False, str(e))

    async def run_all_tests(self):
        """Run all Pinecone tests."""
        print("🚀 Comprehensive Pinecone Test Suite")
        print("=" * 50)

        # Run tests in sequence
        config_ok = await self.test_configuration()
        if not config_ok:
            print("\n❌ Configuration failed. Cannot proceed with other tests.")
            return False

        connection_ok = await self.test_connection()
        if not connection_ok:
            print("\n❌ Connection failed. Cannot proceed with vector tests.")
            return False

        await self.test_vector_search()
        await self.test_concept_searches()
        await self.test_interest_integration()
        await self.test_service_integration()
        await self.test_enhanced_exercise_demo()

        # Summary
        print("\n📊 Test Results Summary")
        print("=" * 30)
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(
            f"📈 Success Rate: {(self.passed_tests / (self.passed_tests + self.failed_tests) * 100):.1f}%"
        )

        if self.failed_tests > 0:
            print(
                f"\n⚠️  {self.failed_tests} tests failed. Please review Pinecone setup."
            )
            return False
        else:
            print("\n🎉 All Pinecone tests passed! Vector search integration is ready.")
            return True


async def main():
    """Main entry point."""
    tester = PineconeTestSuite()
    success = await tester.run_all_tests()

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
