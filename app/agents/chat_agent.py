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
        elif action == "get_new_exercise":
            return await self._handle_get_new_exercise(session_state)
        elif action == "practice":
            return await self._handle_practice(session_state)
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
        """Orchestrates response evaluation with comprehensive results presentation."""
        exercise = session_state.get("current_exercise")
        if not exercise:
            return self._create_error_response("No active exercise found in session.", session_state)

        concept = {"id": exercise.get("concept_id"), "name": exercise.get("topic")}

        tool_result = await self.evaluation_tool.evaluate(exercise, student_response, concept)
        
        # Present comprehensive evaluation results
        comprehensive_feedback = await self._craft_comprehensive_feedback_message(tool_result, session_state)

        session_state["current_evaluation"] = tool_result
        session_state["phase"] = "evaluation"
        
        # Determine available actions based on evaluation results
        available_actions = ["get_new_exercise"]
        
        # Only add "practice" button if remediation is needed
        evaluation_data = tool_result.get("evaluation", {})
        needs_remediation = evaluation_data.get("needs_remediation", False)
        understanding_score = evaluation_data.get("understanding_score", 1.0)
        
        # Show practice button if remediation is needed OR score is below 0.7
        if needs_remediation or understanding_score < 0.7:
            available_actions.append("practice")
            
        return {
            "message": comprehensive_feedback,
            "session_state": session_state,
            "available_actions": available_actions,
            "data": tool_result,
        }

    async def _handle_get_new_exercise(self, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle getting a new exercise, adjusting difficulty if needed."""
        evaluation = session_state.get("current_evaluation")
        student_profile = session_state.get("student_profile", {}).copy()
        
        # Check if score is 3/10 or lower (0.3 or lower) and adjust difficulty
        if evaluation:
            understanding_score = evaluation.get("evaluation", {}).get("understanding_score", 0.0)
            if understanding_score <= 0.3:
                # Lower the difficulty level
                current_difficulty = student_profile.get("difficulty", "basic")
                if current_difficulty == "advanced":
                    student_profile["difficulty"] = "intermediate"
                elif current_difficulty == "intermediate":
                    student_profile["difficulty"] = "basic"
                # If already at basic, keep it at basic
                
                # Update the session state with adjusted difficulty
                session_state["student_profile"] = student_profile
        
        # Generate new exercise with potentially adjusted difficulty
        concept = {"id": "linear_systems", "name": "Systems of Linear Equations", "content": "Systems of linear equations consist of multiple linear equations with the same variables that must be solved simultaneously using substitution, elimination, or graphing methods."}
        
        tool_result = await self.exercise_tool.generate(concept, student_profile)
        exercise_data = tool_result.get("exercise", {})

        intro_message = await self._craft_intro_message(exercise_data, session_state)

        # Clear previous session data and start fresh with new exercise
        session_state["current_exercise"] = exercise_data
        session_state["phase"] = "exercise"
        session_state.pop("current_evaluation", None)  # Clear previous evaluation
        session_state.pop("history", None)  # Clear chat history for fresh start

        return {
            "message": intro_message,
            "session_state": session_state,
            "available_actions": ["submit_answer", "get_hint", "ask_question"],
            "data": tool_result,
        }

    async def _handle_practice(self, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle practice button - requests remediation and walks through it."""
        evaluation = session_state.get("current_evaluation")
        exercise = session_state.get("current_exercise")
        if not evaluation or not exercise:
            return self._create_error_response("No evaluation found to generate practice session.", session_state)

        concept = {"id": exercise.get("concept_id"), "name": exercise.get("topic")}
        
        tool_result = await self.remediation_tool.generate(evaluation, exercise, concept, session_state.get("student_profile", {}))
        
        remediation_message = await self._craft_remediation_message(tool_result, session_state)
        
        session_state["phase"] = "remediation"
        
        return {
            "message": remediation_message,
            "session_state": session_state,
            "available_actions": ["get_new_exercise", "get_hint", "ask_question"],
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
            "available_actions": ["get_new_exercise", "get_hint", "ask_question"],
            "data": tool_result,
        }

    async def _handle_general_chat(self, message: str, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handles conversational turns that are not specific actions."""
        exercise = session_state.get("current_exercise")
        if not exercise:
            return self._create_error_response("No active exercise found in session.", session_state)
        
        # Determine if this is a question or a step submission
        is_question = await self._is_question(message)
        
        if is_question:
            # Handle as a question - provide scaffolded help
            return await self._handle_question(message, session_state)
        else:
            # Handle as a step submission - evaluate the work
            return await self._handle_step_submission(message, session_state)

    async def _is_question(self, message: str) -> bool:
        """Determines if the message is a question or a step submission."""
        # Simple heuristics for question detection
        message_lower = message.lower().strip()
        
        # Obvious question indicators
        if message_lower.endswith('?'):
            return True
        
        # Question words
        question_words = ['what', 'how', 'why', 'where', 'when', 'which', 'who', 'can', 'could', 'should', 'would', 'is', 'are', 'do', 'does', 'did']
        if any(message_lower.startswith(word + ' ') for word in question_words):
            return True
        
        # If it contains mathematical work (equations, numbers, steps), likely not a question
        if any(char in message for char in ['=', '+', '-', '*', '/', '(', ')']):
            return False
        
        # Use LLM as final arbiter for ambiguous cases
        prompt = f"""
        Determine if the following student message is a QUESTION asking for help, or a STEP/WORK submission showing their mathematical work:
        
        Student message: "{message}"
        
        Respond with only "QUESTION" or "STEP" - nothing else.
        """
        
        response = await self.client.chat.completions.create(
            model=settings.GENERATION_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = response.choices[0].message.content
        return "QUESTION" in (content.upper() if content else "")

    async def _handle_question(self, message: str, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handles when student asks a question - provides scaffolded help."""
        exercise = session_state.get("current_exercise")
        if not exercise:
            return self._create_error_response("No active exercise found in session.", session_state)
            
        personality_prompt = personality_loader.get_personality_prompt(session_state.get("personality_type"))
        
        prompt = f"""
        You are an AI tutor with the following personality: {personality_prompt}
        
        Current Exercise Context:
        - Scenario: {exercise.get('scenario', 'N/A')}
        - Problem: {exercise.get('problem', 'N/A')}
        - Expected Solution: {exercise.get('expected_solution', 'N/A')}
        - Hints: {exercise.get('hints', [])}
        
        Student Question: "{message}"
        
        Your task:
        1. Answer the student's question by providing scaffolded help related to the current exercise.
        2. Don't give away the complete solution - guide them to discover it themselves.
        3. Use the exercise context to provide relevant, specific help.
        4. Be encouraging and match your personality.
        5. Do NOT invent a name or any details for the student.
        6. **Crucially, any mathematical equations, variables, or expressions in your response MUST be enclosed in double dollar signs for LaTeX rendering. Example: $$2x + 3y = 7$$**
        """
        
        response = await self.client.chat.completions.create(
            model=settings.GENERATION_MODEL,
            messages=[{"role": "system", "content": "You are a conversational AI Tutor."}, {"role": "user", "content": prompt}]
        )
        
        return {
            "message": response.choices[0].message.content or "I'm here to help with your question!",
            "session_state": session_state,
            "available_actions": ["submit_answer", "get_hint", "ask_question"],
            "data": {"response_type": "question_help"},
        }

    async def _handle_step_submission(self, message: str, session_state: Dict[str, Any]) -> Dict[str, Any]:
        """Handles when student submits work/steps - provides acknowledgment WITHOUT evaluation."""
        exercise = session_state.get("current_exercise")
        if not exercise:
            return self._create_error_response("No active exercise found in session.", session_state)
            
        # For step submissions, just acknowledge receipt without evaluation
        personality_prompt = personality_loader.get_personality_prompt(session_state.get("personality_type"))
        
        prompt = f"""
        You are an AI tutor with the following personality: {personality_prompt}
        
        The student submitted some work/steps: "{message}"
        
        Your task:
        1. Briefly acknowledge their step submission in an encouraging way.
        2. Do NOT evaluate or judge their work - just acknowledge it.
        3. Encourage them to continue working or ask questions if needed.
        4. Keep it brief and supportive.
        5. Match your personality.
        6. Do NOT invent a name or any details for the student.
        7. **Crucially, any mathematical equations, variables, or expressions in your response MUST be enclosed in double dollar signs for LaTeX rendering. Example: $$x = 5$$**
        """
        
        response = await self.client.chat.completions.create(
            model=settings.GENERATION_MODEL,
            messages=[{"role": "system", "content": "You are a conversational AI Tutor."}, {"role": "user", "content": prompt}]
        )
        
        return {
            "message": response.choices[0].message.content or "Thanks for sharing your work! Keep going.",
            "session_state": session_state,
            "available_actions": ["submit_answer", "get_hint", "ask_question"],
            "data": {"response_type": "step_acknowledgment"},
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

    async def _craft_comprehensive_feedback_message(self, eval_data: Dict[str, Any], session_state: Dict[str, Any]) -> str:
        """Uses an LLM to craft a personality-driven comprehensive feedback message."""
        personality_prompt = personality_loader.get_personality_prompt(session_state.get("personality_type"))
        analysis = eval_data.get("analysis", {})
        prompt = f"""
        You are an AI tutor with the following personality: {personality_prompt}
        You just evaluated your student's response. Here is the comprehensive analysis:
        - Strengths: {', '.join(analysis.get('strengths',[]))}
        - Weaknesses: {', '.join(analysis.get('weaknesses',[]))}
        - Detailed Feedback: {analysis.get('detailed_feedback')}
        - Understanding Score: {eval_data.get('evaluation', {}).get('understanding_score', 'N/A')}
        - Correctness Score: {eval_data.get('evaluation', {}).get('correctness_score', 'N/A')}
        - Overall Score: {eval_data.get('evaluation', {}).get('overall_score', 'N/A')}

        Your task:
        1. Present this comprehensive feedback to the student based on your personality.
        2. Emphasize the positive aspects and areas for improvement.
        3. Do NOT invent a name or any other details for the student.
        4. **Crucially, any mathematical equations, variables, or expressions in your response MUST be enclosed in double dollar signs for LaTeX rendering. Example: $$y = mx + b$$**
        """
        response = await self.client.chat.completions.create(
            model=settings.GENERATION_MODEL,
            messages=[{"role": "system", "content": "You are a conversational AI Tutor."}, {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content or "Here's a comprehensive look at your work."

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