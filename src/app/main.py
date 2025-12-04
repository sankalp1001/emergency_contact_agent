"""
Emergency Contact Agent - Main FastAPI Application
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import json

from llm.orchestrator import create_orchestrator, EmergencyOrchestrator
from llm.state_manager import session_manager
from dispatcher.setup_database import setup_all_databases

# Initialize FastAPI app
app = FastAPI(
    title="Emergency Contact Agent",
    description="AI-powered emergency response system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
app.mount("/frontend", StaticFiles(directory="../frontend"), name="frontend")

# Store active orchestrators
active_sessions: dict[str, EmergencyOrchestrator] = {}


# ============== Pydantic Models ==============

class QueryRequest(BaseModel):
    """Request model for user queries"""
    message: str
    session_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class LocationUpdate(BaseModel):
    """Request model for location updates"""
    session_id: str
    latitude: float
    longitude: float
    source: str = "device"


# ============== API Endpoints ==============

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "name": "Emergency Contact Agent",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "chat": "/chat",
            "stream": "/chat/stream",
            "session": "/session/{session_id}",
            "location": "/location"
        }
    }


@app.post("/chat")
async def chat(request: QueryRequest):
    """
    Process a chat message and return response with tool execution results
    
    This endpoint handles the full orchestration including:
    - Emergency type detection
    - Information gathering
    - Tool execution (assessment, dispatch)
    - Response generation
    """
    try:
        # Get or create orchestrator for session
        session_id = request.session_id or f"session_{len(active_sessions) + 1}"
        
        if session_id in active_sessions:
            orchestrator = active_sessions[session_id]
        else:
            orchestrator = create_orchestrator(session_id)
            active_sessions[session_id] = orchestrator
        
        # Set location if provided
        if request.latitude and request.longitude:
            orchestrator.set_user_location(request.latitude, request.longitude, "device")
        
        # Process message
        response_text = ""
        metadata = {}
        
        for chunk in orchestrator.process_user_message(request.message):
            if isinstance(chunk, str):
                response_text = chunk
            elif isinstance(chunk, dict):
                metadata = chunk
        
        return JSONResponse({
            "success": True,
            "response": response_text,
            "session_id": orchestrator.session_id,
            "phase": orchestrator.state.phase.value,
            "emergency_type": orchestrator.state.emergency_type.value,
            "dispatched": orchestrator.is_dispatched(),
            "dispatch_info": orchestrator.get_dispatch_info(),
            "context": orchestrator.get_context(),
            "metadata": metadata
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: QueryRequest):
    """
    Stream chat response
    Note: Tool calling responses are not streamed (returned as complete after tool execution)
    """
    try:
        session_id = request.session_id or f"session_{len(active_sessions) + 1}"
        
        if session_id in active_sessions:
            orchestrator = active_sessions[session_id]
        else:
            orchestrator = create_orchestrator(session_id)
            active_sessions[session_id] = orchestrator
        
        if request.latitude and request.longitude:
            orchestrator.set_user_location(request.latitude, request.longitude, "device")
        
        def generate():
            for chunk in orchestrator.process_user_message(request.message):
                if isinstance(chunk, str):
                    yield f"data: {json.dumps({'type': 'content', 'data': chunk})}\n\n"
                elif isinstance(chunk, dict):
                    yield f"data: {json.dumps({'type': 'metadata', 'data': chunk})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
        return StreamingResponse(generate(), media_type="text/event-stream")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}")
def get_session(session_id: str):
    """Get session state and history"""
    if session_id in active_sessions:
        orchestrator = active_sessions[session_id]
        return JSONResponse({
            "success": True,
            "session_id": session_id,
            "state": orchestrator.get_state_summary()
        })
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.post("/location")
async def update_location(request: LocationUpdate):
    """Update user location for a session"""
    if request.session_id in active_sessions:
        orchestrator = active_sessions[request.session_id]
        orchestrator.set_user_location(
            request.latitude, 
            request.longitude, 
            request.source
        )
        return JSONResponse({
            "success": True,
            "message": "Location updated",
            "location": {
                "latitude": request.latitude,
                "longitude": request.longitude
            }
        })
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.delete("/session/{session_id}")
def end_session(session_id: str):
    """End and clean up a session"""
    if session_id in active_sessions:
        del active_sessions[session_id]
        session_manager.end_session(session_id)
        return JSONResponse({
            "success": True,
            "message": f"Session {session_id} ended"
        })
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/sessions")
def list_sessions():
    """List all active sessions"""
    sessions = []
    for sid, orch in active_sessions.items():
        sessions.append({
            "session_id": sid,
            "phase": orch.state.phase.value,
            "emergency_type": orch.state.emergency_type.value,
            "dispatched": orch.is_dispatched()
        })
    return JSONResponse({
        "success": True,
        "count": len(sessions),
        "sessions": sessions
    })


@app.post("/setup-db")
def setup_databases():
    """Initialize/reset all databases"""
    try:
        setup_all_databases()
        return JSONResponse({
            "success": True,
            "message": "All databases setup complete"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== Legacy Endpoints (Backward Compatibility) ==============

# Store for legacy endpoint
conversation_state = {}

@app.get("/response_stream")
def stream_response():
    """Legacy streaming endpoint"""
    output_generator = conversation_state.get("output_generator")
    if output_generator:
        return StreamingResponse(output_generator, media_type='text/event-stream')
    raise HTTPException(status_code=400, detail="No active query")


@app.post("/receive_query")
def receive_query(query: str):
    """Legacy query endpoint"""
    from llm.connect_llm import get_simple_response
    conversation_state['input'] = query
    conversation_state['output_generator'] = get_simple_response(query)
    return 'received query'


# ============== Startup Event ==============

@app.on_event("startup")
async def startup_event():
    """Initialize databases on startup"""
    print("\nEmergency Contact Agent Starting...")
    print("Initializing databases...")
    try:
        setup_all_databases()
    except Exception as e:
        print(f"[WARNING] Database setup warning: {e}")
    print("Agent ready!\n")


# ============== Run ==============

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
