"""
LLM Module
Handles LLM connections, state management, and orchestration for emergency handling
"""

from .state_manager import (
    ConversationState,
    SessionManager,
    EmergencyType,
    ConversationPhase,
    LocationInfo,
    MedicalInfo,
    FireInfo,
    PoliceInfo,
    DispatchInfo,
    session_manager
)

from .prompts import (
    build_system_prompt,
    get_tools_for_phase,
    QUICK_RESPONSES,
    BASE_SYSTEM_PROMPT
)

from .connect_llm import (
    get_simple_response,
    get_response_with_tools,
    get_streaming_response_with_history,
    get_response,  # Legacy
    DEFAULT_MODEL
)

from .orchestrator import (
    EmergencyOrchestrator,
    create_orchestrator,
    process_message
)

__all__ = [
    # State Management
    'ConversationState',
    'SessionManager', 
    'EmergencyType',
    'ConversationPhase',
    'LocationInfo',
    'MedicalInfo',
    'FireInfo',
    'PoliceInfo',
    'DispatchInfo',
    'session_manager',
    
    # Prompts
    'build_system_prompt',
    'get_tools_for_phase',
    'QUICK_RESPONSES',
    'BASE_SYSTEM_PROMPT',
    
    # LLM Connection
    'get_simple_response',
    'get_response_with_tools',
    'get_streaming_response_with_history',
    'get_response',
    'DEFAULT_MODEL',
    
    # Orchestrator
    'EmergencyOrchestrator',
    'create_orchestrator',
    'process_message',
]

