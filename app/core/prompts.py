"""Chain-of-thought prompting strategies and templates."""

from typing import Dict, Any, List, Optional


class ChainOfThoughtPrompts:
    """Enhanced prompts using chain-of-thought strategies."""
    
    @staticmethod
    def get_step_by_step_instruction_template() -> str:
        """Template for explicit step-by-step instructions."""
        return """
        Before providing your answer, please follow these steps:
        1. **Think through the problem**: First, analyze what is being asked
        2. **Plan your approach**: Outline your solution method
        3. **Execute step-by-step**: Work through each step systematically
        4. **Verify your work**: Check your reasoning and calculations
        5. **Present your answer**: Provide a clear, complete response
        
        Show your reasoning for each step before moving to the next.
        """
    
    @staticmethod
    def get_intermediate_questions_template() -> str:
        """Template for breaking complex tasks into subtasks."""
        return """
        Break down this task by answering these intermediate questions:
        
        **First, identify the key concepts:**
        - What are the main concepts involved?
        - What do I already know about these concepts?
        
        **Next, outline the solution steps:**
        - What method should I use to solve this?
        - What are the key steps in this method?
        
        **Finally, provide the answer:**
        - Execute the solution step by step
        - Verify the result makes sense
        """
    
    @staticmethod
    def get_self_check_template() -> str:
        """Template for self-verification prompts."""
        return """
        After completing your solution, perform these self-checks:
        
        **Verify your answer:**
        - Does your answer make sense in the context?
        - Have you addressed all parts of the problem?
        - Are your calculations correct?
        
        **Check your assumptions:**
        - What assumptions did you make?
        - Are these assumptions reasonable?
        - How might different assumptions change your answer?
        
        **Reflect on your method:**
        - Was this the most efficient approach?
        - Are there alternative methods that might work?
        """
    
    @staticmethod
    def get_worked_example_template(concept_name: str) -> str:
        """Template providing worked example format."""
        return f"""
        Here's the format to follow for {concept_name} problems:
        
        **Example Problem Format:**
        1. **Problem Statement**: Clearly state what needs to be solved
        2. **Given Information**: List what is known
        3. **Method Selection**: Choose the appropriate approach
        4. **Step-by-Step Solution**: 
           - Step 1: [Description and calculation]
           - Step 2: [Description and calculation]
           - Step 3: [Description and calculation]
        5. **Verification**: Check the answer by substitution or alternative method
        6. **Interpretation**: Explain what the answer means in context
        
        Follow this exact format for your solution.
        """
    
    @staticmethod
    def get_reflection_template() -> str:
        """Template for reflection and improvement."""
        return """
        **Reflection Step:**
        Now reflect on your solution:
        
        **Evaluate your approach:**
        - What worked well in your solution?
        - What was challenging about this problem?
        - How confident are you in your answer?
        
        **Consider improvements:**
        - How could you improve your solution method?
        - What would you do differently next time?
        - What additional practice would help you master this concept?
        
        **Alternative approaches:**
        - Are there other ways to solve this problem?
        - Which method would be most efficient?
        - When would you use different approaches?
        """
    
    @staticmethod
    def create_enhanced_exercise_prompt(
        concept: Dict[str, Any],
        student_profile: Dict[str, Any],
        context_chunks: List[Dict[str, Any]],
        **kwargs
    ) -> str:
        """Create enhanced exercise generation prompt with chain-of-thought."""
        base_prompt = f"""
        # Exercise Generation Task
        
        ## Your Mission
        Create a comprehensive exercise that tests deep understanding of {concept.get('name', 'the concept')}.
        
        ## Chain-of-Thought Process
        {ChainOfThoughtPrompts.get_step_by_step_instruction_template()}
        
        ## Student Context
        - **Interests**: {', '.join(student_profile.get('interests', []))}
        - **Grade Level**: {student_profile.get('grade_level', 'high school')}
        - **Learning Style**: Connect to real-world applications
        
        ## Concept Details
        - **Name**: {concept.get('name', 'Unknown')}
        - **Content**: {concept.get('content', 'No description provided')}
        - **Type**: {concept.get('type', 'general')}
        """
        
        # Add context if available
        if context_chunks:
            base_prompt += "\n## Additional Context\n"
            for i, chunk in enumerate(context_chunks[:2]):
                content = chunk.get('content', str(chunk))
                base_prompt += f"**Context {i+1}**: {content[:300]}...\n"
        
        base_prompt += f"""
        ## Exercise Requirements
        {ChainOfThoughtPrompts.get_intermediate_questions_template()}
        
        ## Expected Student Response Format
        {ChainOfThoughtPrompts.get_worked_example_template(concept.get('name', 'this concept'))}
        
        ## Quality Checklist
        {ChainOfThoughtPrompts.get_self_check_template()}
        
        ## Final Instructions
        Create an exercise that requires students to:
        1. Demonstrate understanding of each concept component
        2. Show their complete reasoning process
        3. Verify their own work
        4. Connect the solution to real-world applications
        
        Return your response as JSON with the standard exercise format.
        """
        
        return base_prompt
    
    @staticmethod
    def create_enhanced_evaluation_prompt(
        exercise: Dict[str, Any],
        student_response: str,
        concept: Dict[str, Any],
        context_chunks: List[Dict[str, Any]],
        **kwargs
    ) -> str:
        """Create enhanced evaluation prompt with chain-of-thought."""
        base_prompt = f"""
        # Response Evaluation Task
        
        ## Your Mission
        Evaluate this student's response using rigorous educational assessment principles.
        
        ## Chain-of-Thought Evaluation Process
        {ChainOfThoughtPrompts.get_step_by_step_instruction_template()}
        
        ## Exercise Context
        **Concept**: {concept.get('name', 'Unknown')}
        **Problem**: {exercise.get('content', {}).get('problem', 'No problem specified')}
        **Expected Steps**: {exercise.get('expected_steps', [])}
        
        ## Student Response to Evaluate
        ```
        {student_response}
        ```
        
        ## Evaluation Framework
        {ChainOfThoughtPrompts.get_intermediate_questions_template()}
        
        ## Assessment Criteria
        For each expected step, determine:
        1. **Demonstrated Understanding**: What does the student clearly understand?
        2. **Process Quality**: How well did they explain their reasoning?
        3. **Accuracy**: Are their calculations and logic correct?
        4. **Completeness**: Did they address all required components?
        5. **Verification**: Did they check their work appropriately?
        """
        
        # Add context if available
        if context_chunks:
            base_prompt += "\n## Educational Context for Verification\n"
            for i, chunk in enumerate(context_chunks[:2]):
                content = chunk.get('content', str(chunk))
                base_prompt += f"**Reference {i+1}**: {content[:300]}...\n"
        
        base_prompt += f"""
        ## Evaluation Checklist
        {ChainOfThoughtPrompts.get_self_check_template()}
        
        ## Scoring Guidelines
        - **10/10**: Complete understanding, perfect execution, clear reasoning
        - **8-9/10**: Strong understanding, minor gaps in explanation
        - **6-7/10**: Good understanding, some missing steps or reasoning
        - **4-5/10**: Partial understanding, significant gaps
        - **0-3/10**: Little to no understanding demonstrated
        
        ## Reflection on Evaluation
        {ChainOfThoughtPrompts.get_reflection_template()}
        
        Return your evaluation as JSON with detailed understanding_analysis including explicit "Understanding score: X/10".
        """
        
        return base_prompt
    
    @staticmethod
    def create_enhanced_remediation_prompt(
        concept: Dict[str, Any],
        target_gap: str,
        student_profile: Dict[str, Any],
        evaluation: Dict[str, Any],
        context_chunks: List[Dict[str, Any]],
        **kwargs
    ) -> str:
        """Create enhanced remediation prompt with chain-of-thought."""
        base_prompt = f"""
        # Remediation Generation Task
        
        ## Your Mission
        Create targeted remediation that transforms the learning gap into a growth opportunity.
        
        ## Chain-of-Thought Remediation Process
        {ChainOfThoughtPrompts.get_step_by_step_instruction_template()}
        
        ## Student Situation
        **Target Gap**: {target_gap}
        **Current Understanding**: {evaluation.get('understanding_score', 0):.1%}
        **Interests**: {', '.join(student_profile.get('interests', []))}
        **Strengths**: {evaluation.get('competency_map', {}).get('correct_steps', [])}
        
        ## Gap Analysis Framework
        {ChainOfThoughtPrompts.get_intermediate_questions_template()}
        
        ## Remediation Strategy
        1. **Build on Strengths**: Start with what the student did well
        2. **Address Specific Gaps**: Target the exact understanding gaps
        3. **Provide Scaffolding**: Break complex concepts into manageable steps
        4. **Connect to Interests**: Use their interests to maintain engagement
        5. **Include Practice**: Give concrete opportunities to apply learning
        """
        
        # Add context if available
        if context_chunks:
            base_prompt += "\n## Educational Resources\n"
            for i, chunk in enumerate(context_chunks[:2]):
                content = chunk.get('content', str(chunk))
                base_prompt += f"**Resource {i+1}**: {content[:300]}...\n"
        
        base_prompt += f"""
        ## Remediation Components
        Create remediation that includes:
        1. **Clear Explanation**: Address the specific gap with concrete examples
        2. **Guided Practice**: Step-by-step exercises with scaffolding
        3. **Self-Check Tools**: Ways for students to verify understanding
        4. **Real-World Connections**: Links to their interests and experiences
        5. **Confidence Building**: Positive reinforcement of their capabilities
        
        ## Quality Assurance
        {ChainOfThoughtPrompts.get_self_check_template()}
        
        ## Reflection on Remediation Design
        {ChainOfThoughtPrompts.get_reflection_template()}
        
        Return your remediation as JSON with comprehensive content addressing the learning gap.
        """
        
        return base_prompt 