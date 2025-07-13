"""API router for the main chat functionality."""

from fastapi import APIRouter, Request, HTTPException
import structlog

from app.models.chat import ChatRequest, ChatResponse
from app.agents.chat_agent import ChatAgent
from app.core.session import SessionManager
from app.resources.personalities.personality_loader import personality_loader

router = APIRouter()
logger = structlog.get_logger()


@router.get("/personalities")
async def get_personalities():
    """Get list of available personalities."""
    try:
        personalities = personality_loader.list_available_personalities()
        return {"personalities": personalities}
    except Exception as e:
        logger.error("Failed to get personalities", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve personalities")


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    chat_request: ChatRequest, request: Request
) -> ChatResponse:
    """Single endpoint for all chat interactions."""
    session_manager = SessionManager()
    chat_agent = ChatAgent()

    try:
        # 1. Get or create session state
        session_state = await session_manager.get_session_state(chat_request.session_id)

        # 2. Update session with any new profile info
        if chat_request.student_profile:
            session_state["student_profile"] = chat_request.student_profile
        
        # 3. Process the message through the chat agent
        agent_response = await chat_agent.process_chat_message(
            message=chat_request.message,
            action=chat_request.action or "chat",
            session_state=session_state,
        )

        # 4. Save the updated state
        final_state = await session_manager.update_session_state(
            chat_request.session_id, agent_response.get("session_state", {})
        )

        # 5. Return the response to the client
        return ChatResponse(
            message=agent_response.get("message", "Sorry, something went wrong."),
            session_state=final_state,
            available_actions=agent_response.get("available_actions", []),
            data=agent_response.get("data", {}),
        )

    except Exception as e:
        logger.error("Chat endpoint failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        ) 