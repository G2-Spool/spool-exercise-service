"""Personality loader utility for system prompt personalization."""

import os
from typing import Optional
import structlog
from pathlib import Path

logger = structlog.get_logger()


class PersonalityLoader:
    """Load and apply personality profiles to system prompts."""
    
    def __init__(self):
        self.personalities_dir = Path(__file__).parent
        self.available_personalities = self._load_available_personalities()
    
    def _load_available_personalities(self) -> dict:
        """Load all available personality profiles."""
        personalities = {}
        
        for file_path in self.personalities_dir.glob("*.md"):
            if file_path.name != "personality_loader.py":
                personality_name = file_path.stem
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        personalities[personality_name] = content
                except Exception as e:
                    logger.warning(f"Failed to load personality {personality_name}: {e}")
        
        logger.info(f"Loaded {len(personalities)} personality profiles", 
                   personalities=list(personalities.keys()))
        return personalities
    
    def get_personality_prompt(self, personality: Optional[str] = None) -> str:
        """Get the personality prompt text for a given personality."""
        if not personality:
            personality = "default"
        
        if personality not in self.available_personalities:
            logger.warning(f"Unknown personality '{personality}', using default")
            personality = "default"
        
        if personality not in self.available_personalities:
            logger.error("Default personality not found, using empty string")
            return ""
        
        return self.available_personalities[personality]
    
    def apply_personality_to_prompt(self, base_prompt: str, personality: Optional[str] = None) -> str:
        """Apply a personality profile to a base system prompt."""
        personality_content = self.get_personality_prompt(personality)
        
        if not personality_content:
            return base_prompt
        
        # Combine the base prompt with the personality profile
        combined_prompt = f"""
{base_prompt}

## PERSONALITY PROFILE
{personality_content}

## INSTRUCTION INTEGRATION
Apply the above personality profile to all your interactions. Your communication style, approach to learning, feedback style, and problem-solving approach should reflect the personality characteristics described above. Maintain the core educational requirements while expressing them through your unique teaching personality.
"""
        
        logger.info(f"Applied personality '{personality or 'default'}' to system prompt")
        return combined_prompt
    
    def list_available_personalities(self) -> list:
        """Get a list of all available personality names."""
        return list(self.available_personalities.keys())


# Global instance for use across the application
personality_loader = PersonalityLoader() 