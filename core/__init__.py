"""
Core business logic modules for WebSpark.

This package contains the core functionality for:
- Macro recording and playback (macro_recorder)
- Selector configuration and management (selectors_config)
"""

# Make key classes available at package level for easier imports
from .macro_recorder import (
    MacroAction,
    Macro,
    RecordingSession,
    MacroStorage,
    MacroRecorderManager,
    PlaybackSession,
    recorder_manager
)

from .selectors_config import (
    PAGE_TYPE_SELECTORS,
    USE_AGENT_SELECTORS,
    AGENT_DISCOVERED_SELECTORS
)

__all__ = [
    # Macro recording classes
    'MacroAction',
    'Macro', 
    'RecordingSession',
    'MacroStorage',
    'MacroRecorderManager',
    'PlaybackSession',
    'recorder_manager',
    # Selector configuration
    'PAGE_TYPE_SELECTORS',
    'USE_AGENT_SELECTORS', 
    'AGENT_DISCOVERED_SELECTORS'
]