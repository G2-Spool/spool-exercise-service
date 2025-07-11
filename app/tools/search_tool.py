"""Search tool for content retrieval and context augmentation."""

from typing import Dict, Any, List, Optional
import structlog
from app.services.pinecone_service import PineconeExerciseService

logger = structlog.get_logger()


class SearchTool:
    """Enhanced search tool for educational content retrieval."""
    
    def __init__(self):
        self.pinecone_service = PineconeExerciseService()
        self.enabled = True
        
    async def search_concept_definitions(self, concept_name: str, limit: int = 3) -> Dict[str, Any]:
        """
        Search for concept definitions and explanations.
        
        Args:
            concept_name: Name of the concept to search for
            limit: Maximum number of results to return
            
        Returns:
            Dictionary with search results
        """
        try:
            query = f"definition explanation {concept_name} what is meaning"
            results = await self.pinecone_service._search_content_service(
                query, limit, {"content_type": "definition"}
            )
            
            return {
                'success': True,
                'query': query,
                'concept': concept_name,
                'results': results,
                'count': len(results)
            }
            
        except Exception as e:
            logger.error("Concept definition search failed", concept=concept_name, error=str(e))
            return {
                'success': False,
                'error': str(e),
                'concept': concept_name,
                'results': []
            }
    
    async def search_examples(self, concept_name: str, context: str = "", limit: int = 3) -> Dict[str, Any]:
        """
        Search for examples and applications of a concept.
        
        Args:
            concept_name: Name of the concept
            context: Additional context for the search
            limit: Maximum number of results
            
        Returns:
            Dictionary with example results
        """
        try:
            query = f"examples applications {concept_name} {context}".strip()
            results = await self.pinecone_service._search_content_service(
                query, limit, {"content_type": "example"}
            )
            
            return {
                'success': True,
                'query': query,
                'concept': concept_name,
                'context': context,
                'results': results,
                'count': len(results)
            }
            
        except Exception as e:
            logger.error("Example search failed", concept=concept_name, error=str(e))
            return {
                'success': False,
                'error': str(e),
                'concept': concept_name,
                'results': []
            }
    
    async def search_step_by_step_guides(self, concept_name: str, difficulty: str = "basic", limit: int = 2) -> Dict[str, Any]:
        """
        Search for step-by-step guides and procedures.
        
        Args:
            concept_name: Name of the concept
            difficulty: Difficulty level (basic, intermediate, advanced)
            limit: Maximum number of results
            
        Returns:
            Dictionary with guide results
        """
        try:
            query = f"step by step guide procedure {concept_name} {difficulty} how to"
            results = await self.pinecone_service._search_content_service(
                query, limit, {"content_type": "guide"}
            )
            
            return {
                'success': True,
                'query': query,
                'concept': concept_name,
                'difficulty': difficulty,
                'results': results,
                'count': len(results)
            }
            
        except Exception as e:
            logger.error("Step-by-step guide search failed", concept=concept_name, error=str(e))
            return {
                'success': False,
                'error': str(e),
                'concept': concept_name,
                'results': []
            }
    
    async def search_common_mistakes(self, concept_name: str, limit: int = 3) -> Dict[str, Any]:
        """
        Search for common mistakes and misconceptions.
        
        Args:
            concept_name: Name of the concept
            limit: Maximum number of results
            
        Returns:
            Dictionary with mistake patterns
        """
        try:
            query = f"common mistakes errors misconceptions {concept_name} wrong typical"
            results = await self.pinecone_service._search_content_service(
                query, limit, {"content_type": "mistake"}
            )
            
            return {
                'success': True,
                'query': query,
                'concept': concept_name,
                'results': results,
                'count': len(results)
            }
            
        except Exception as e:
            logger.error("Common mistakes search failed", concept=concept_name, error=str(e))
            return {
                'success': False,
                'error': str(e),
                'concept': concept_name,
                'results': []
            }
    
    async def search_verification_methods(self, concept_name: str, limit: int = 2) -> Dict[str, Any]:
        """
        Search for verification and checking methods.
        
        Args:
            concept_name: Name of the concept
            limit: Maximum number of results
            
        Returns:
            Dictionary with verification methods
        """
        try:
            query = f"verify check validate {concept_name} how to confirm correct"
            results = await self.pinecone_service._search_content_service(
                query, limit, {"content_type": "verification"}
            )
            
            return {
                'success': True,
                'query': query,
                'concept': concept_name,
                'results': results,
                'count': len(results)
            }
            
        except Exception as e:
            logger.error("Verification methods search failed", concept=concept_name, error=str(e))
            return {
                'success': False,
                'error': str(e),
                'concept': concept_name,
                'results': []
            }
    
    async def comprehensive_search(self, concept_name: str, student_interests: List[str] = None, difficulty: str = "basic") -> Dict[str, Any]:
        """
        Perform comprehensive search for all types of content.
        
        Args:
            concept_name: Name of the concept
            student_interests: List of student interests
            difficulty: Difficulty level
            
        Returns:
            Dictionary with comprehensive search results
        """
        try:
                         # Get context from Pinecone service
            context_chunks = await self.pinecone_service.get_concept_context(
                concept_name, 
                student_interests if student_interests is not None else [], 
                difficulty
            )
            
                         # Search for different types of content
            search_tasks = [
                self.search_concept_definitions(concept_name, 2),
                self.search_examples(concept_name, " ".join(student_interests if student_interests is not None else []), 2),
                self.search_step_by_step_guides(concept_name, difficulty, 2),
                self.search_common_mistakes(concept_name, 2),
                self.search_verification_methods(concept_name, 1)
            ]
            
            # Execute all searches (in sequence for now)
            definitions = await search_tasks[0]
            examples = await search_tasks[1]
            guides = await search_tasks[2]
            mistakes = await search_tasks[3]
            verification = await search_tasks[4]
            
            return {
                'success': True,
                'concept': concept_name,
                'student_interests': student_interests,
                'difficulty': difficulty,
                'context_chunks': context_chunks,
                'definitions': definitions,
                'examples': examples,
                'guides': guides,
                'mistakes': mistakes,
                'verification': verification,
                'total_results': (
                    definitions['count'] + 
                    examples['count'] + 
                    guides['count'] + 
                    mistakes['count'] + 
                    verification['count']
                )
            }
            
        except Exception as e:
            logger.error("Comprehensive search failed", concept=concept_name, error=str(e))
            return {
                'success': False,
                'error': str(e),
                'concept': concept_name
            }
    
    async def search_for_prompt_enhancement(self, base_query: str, enhancement_type: str = "context") -> Dict[str, Any]:
        """
        Search for content to enhance prompts.
        
        Args:
            base_query: Base search query
            enhancement_type: Type of enhancement (context, examples, verification)
            
        Returns:
            Dictionary with enhancement content
        """
        try:
            if enhancement_type == "context":
                query = f"context background information {base_query}"
            elif enhancement_type == "examples":
                query = f"examples demonstrations {base_query}"
            elif enhancement_type == "verification":
                query = f"verification checking methods {base_query}"
            else:
                query = base_query
            
            results = await self.pinecone_service._search_content_service(query, 3)
            
            return {
                'success': True,
                'query': query,
                'enhancement_type': enhancement_type,
                'results': results,
                'count': len(results)
            }
            
        except Exception as e:
            logger.error("Prompt enhancement search failed", query=base_query, error=str(e))
            return {
                'success': False,
                'error': str(e),
                'query': base_query,
                'results': []
            }
    
    def get_tool_description(self) -> str:
        """Get description of search tool capabilities."""
        return """
        Search Tool - Available for content retrieval and context augmentation:
        
        **Functions:**
        - search_concept_definitions(concept, limit=3): Find definitions and explanations
        - search_examples(concept, context="", limit=3): Find examples and applications
        - search_step_by_step_guides(concept, difficulty="basic", limit=2): Find procedures
        - search_common_mistakes(concept, limit=3): Find typical errors and misconceptions
        - search_verification_methods(concept, limit=2): Find checking methods
        - comprehensive_search(concept, interests=None, difficulty="basic"): All-in-one search
        - search_for_prompt_enhancement(query, type="context"): Enhance prompts with context
        
        **Use Cases:**
        - Exercise Generation: Get context, examples, and real-world applications
        - Response Evaluation: Access verification methods and common mistakes
        - Remediation: Find step-by-step guides and targeted explanations
        
        **Examples:**
        - search_concept_definitions("quadratic equations") → definitions and explanations
        - search_examples("quadratic equations", "sports basketball") → sports-related examples
        - comprehensive_search("algebra", ["music", "art"], "intermediate") → full context
        """ 