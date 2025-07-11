"""Pinecone integration for exercise service."""

from typing import List, Dict, Any, Optional
import structlog
import httpx
from openai import AsyncOpenAI

from app.core.config import settings

logger = structlog.get_logger()


class PineconeExerciseService:
    """Enhanced Pinecone service for exercise generation context."""

    def __init__(self) -> None:
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.content_service_url = settings.CONTENT_SERVICE_SEARCH_URL
        self.enabled = settings.ENABLE_VECTOR_CONTEXT

    async def get_concept_context(
        self,
        concept_name: str,
        student_interests: List[str],
        difficulty_level: str = "basic",
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        """Get relevant context for a concept from vector database."""
        if not self.enabled:
            return []

        try:
            # Create enhanced query combining concept and interests
            enhanced_query = self._create_enhanced_query(
                concept_name, student_interests, difficulty_level
            )

            # Search via content service
            context_chunks = await self._search_content_service(enhanced_query, limit)

            logger.info(
                "Retrieved concept context",
                concept=concept_name,
                chunks_found=len(context_chunks),
            )

            return context_chunks

        except Exception as e:
            logger.error(
                "Failed to get concept context", concept=concept_name, error=str(e)
            )
            return []

    async def find_similar_exercises(
        self,
        concept_id: str,
        student_profile: Dict[str, Any],
        exclude_exercise_id: Optional[str] = None,
        limit: int = 2,
    ) -> List[Dict[str, Any]]:
        """Find similar exercises for reference during generation."""
        if not self.enabled:
            return []

        try:
            interests = student_profile.get("interests", [])
            query = f"exercise problems for {concept_id} with {', '.join(interests)}"

            similar_content = await self._search_content_service(
                query, limit, {"content_type": "exercise"}
            )

            return similar_content

        except Exception as e:
            logger.error(
                "Failed to find similar exercises", concept_id=concept_id, error=str(e)
            )
            return []

    async def get_remediation_examples(
        self,
        target_gap: str,
        concept_name: str,
        student_interests: List[str],
        limit: int = 2,
    ) -> List[Dict[str, Any]]:
        """Get examples and explanations for remediation."""
        if not self.enabled:
            return []

        try:
            # Create targeted query for remediation
            query = f"examples explanations {target_gap} {concept_name} step by step"

            remediation_content = await self._search_content_service(
                query, limit, {"content_type": "explanation"}
            )

            return remediation_content

        except Exception as e:
            logger.error(
                "Failed to get remediation examples",
                target_gap=target_gap,
                error=str(e),
            )
            return []

    def _create_enhanced_query(
        self, concept_name: str, student_interests: List[str], difficulty_level: str
    ) -> str:
        """Create enhanced query combining concept and student context."""
        base_query = f"{concept_name} {difficulty_level}"

        if student_interests:
            interests_part = " ".join(student_interests[:2])  # Use top 2 interests
            base_query += f" applications {interests_part}"

        return base_query

    async def _search_content_service(
        self, query: str, limit: int, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search content via content service API."""
        try:
            search_payload = {"query": query, "limit": limit}

            if filters:
                search_payload["filters"] = filters

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.content_service_url, json=search_payload, timeout=10.0
                )
                response.raise_for_status()

                results = response.json()
                return results if isinstance(results, list) else []

        except Exception as e:
            logger.error("Content service search failed", query=query, error=str(e))
            return []

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI."""
        try:
            response = await self.openai_client.embeddings.create(
                model="text-embedding-3-small", input=text.replace("\n", " ")
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error("Failed to generate embedding", error=str(e))
            return []
