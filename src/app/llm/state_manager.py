"""
State Manager Module
Manages conversation state, emergency context, and session data for LLM orchestration
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json


class EmergencyType(Enum):
    """Types of emergencies the system can handle"""
    UNKNOWN = "unknown"
    MEDICAL = "medical"
    FIRE = "fire"
    POLICE = "police"  # Includes kidnap, extortion


class ConversationPhase(Enum):
    """Phases of emergency conversation"""
    INITIAL = "initial"                    # Just started, identifying emergency type
    GATHERING_INFO = "gathering_info"      # Collecting essential information
    ASSESSING = "assessing"                # Assessing severity/threat level
    DISPATCHING = "dispatching"            # Dispatching emergency services
    PROVIDING_GUIDANCE = "providing_guidance"  # Giving safety instructions
    MONITORING = "monitoring"              # Monitoring ongoing situation
    RESOLVED = "resolved"                  # Emergency handled


@dataclass
class LocationInfo:
    """User location information"""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    obtained_from: Optional[str] = None  # 'device', 'user_input', 'estimated'
    confidence: str = "unknown"  # 'high', 'medium', 'low', 'unknown'
    
    def is_valid(self) -> bool:
        return self.latitude is not None and self.longitude is not None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "address": self.address,
            "obtained_from": self.obtained_from,
            "confidence": self.confidence
        }


@dataclass
class MedicalInfo:
    """Medical emergency specific information"""
    patient_count: int = 0
    symptoms: List[str] = field(default_factory=list)
    patient_conscious: Optional[bool] = None
    patient_breathing: Optional[bool] = None
    severity_level: Optional[str] = None  # 'critical', 'high', 'moderate', 'low'
    ambulance_type_needed: Optional[str] = None
    additional_notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "patient_count": self.patient_count,
            "symptoms": self.symptoms,
            "patient_conscious": self.patient_conscious,
            "patient_breathing": self.patient_breathing,
            "severity_level": self.severity_level,
            "ambulance_type_needed": self.ambulance_type_needed,
            "additional_notes": self.additional_notes
        }


@dataclass  
class FireInfo:
    """Fire emergency specific information"""
    smoke_visible: Optional[bool] = None
    flames_visible: Optional[bool] = None
    building_type: Optional[str] = None  # 'residential', 'commercial', 'industrial', 'vehicle', 'forest'
    people_trapped: int = 0
    floor_count: int = 1
    spread_rate: str = "unknown"  # 'slow', 'moderate', 'fast', 'unknown'
    severity_level: Optional[str] = None
    units_recommended: int = 1
    additional_notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "smoke_visible": self.smoke_visible,
            "flames_visible": self.flames_visible,
            "building_type": self.building_type,
            "people_trapped": self.people_trapped,
            "floor_count": self.floor_count,
            "spread_rate": self.spread_rate,
            "severity_level": self.severity_level,
            "units_recommended": self.units_recommended,
            "additional_notes": self.additional_notes
        }


@dataclass
class PoliceInfo:
    """Police emergency specific information (kidnap, extortion, etc.)"""
    emergency_subtype: Optional[str] = None  # 'kidnap', 'extortion', 'robbery', 'assault', 'threat'
    weapons_involved: Optional[bool] = None
    hostage_situation: Optional[bool] = None
    suspect_count: int = 0
    victim_count: int = 1
    suspect_present: Optional[bool] = None
    violence_occurred: Optional[bool] = None
    victim_safe: Optional[bool] = None
    threat_level: Optional[str] = None  # 'critical', 'high', 'medium', 'low'
    case_number: Optional[str] = None
    additional_notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "emergency_subtype": self.emergency_subtype,
            "weapons_involved": self.weapons_involved,
            "hostage_situation": self.hostage_situation,
            "suspect_count": self.suspect_count,
            "victim_count": self.victim_count,
            "suspect_present": self.suspect_present,
            "violence_occurred": self.violence_occurred,
            "victim_safe": self.victim_safe,
            "threat_level": self.threat_level,
            "case_number": self.case_number,
            "additional_notes": self.additional_notes
        }


@dataclass
class DispatchInfo:
    """Information about dispatched services"""
    dispatch_id: Optional[int] = None
    service_type: Optional[str] = None  # 'ambulance', 'fire', 'police'
    unit_id: Optional[int] = None
    unit_identifier: Optional[str] = None  # vehicle number or unit code
    eta_minutes: Optional[int] = None
    status: str = "pending"  # 'pending', 'dispatched', 'en_route', 'arrived', 'completed'
    dispatched_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dispatch_id": self.dispatch_id,
            "service_type": self.service_type,
            "unit_id": self.unit_id,
            "unit_identifier": self.unit_identifier,
            "eta_minutes": self.eta_minutes,
            "status": self.status,
            "dispatched_at": self.dispatched_at.isoformat() if self.dispatched_at else None
        }


class ConversationState:
    """
    Manages the complete state of an emergency conversation session
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        # Conversation tracking
        self.messages: List[Dict[str, Any]] = []
        self.phase = ConversationPhase.INITIAL
        
        # Emergency context
        self.emergency_type = EmergencyType.UNKNOWN
        self.location = LocationInfo()
        
        # Type-specific info
        self.medical_info = MedicalInfo()
        self.fire_info = FireInfo()
        self.police_info = PoliceInfo()
        
        # Dispatch tracking
        self.dispatches: List[DispatchInfo] = []
        self.active_dispatch: Optional[DispatchInfo] = None
        
        # Tool call history
        self.tool_calls: List[Dict[str, Any]] = []
        
        # Flags
        self.location_requested = False
        self.emergency_services_dispatched = False
        self.safety_instructions_given = False
        
    def add_message(self, role: str, content: str, tool_calls: Optional[List] = None):
        """Add a message to conversation history"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        if tool_calls:
            message["tool_calls"] = tool_calls
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def add_tool_result(self, tool_call_id: str, tool_name: str, result: Dict[str, Any]):
        """Add a tool result to the conversation"""
        self.messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": json.dumps(result),
            "timestamp": datetime.now().isoformat()
        })
        self.tool_calls.append({
            "id": tool_call_id,
            "name": tool_name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()
    
    def get_messages_for_llm(self) -> List[Dict[str, str]]:
        """Get messages formatted for LLM API"""
        llm_messages = []
        for msg in self.messages:
            if msg["role"] == "tool":
                llm_messages.append({
                    "role": "tool",
                    "tool_call_id": msg.get("tool_call_id"),
                    "name": msg.get("name"),
                    "content": msg["content"]
                })
            else:
                llm_msg = {"role": msg["role"], "content": msg["content"]}
                if "tool_calls" in msg:
                    llm_msg["tool_calls"] = msg["tool_calls"]
                llm_messages.append(llm_msg)
        return llm_messages
    
    def set_emergency_type(self, emergency_type: EmergencyType):
        """Set the identified emergency type"""
        self.emergency_type = emergency_type
        if self.phase == ConversationPhase.INITIAL:
            self.phase = ConversationPhase.GATHERING_INFO
        self.updated_at = datetime.now()
    
    def set_location(self, lat: float, lon: float, source: str = "user_input", address: str = None):
        """Set user location"""
        self.location = LocationInfo(
            latitude=lat,
            longitude=lon,
            address=address,
            obtained_from=source,
            confidence="high" if source == "device" else "medium"
        )
        self.updated_at = datetime.now()
    
    def add_dispatch(self, dispatch_result: Dict[str, Any], service_type: str):
        """Record a dispatch"""
        dispatch = DispatchInfo(
            dispatch_id=dispatch_result.get("dispatch_id"),
            service_type=service_type,
            unit_identifier=dispatch_result.get("ambulance", {}).get("vehicle_number") or 
                           dispatch_result.get("fire_truck", {}).get("vehicle_number") or
                           dispatch_result.get("patrol_unit", {}).get("unit_code"),
            eta_minutes=dispatch_result.get("estimated_arrival_minutes"),
            status="dispatched",
            dispatched_at=datetime.now()
        )
        self.dispatches.append(dispatch)
        self.active_dispatch = dispatch
        self.emergency_services_dispatched = True
        
        if self.phase in [ConversationPhase.GATHERING_INFO, ConversationPhase.ASSESSING]:
            self.phase = ConversationPhase.DISPATCHING
        
        self.updated_at = datetime.now()
    
    def advance_phase(self, new_phase: ConversationPhase):
        """Advance to a new conversation phase"""
        self.phase = new_phase
        self.updated_at = datetime.now()
    
    def get_context_summary(self) -> str:
        """Get a summary of current state for system prompt injection"""
        summary_parts = [
            f"Session: {self.session_id}",
            f"Phase: {self.phase.value}",
            f"Emergency Type: {self.emergency_type.value}"
        ]
        
        if self.location.is_valid():
            summary_parts.append(f"Location: ({self.location.latitude}, {self.location.longitude})")
        else:
            summary_parts.append("Location: NOT OBTAINED")
        
        if self.emergency_type == EmergencyType.MEDICAL:
            info = self.medical_info
            if info.patient_count > 0:
                summary_parts.append(f"Patients: {info.patient_count}")
            if info.symptoms:
                summary_parts.append(f"Symptoms: {', '.join(info.symptoms)}")
            if info.severity_level:
                summary_parts.append(f"Severity: {info.severity_level}")
                
        elif self.emergency_type == EmergencyType.FIRE:
            info = self.fire_info
            if info.building_type:
                summary_parts.append(f"Building: {info.building_type}")
            if info.people_trapped > 0:
                summary_parts.append(f"People trapped: {info.people_trapped}")
            if info.severity_level:
                summary_parts.append(f"Severity: {info.severity_level}")
                
        elif self.emergency_type == EmergencyType.POLICE:
            info = self.police_info
            if info.emergency_subtype:
                summary_parts.append(f"Type: {info.emergency_subtype}")
            if info.threat_level:
                summary_parts.append(f"Threat: {info.threat_level}")
            if info.case_number:
                summary_parts.append(f"Case: {info.case_number}")
        
        if self.emergency_services_dispatched:
            summary_parts.append(f"Services dispatched: {len(self.dispatches)}")
            if self.active_dispatch and self.active_dispatch.eta_minutes:
                summary_parts.append(f"ETA: {self.active_dispatch.eta_minutes} minutes")
        
        return " | ".join(summary_parts)
    
    def get_missing_critical_info(self) -> List[str]:
        """Get list of critical information still needed"""
        missing = []
        
        if not self.location.is_valid():
            missing.append("location")
        
        if self.emergency_type == EmergencyType.UNKNOWN:
            missing.append("emergency_type")
        
        if self.emergency_type == EmergencyType.MEDICAL:
            if self.medical_info.patient_count == 0:
                missing.append("patient_count")
            if self.medical_info.patient_conscious is None:
                missing.append("patient_conscious_status")
            if self.medical_info.patient_breathing is None:
                missing.append("patient_breathing_status")
                
        elif self.emergency_type == EmergencyType.FIRE:
            if self.fire_info.building_type is None:
                missing.append("building_type")
            if self.fire_info.smoke_visible is None and self.fire_info.flames_visible is None:
                missing.append("fire_visibility")
                
        elif self.emergency_type == EmergencyType.POLICE:
            if self.police_info.emergency_subtype is None:
                missing.append("emergency_subtype")
            if self.police_info.victim_safe is None:
                missing.append("victim_safety_status")
        
        return missing
    
    def should_dispatch(self) -> bool:
        """Determine if we have enough info to dispatch"""
        # Must have location
        if not self.location.is_valid():
            return False
        
        # Must know emergency type
        if self.emergency_type == EmergencyType.UNKNOWN:
            return False
        
        # Already dispatched
        if self.emergency_services_dispatched:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize state to dictionary"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "phase": self.phase.value,
            "emergency_type": self.emergency_type.value,
            "location": self.location.to_dict(),
            "medical_info": self.medical_info.to_dict(),
            "fire_info": self.fire_info.to_dict(),
            "police_info": self.police_info.to_dict(),
            "dispatches": [d.to_dict() for d in self.dispatches],
            "flags": {
                "location_requested": self.location_requested,
                "emergency_services_dispatched": self.emergency_services_dispatched,
                "safety_instructions_given": self.safety_instructions_given
            },
            "message_count": len(self.messages),
            "tool_call_count": len(self.tool_calls)
        }


class SessionManager:
    """
    Manages multiple conversation sessions
    """
    
    def __init__(self):
        self.sessions: Dict[str, ConversationState] = {}
        self._session_counter = 0
    
    def create_session(self, session_id: Optional[str] = None) -> ConversationState:
        """Create a new conversation session"""
        if session_id is None:
            self._session_counter += 1
            session_id = f"session_{self._session_counter}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        session = ConversationState(session_id)
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[ConversationState]:
        """Get an existing session"""
        return self.sessions.get(session_id)
    
    def get_or_create_session(self, session_id: str) -> ConversationState:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            return self.create_session(session_id)
        return self.sessions[session_id]
    
    def end_session(self, session_id: str):
        """End and archive a session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.advance_phase(ConversationPhase.RESOLVED)
            # Could persist to database here
            del self.sessions[session_id]
    
    def list_active_sessions(self) -> List[str]:
        """List all active session IDs"""
        return list(self.sessions.keys())


# Global session manager instance
session_manager = SessionManager()


if __name__ == "__main__":
    # Test the state manager
    print("\n=== Testing State Manager ===\n")
    
    # Create a session
    session = session_manager.create_session("test_session")
    print(f"Created session: {session.session_id}")
    
    # Simulate conversation flow
    session.add_message("user", "Help! There's been an accident!")
    session.set_emergency_type(EmergencyType.MEDICAL)
    print(f"Phase: {session.phase.value}")
    
    session.set_location(12.9716, 77.5946, "user_input")
    session.medical_info.patient_count = 2
    session.medical_info.symptoms = ["bleeding", "unconscious"]
    session.medical_info.patient_conscious = False
    session.medical_info.patient_breathing = True
    
    print(f"\nContext Summary:\n{session.get_context_summary()}")
    print(f"\nMissing Info: {session.get_missing_critical_info()}")
    print(f"Should Dispatch: {session.should_dispatch()}")
    
    # Simulate dispatch
    dispatch_result = {
        "dispatch_id": 1,
        "ambulance": {"vehicle_number": "KA-01-AM-1001"},
        "estimated_arrival_minutes": 8
    }
    session.add_dispatch(dispatch_result, "ambulance")
    
    print(f"\nAfter dispatch:")
    print(f"Phase: {session.phase.value}")
    print(f"Active dispatch ETA: {session.active_dispatch.eta_minutes} minutes")
    
    print(f"\nFull State:\n{json.dumps(session.to_dict(), indent=2)}")

