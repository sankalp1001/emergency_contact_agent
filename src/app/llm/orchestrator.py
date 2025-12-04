"""
LLM Orchestrator Module
Manages the complete flow between user input, LLM, tool execution, and response generation
All decision making is done by the LLM through tool calls - no keyword matching
"""

import json
from typing import Dict, Any, List, Optional, Generator, Tuple
from datetime import datetime

from .state_manager import (
    ConversationState, 
    SessionManager, 
    EmergencyType, 
    ConversationPhase,
    session_manager
)
from .prompts import build_system_prompt, QUICK_RESPONSES
from .connect_llm import (
    get_response_with_tools,
    get_streaming_response_with_history,
    parse_tool_calls,
    has_tool_calls,
    get_response_content,
    format_tool_result_message,
    format_assistant_message_with_tool_calls
)
from dispatcher.tool_executor import execute_tool, TOOL_REGISTRY
from dispatcher.state_tools import STATE_TOOLS
from dispatcher import AMBULANCE_TOOLS, FIRE_TOOLS, POLICE_TOOLS


def get_all_tools() -> List[Dict[str, Any]]:
    """Get all available tools for the LLM"""
    return STATE_TOOLS + AMBULANCE_TOOLS + FIRE_TOOLS + POLICE_TOOLS


class EmergencyOrchestrator:
    """
    Orchestrates the emergency response conversation flow
    All decision making is delegated to the LLM through tool calls
    """
    
    MAX_TOOL_ITERATIONS = 5  # Prevent infinite tool calling loops
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize orchestrator with a session
        
        Args:
            session_id: Optional session ID (creates new if not provided)
        """
        if session_id:
            self.state = session_manager.get_or_create_session(session_id)
        else:
            self.state = session_manager.create_session()
        
        self.session_id = self.state.session_id
    
    def process_user_message(self, user_message: str) -> Generator:
        """
        Process a user message and generate response with potential tool calls
        LLM handles all decision making through tools
        
        Args:
            user_message: The user's message
        
        Yields:
            Response chunks for streaming
        
        Returns:
            Final result dict with metadata
        """
        # Add user message to state
        self.state.add_message("user", user_message)
        
        # Build system prompt based on current state
        system_prompt = build_system_prompt(self.state)
        
        # Give LLM all tools - it decides what to use
        tools = get_all_tools()
        
        # Get messages for LLM
        messages = self.state.get_messages_for_llm()
        
        # Process with tool calling loop
        full_response = ""
        tool_results = []
        iterations = 0
        
        while iterations < self.MAX_TOOL_ITERATIONS:
            iterations += 1
            
            # Get LLM response
            response = get_response_with_tools(messages, tools, system_prompt)
            
            # Check for tool calls
            if has_tool_calls(response):
                # Execute tools
                tool_calls = response.choices[0].message.tool_calls
                assistant_content = get_response_content(response)
                
                # Add assistant message with tool calls to history
                assistant_msg = format_assistant_message_with_tool_calls(
                    assistant_content, 
                    tool_calls
                )
                messages.append(assistant_msg)
                
                # Execute each tool and add results
                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        arguments = {}
                    
                    # Execute the tool
                    result = execute_tool(tool_name, arguments)
                    tool_results.append({
                        "tool": tool_name,
                        "arguments": arguments,
                        "result": result
                    })
                    
                    # Process tool result for state updates
                    self._process_tool_result(tool_name, arguments, result)
                    
                    # Add tool result to messages
                    tool_msg = format_tool_result_message(tool_call.id, tool_name, result)
                    messages.append(tool_msg)
                    
                    # Also add to state
                    self.state.add_tool_result(tool_call.id, tool_name, result)
                
                # Continue loop to get final response after tool execution
                continue
            
            else:
                # No tool calls, get the final response
                full_response = get_response_content(response)
                break
        
        # Add assistant response to state
        self.state.add_message("assistant", full_response)
        
        # Yield response text first
        yield full_response
        
        # Then yield metadata as dict
        yield {
            "session_id": self.session_id,
            "phase": self.state.phase.value,
            "emergency_type": self.state.emergency_type.value,
            "tools_called": len(tool_results),
            "tool_results": tool_results,
            "dispatched": self.state.emergency_services_dispatched,
            "state_summary": self.state.get_context_summary()
        }
    
    def _process_tool_result(self, tool_name: str, arguments: Dict, result: Dict):
        """
        Process tool results to update state
        This is where we sync tool results back to our state tracking
        """
        if not result.get("success", False):
            return
        
        # Handle emergency classification
        if tool_name == "classify_emergency":
            emergency_type_str = result.get("emergency_type", "").lower()
            type_map = {
                "medical": EmergencyType.MEDICAL,
                "fire": EmergencyType.FIRE,
                "police": EmergencyType.POLICE
            }
            if emergency_type_str in type_map:
                self.state.set_emergency_type(type_map[emergency_type_str])
        
        # Handle location setting
        elif tool_name == "set_user_location":
            location = result.get("location", {})
            if location.get("latitude") and location.get("longitude"):
                self.state.set_location(
                    location["latitude"],
                    location["longitude"],
                    "llm_tool",
                    location.get("address")
                )
        
        # Handle area name lookup
        elif tool_name == "lookup_location_by_area":
            location = result.get("location", {})
            if location.get("latitude") and location.get("longitude"):
                self.state.set_location(
                    location["latitude"],
                    location["longitude"],
                    "area_lookup",
                    location.get("address")
                )
        
        # Handle medical info updates
        elif tool_name == "update_medical_info":
            update = result.get("medical_info_update", {})
            if "patient_count" in update:
                self.state.medical_info.patient_count = update["patient_count"]
            if "symptoms" in update:
                self.state.medical_info.symptoms = update["symptoms"]
            if "patient_conscious" in update:
                self.state.medical_info.patient_conscious = update["patient_conscious"]
            if "patient_breathing" in update:
                self.state.medical_info.patient_breathing = update["patient_breathing"]
            if "notes" in update:
                self.state.medical_info.additional_notes = update["notes"]
        
        # Handle fire info updates
        elif tool_name == "update_fire_info":
            update = result.get("fire_info_update", {})
            if "smoke_visible" in update:
                self.state.fire_info.smoke_visible = update["smoke_visible"]
            if "flames_visible" in update:
                self.state.fire_info.flames_visible = update["flames_visible"]
            if "building_type" in update:
                self.state.fire_info.building_type = update["building_type"]
            if "people_trapped" in update:
                self.state.fire_info.people_trapped = update["people_trapped"]
            if "floor_count" in update:
                self.state.fire_info.floor_count = update["floor_count"]
            if "notes" in update:
                self.state.fire_info.additional_notes = update["notes"]
        
        # Handle police info updates
        elif tool_name == "update_police_info":
            update = result.get("police_info_update", {})
            if "emergency_subtype" in update:
                self.state.police_info.emergency_subtype = update["emergency_subtype"]
            if "weapons_involved" in update:
                self.state.police_info.weapons_involved = update["weapons_involved"]
            if "hostage_situation" in update:
                self.state.police_info.hostage_situation = update["hostage_situation"]
            if "suspect_count" in update:
                self.state.police_info.suspect_count = update["suspect_count"]
            if "victim_count" in update:
                self.state.police_info.victim_count = update["victim_count"]
            if "suspect_present" in update:
                self.state.police_info.suspect_present = update["suspect_present"]
            if "victim_safe" in update:
                self.state.police_info.victim_safe = update["victim_safe"]
            if "notes" in update:
                self.state.police_info.additional_notes = update["notes"]
        
        # Handle assessment results
        elif "assess" in tool_name:
            assessment = result.get("assessment", {})
            
            if tool_name == "assess_ambulance_need":
                self.state.medical_info.severity_level = assessment.get("urgency_level")
                self.state.medical_info.ambulance_type_needed = assessment.get("recommended_ambulance_type")
                self._advance_phase_if_needed(ConversationPhase.ASSESSING)
            
            elif tool_name == "assess_fire_severity":
                self.state.fire_info.severity_level = assessment.get("severity_level")
                self.state.fire_info.units_recommended = assessment.get("units_recommended", 1)
                self._advance_phase_if_needed(ConversationPhase.ASSESSING)
            
            elif tool_name == "assess_threat_level":
                self.state.police_info.threat_level = assessment.get("threat_level")
                self._advance_phase_if_needed(ConversationPhase.ASSESSING)
        
        # Handle dispatch results
        elif "dispatch" in tool_name:
            if tool_name in ["dispatch_nearest_ambulance", "dispatch_ambulance"]:
                self.state.add_dispatch(result, "ambulance")
            elif tool_name in ["dispatch_nearest_fire_truck", "dispatch_fire_truck", "dispatch_multiple_fire_units"]:
                self.state.add_dispatch(result, "fire")
            elif tool_name in ["dispatch_nearest_patrol_unit", "dispatch_patrol_unit", "dispatch_multiple_police_units"]:
                self.state.add_dispatch(result, "police")
                if result.get("case_number"):
                    self.state.police_info.case_number = result.get("case_number")
            
            self._advance_phase_if_needed(ConversationPhase.PROVIDING_GUIDANCE)
        
        # Handle case creation
        elif tool_name == "create_case":
            self.state.police_info.case_number = result.get("case_number")
    
    def _advance_phase_if_needed(self, target_phase: ConversationPhase):
        """Advance to target phase if current phase is earlier"""
        phase_order = [
            ConversationPhase.INITIAL,
            ConversationPhase.GATHERING_INFO,
            ConversationPhase.ASSESSING,
            ConversationPhase.DISPATCHING,
            ConversationPhase.PROVIDING_GUIDANCE,
            ConversationPhase.MONITORING,
            ConversationPhase.RESOLVED
        ]
        
        current_idx = phase_order.index(self.state.phase)
        target_idx = phase_order.index(target_phase)
        
        if target_idx > current_idx:
            self.state.advance_phase(target_phase)
    
    def set_user_location(self, latitude: float, longitude: float, source: str = "device"):
        """
        Set user location directly (e.g., from device GPS)
        
        Args:
            latitude: User's latitude
            longitude: User's longitude
            source: Source of location ('device', 'user_input', 'estimated')
        """
        self.state.set_location(latitude, longitude, source)
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get current state as dictionary"""
        return self.state.to_dict()
    
    def get_context(self) -> str:
        """Get context summary string"""
        return self.state.get_context_summary()
    
    def is_dispatched(self) -> bool:
        """Check if emergency services have been dispatched"""
        return self.state.emergency_services_dispatched
    
    def get_dispatch_info(self) -> Optional[Dict[str, Any]]:
        """Get info about active dispatch"""
        if self.state.active_dispatch:
            return self.state.active_dispatch.to_dict()
        return None


def create_orchestrator(session_id: Optional[str] = None) -> EmergencyOrchestrator:
    """Factory function to create an orchestrator"""
    return EmergencyOrchestrator(session_id)


def process_message(session_id: str, message: str, location: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
    """
    Convenience function to process a message and get complete response
    """
    orchestrator = create_orchestrator(session_id)
    
    if location:
        orchestrator.set_user_location(location[0], location[1], "device")
    
    response_text = ""
    metadata = {}
    
    for chunk in orchestrator.process_user_message(message):
        if isinstance(chunk, str):
            response_text += chunk
        elif isinstance(chunk, dict):
            metadata = chunk
    
    return {
        "response": response_text,
        "session_id": orchestrator.session_id,
        "metadata": metadata
    }


if __name__ == "__main__":
    print("\n" + "="*60)
    print("EMERGENCY ORCHESTRATOR TEST")
    print("="*60 + "\n")
    
    orchestrator = create_orchestrator("test_session")
    print(f"Session created: {orchestrator.session_id}")
    print(f"All tools available to LLM: {len(get_all_tools())}")
