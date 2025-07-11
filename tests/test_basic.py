"""Basic tests for the exercise service."""

import pytest


def test_basic_import():
    """Test that basic imports work."""
    from app.core.config import settings

    assert settings is not None


def test_langgraph_imports():
    """Test that langgraph imports work."""
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver

    assert StateGraph is not None
    assert END is not None
    assert MemorySaver is not None


@pytest.mark.asyncio
async def test_workflow_creation():
    """Test that workflow can be created."""
    from app.langgraph.workflows import ExerciseWorkflow

    workflow = ExerciseWorkflow()
    assert workflow is not None
