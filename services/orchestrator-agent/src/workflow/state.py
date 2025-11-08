# services/orchestrator-agent/src/workflow/state.py

from typing import List, Dict, TypedDict

# TypedDict provides a way to define a dictionary with a fixed set of keys and value types.
# This acts as our "schema" for the workflow's memory.
class VideoGenerationState(TypedDict):
    """
    Represents the state of a single video generation job.
    This dictionary is passed between all nodes in the graph.
    """
    # Input from the user
    prompt: str

    # Output from the Creative Agent (mocked for now)
    script: str
    storyboard: List[Dict]

    # Output from the Asset Generation Agent (mocked for now)
    asset_urls: Dict[str, str]

    # Final output from the Post-Production Agent (mocked for now)
    final_video_url: str

    # To handle any errors during the process
    error_message: str | None