"""The central chat agent for orchestrating user interactions."""

import json
from typing import Dict, Any
from openai import AsyncOpenAI
import structlog

from app.core.config import settings
from app.tools.exercise_tool import ExerciseTool
from app.tools.evaluation_tool import EvaluationTool
from app.tools.remediation_tool import RemediationTool
from app.resources.personalities.personality_loader import personality_loader

logger = structlog.get_logger()


class ChatAgent:
    """
    Orchestrates the chat flow, using specialized tools to generate and evaluate
    exercises, and applying a personality to the responses.
    """

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.exercise_tool = ExerciseTool()
        self.evaluation_tool = EvaluationTool()
        self.remediation_tool = RemediationTool()

    async def process_chat_message(
        self, message: str, action: str, session_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Main entry point for processing a user's message."""
        
        # Update personality in session from the latest student profile
        if session_state.get("student_profile", {}).get("personality_type"):
            session_state["personality_type"] = session_state["student_profile"]["personality_type"]

        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("test"):
             return self._handle_mock_action(action, session_state)

        if action == "generate_exercise":
            return await self._handle_generate_exercise(session_state)
        elif action == "submit_answer":
            return await self._handle_evaluate_response(message, session_state)
        elif action == "request_remediation":
            return await self._handle_request_remediation(session_state)
        else:
            return await self._handle_general_chat(message, session_state)

    async def _handle_generate_exercise(self, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrates exercise generation."""
        concept = {"id": "linear_systems", "name": "Systems of Linear Equations", "content": "Systems of linear equations consist of multiple linear equations with the same variables that must be solved simultaneously using substitution, elimination, or graphing methods."}
        
        tool_result = await self.exercise_tool.generate(concept, session_state.get("student_profile", {}))
        exercise_data = tool_result.get("exercise", {})

        intro_message = await self._craft_intro_message(exercise_data, session_state)

        session_state["current_exercise"] = exercise_data
        session_state["phase"] = "exercise"

        return {
            "message": intro_message,
            "session_state": session_state,
            "available_actions": ["submit_answer", "get_hint", "ask_question"],
            "data": tool_result,
        }

    async def _handle_evaluate_response(self, student_response: str, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrates response evaluation."""
        exercise = session_state.get("current_exercise")
        if not exercise:
            return self._create_error_response("No active exercise found in session.", session_state)

        concept = {"id": exercise.get("concept_id"), "name": exercise.get("topic")}

        tool_result = await self.evaluation_tool.evaluate(exercise, student_response, concept)
        
        feedback_message = await self._craft_feedback_message(tool_result, session_state)

        session_state["current_evaluation"] = tool_result
        session_state["phase"] = "evaluation"
        
        available_actions = ["new_exercise", "continue_chat"]
        if tool_result.get("evaluation", {}).get("needs_remediation"):
            available_actions.insert(0, "request_remediation")
            
        return {
            "message": feedback_message,
            "session_state": session_state,
            "available_actions": available_actions,
            "data": tool_result,
        }
        
    async def _handle_request_remediation(self, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrates remediation generation."""
        evaluation = session_state.get("current_evaluation")
        exercise = session_state.get("current_exercise")
        if not evaluation or not exercise:
            return self._create_error_response("No evaluation found to generate remediation.", session_state)

        concept = {"id": exercise.get("concept_id"), "name": exercise.get("topic")}
        
        tool_result = await self.remediation_tool.generate(evaluation, exercise, concept, session_state.get("student_profile", {}))
        
        remediation_message = await self._craft_remediation_message(tool_result, session_state)
        
        session_state["phase"] = "remediation"
        
        return {
            "message": remediation_message,
            "session_state": session_state,
            "available_actions": ["new_exercise", "ask_question"],
            "data": tool_result,
        }

    async def _handle_general_chat(self, message: str, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handles conversational turns that are not specific actions."""
        return {
            "message": "That's a great question! Let's explore that. (general chat not fully implemented yet)",
            "session_state": session_state,
            "available_actions": session_state.get("available_actions", []),
            "data": {},
        }

    async def _craft_intro_message(self, exercise_data: Dict[str, Any], session_state: Dict[str, Any]) -> str:
        """Uses an LLM to craft a personality-driven introduction to an exercise."""
        personality_prompt = personality_loader.get_personality_prompt(session_state.get("personality_type"))
        prompt = f"""
        You are an AI tutor with the following personality: {personality_prompt}
        A new exercise has been generated for your student:
        - Scenario: {exercise_data.get('scenario')}
        - Problem: {exercise_data.get('problem')}

        Your task:
        1. Introduce this exercise in an encouraging and engaging way that matches your personality.
        2. Keep it brief and focused on getting the student started.
        3. Do NOT invent a name or any other details for the student. Refer to them as "you".
        4. Do NOT say "you're on the right track" or similar, as the student has not started yet.
        5. **Crucially, any mathematical equations, variables, or expressions in your response MUST be enclosed in double dollar signs for LaTeX rendering. Example: $$ax^2 + bx + c = 0$$**
        """
        response = await self.client.chat.completions.create(
            model=settings.GENERATION_MODEL,
            messages=[{"role": "system", "content": "You are a conversational AI Tutor."}, {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content or "Let's get started on your new exercise!"

    async def _craft_feedback_message(self, eval_data: Dict[str, Any], session_state: Dict[str, Any]) -> str:
        """Uses an LLM to craft personality-driven feedback."""
        personality_prompt = personality_loader.get_personality_prompt(session_state.get("personality_type"))
        analysis = eval_data.get("analysis", {})
        prompt = f"""
        You are an AI tutor with the following personality: {personality_prompt}
        You just evaluated your student's response. Here is the analysis:
        - Strengths: {', '.join(analysis.get('strengths',[]))}
        - Weaknesses: {', '.join(analysis.get('weaknesses',[]))}
        - Detailed Feedback: {analysis.get('detailed_feedback')}

        Your task:
        1. Deliver this feedback to the student based on your personality.
        2. Be encouraging, even if the score is low. Focus on growth and next steps.
        3. Do NOT invent a name or any other details for the student.
        4. **Crucially, any mathematical equations, variables, or expressions in your response MUST be enclosed in double dollar signs for LaTeX rendering. Example: $$y = mx + b$$**
        """
        response = await self.client.chat.completions.create(
            model=settings.GENERATION_MODEL,
            messages=[{"role": "system", "content": "You are a conversational AI Tutor."}, {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content or "Here's some feedback on your work."

    async def _craft_remediation_message(self, rem_data: Dict[str, Any], session_state: Dict[str, Any]) -> str:
        """Uses an LLM to craft a personality-driven remediation message."""
        personality_prompt = personality_loader.get_personality_prompt(session_state.get("personality_type"))
        remediation = rem_data.get("remediation", {})
        prompt = f"""
        You are an AI tutor with the following personality: {personality_prompt}
        You have generated a remediation plan to help your student with: {', '.join(remediation.get('target_gaps',[]))}
        The plan includes:
        - Explanations: {len(remediation.get('explanations',[]))}
        - Examples: {len(remediation.get('examples',[]))}
        - Practice Problems: {len(remediation.get('practice_problems',[]))}

        Your task:
        1. Introduce this remediation plan based on your personality.
        2. Frame it as a positive opportunity to strengthen their skills.
        3. Do NOT invent a name or any other details for the student.
        4. **Crucially, any mathematical equations, variables, or expressions in your response MUST be enclosed in double dollar signs for LaTeX rendering. Example: $$a^2 + b^2 = c^2$$**
        """
        response = await self.client.chat.completions.create(
            model=settings.GENERATION_MODEL,
            messages=[{"role": "system", "content": "You are a conversational AI Tutor."}, {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content or "Let's review some things to help you master this."
        
    def _create_error_response(self, error_message: str, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a standardized error response."""
        return {
            "message": f"An error occurred: {error_message}",
            "session_state": session_state,
            "available_actions": [],
            "data": {"error": True}
        }
        
    def _handle_mock_action(self, action: str, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handles mock responses for local testing."""
        if action == "generate_exercise":
            session_state["phase"] = "exercise"
            return {
                "message": "Mock Exercise: What is $$2+2$$?",
                "session_state": session_state,
                "available_actions": ["submit_answer"],
                "data": {"mock": True}
            }
        elif action == "submit_answer":
            session_state["phase"] = "evaluation"
            return {
                "message": "Mock Evaluation: You got it right!",
                "session_state": session_state,
                "available_actions": ["new_exercise"],
                "data": {"mock": True}
            }
        return self._create_error_response("Mock action not recognized.", session_state) 