"""
FastAPI Server for NeuroDesk AI Multi-Agent System.
Provides REST API and WebSocket for real-time streaming.
"""

import json
import asyncio
import os
from pathlib import Path
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.mab import MAB
from core.sab1 import SAB1
from core.sab2 import SAB2
from core.sab3 import SAB3
from core.tool_registry import ToolRegistry
from config import get_config, save_config, get_pre_instructions, save_pre_instructions
from core.llm_client import fetch_available_models
from memory import db

# Create FastAPI app
app = FastAPI(
    title="NeuroDesk API",
    description="AI Multi-Agent System for Digital Marketing Automation",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")


# Pydantic models
class AgentConfig(BaseModel):
    provider: str
    api_key: str
    model: str


class GoalRequest(BaseModel):
    goal: str
    platform: str = "All"
    session_id: Optional[str] = None

@app.post("/campaign/run")
async def run_campaign(request: GoalRequest):
    """Run a full campaign."""
    try:
        mab = get_mab()
        
        # Save user goal to session if session_id is provided
        if request.session_id:
            db.save_message(request.session_id, "MAB", "user", request.goal)
            
        result = await mab.run(request.goal, None)

        # Check if the inner run() itself failed
        if not result.get("success", False):
            error_msg = result.get("error", result.get("result", "Unknown error during campaign execution"))
            if request.session_id:
                db.save_message(request.session_id, "MAB", "assistant", f"Campaign failed: {error_msg}")
            return {"success": False, "error": str(error_msg)}

        # Extract the actual string report from the result dict
        final_output = result.get("final_output", "")
        if not final_output:
            final_output = str(result)
            
        # Save final report to session if session_id is provided
        if request.session_id:
            db.save_message(request.session_id, "MAB", "assistant", final_output)
            
        # Store in cross-session memory
        db.save_campaign_memory(request.goal, final_output)

        return {"success": True, "result": {"final_output": final_output}}
    except Exception as e:
        if request.session_id:
            db.save_message(request.session_id, "MAB", "assistant", f"Server Error: {str(e)}")
        return {"success": False, "error": str(e)}
class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = None
    session_id: Optional[str] = None


class ToolRequest(BaseModel):
    name: str
    path: str
    description: str = ""
    assigned_to: List[str] = []


# Global instances
mab: Optional[MAB] = None
sab1: Optional[SAB1] = None
sab2: Optional[SAB2] = None
sab3: Optional[SAB3] = None


def get_mab():
    """Get or create MAB instance (refreshed from disk config)."""
    global mab
    if mab is None:
        mab = MAB()
    return mab


def get_sab1():
    """Get or create SAB1 instance (refreshed from disk config)."""
    global sab1
    if sab1 is None:
        sab1 = SAB1()
    return sab1


def get_sab2():
    """Get or create SAB2 instance (refreshed from disk config)."""
    global sab2
    if sab2 is None:
        sab2 = SAB2()
    return sab2


def get_sab3():
    """Get or create SAB3 instance (refreshed from disk config)."""
    global sab3
    if sab3 is None:
        sab3 = SAB3()
    return sab3


@app.on_event("startup")
async def startup_event():
    """Initialize agents on startup."""
    global mab, sab1, sab2, sab3
    mab = MAB()
    sab1 = SAB1()
    sab2 = SAB2()
    sab3 = SAB3()


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {"status": "ok", "service": "NeuroDesk API"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/agents")
async def list_agents():
    """Get information about all agents."""
    return {
        "MAB": get_mab().get_agent_info() if mab else {},
        "SAB1": get_sab1().get_agent_info() if sab1 else {},
        "SAB2": get_sab2().get_agent_info() if sab2 else {},
        "SAB3": get_sab3().get_agent_info() if sab3 else {}
    }


@app.get("/models")
async def get_models(provider: str, api_key: str = "", base_url: str = ""):
    """Fetch available models for a given provider and API key."""
    try:
        models = await fetch_available_models(provider, api_key, base_url)
        return {"success": True, "models": models}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/config")
async def get_config_endpoint():
    """Get current configuration."""
    return get_config()


@app.post("/config")
async def update_config_endpoint(config: Dict[str, Any]):
    """Update configuration and reset cached agent instances so they pick up new settings."""
    global mab, sab1, sab2, sab3
    try:
        save_config(config)
        # Reset global instances so they reload with new config on next request
        mab = None
        sab1 = None
        sab2 = None
        sab3 = None
        return {"success": True, "message": "Configuration saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pre-instructions")
async def get_pre_instructions_endpoint():
    """Get pre-instructions for all agents."""
    return get_pre_instructions()


@app.post("/pre-instructions")
async def update_pre_instructions_endpoint(instructions: Dict[str, str]):
    """Update pre-instructions for all agents."""
    try:
        save_pre_instructions(instructions)
        return {"success": True, "message": "Pre-instructions saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tools")
async def list_tools():
    """Get list of all tools."""
    registry = ToolRegistry()
    return registry.get_all_tools_status()


@app.post("/tools/register")
async def register_tool(tool: ToolRequest):
    """Register a new tool."""
    registry = ToolRegistry()
    try:
        success = registry.register_local_tool(
            tool.name,
            tool.path,
            tool.description,
            tool.assigned_to
        )
        if success:
            return {"success": True, "message": f"Tool '{tool.name}' registered"}
        else:
            raise HTTPException(status_code=400, detail="Tool already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/tools/{tool_name}")
async def remove_tool(tool_name: str):
    """Remove a tool."""
    registry = ToolRegistry()
    try:
        if registry.remove_tool(tool_name):
            return {"success": True, "message": f"Tool '{tool_name}' removed"}
        else:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Session Endpoints ---

class SessionCreate(BaseModel):
    title: str

@app.get("/sessions")
async def list_sessions():
    """Get all sessions."""
    try:
        sessions = db.get_all_sessions()
        return {"success": True, "sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/sessions")
async def create_session(session: SessionCreate):
    """Create a new session."""
    try:
        session_id = db.create_session(session.title)
        return {"success": True, "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    try:
        deleted = db.delete_session(session_id)
        if deleted:
            return {"success": True}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str):
    """Get history for a specific session."""
    try:
        history = db.get_session_history(session_id)
        return {"success": True, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Chat Endpoints ---

@app.post("/mab/chat")
async def mab_chat(request: ChatRequest):
    """Handle chat message for MAB via HTTP (no WebSocket needed)."""
    try:
        agent = get_mab()
        
        # Load history from DB if session exists
        history = request.history
        if request.session_id:
            db_history = db.get_session_history(request.session_id).get("MAB", [])
            if db_history:
                history = db_history
            db.save_message(request.session_id, "MAB", "user", request.message)
        
        # No-op callback for HTTP endpoint (streaming goes via WebSocket separately)
        async def stream_callback(payload):
            pass
            
        result = await agent.chat(
            message=request.message,
            history=history,
            stream_callback=stream_callback
        )
        
        if request.session_id and result.get("success"):
            db.save_message(request.session_id, "MAB", "assistant", result.get("result", ""))
            
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/sab1/chat")
async def sab1_chat(request: ChatRequest):
    """Chat with SAB1."""
    try:
        sab1 = get_sab1()
        history = request.history
        if request.session_id:
            db_history = db.get_session_history(request.session_id).get("SAB1", [])
            if db_history:
                history = db_history
            db.save_message(request.session_id, "SAB1", "user", request.message)
            
        result = await sab1.chat(request.message, history)
        
        res_text = result.get("result", result.get("output", ""))
        if request.session_id and result.get("success"):
            db.save_message(request.session_id, "SAB1", "assistant", res_text)
            
        return {"success": True, "result": res_text}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/sab2/chat")
async def sab2_chat(request: ChatRequest):
    """Chat with SAB2."""
    try:
        sab2 = get_sab2()
        history = request.history
        if request.session_id:
            db_history = db.get_session_history(request.session_id).get("SAB2", [])
            if db_history:
                history = db_history
            db.save_message(request.session_id, "SAB2", "user", request.message)
            
        result = await sab2.chat(request.message, history)
        
        res_text = result.get("result", result.get("output", ""))
        if request.session_id and result.get("success"):
            db.save_message(request.session_id, "SAB2", "assistant", res_text)
            
        return {"success": True, "result": res_text}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/sab3/chat")
async def sab3_chat(request: ChatRequest):
    """Chat with SAB3."""
    try:
        sab3 = get_sab3()
        history = request.history
        if request.session_id:
            db_history = db.get_session_history(request.session_id).get("SAB3", [])
            if db_history:
                history = db_history
            db.save_message(request.session_id, "SAB3", "user", request.message)
            
        result = await sab3.chat(request.message, history)
        
        res_text = result.get("result", result.get("output", ""))
        if request.session_id and result.get("success"):
            db.save_message(request.session_id, "SAB3", "assistant", res_text)
            
        return {"success": True, "result": res_text}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/memory/{agent_id}")
async def get_memory(agent_id: str):
    """Get memory entries for an agent."""
    from core.memory_manager import get_memory_manager
    try:
        manager = get_memory_manager(agent_id)
        entries = manager.get_all()
        return {"success": True, "entries": entries, "count": len(entries)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/memory/{agent_id}/{entry_id}")
async def delete_memory_entry(agent_id: str, entry_id: str):
    """Delete a memory entry."""
    from core.memory_manager import get_memory_manager
    try:
        manager = get_memory_manager(agent_id)
        manager.delete(entry_id)
        return {"success": True, "message": "Entry deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/stats")
async def get_memory_stats():
    """Get memory statistics for all agents."""
    from core.memory_manager import get_memory_manager
    return {
        "MAB": get_memory_manager("MAB").get_stats(),
        "SAB1": get_memory_manager("SAB1").get_stats(),
        "SAB2": get_memory_manager("SAB2").get_stats(),
        "SAB3": get_memory_manager("SAB3").get_stats()
    }


# WebSocket for real-time streaming
@app.websocket("/ws/stream")
async def stream_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time streaming of campaign execution."""
    await websocket.accept()

    try:
        while True:
            # Wait for messages
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "start_campaign":
                # Start campaign execution
                goal = message.get("goal", "")
                platform = message.get("platform", "All")
                session_id = message.get("session_id")

                await websocket.send_json({
                    "type": "status",
                    "message": "Campaign started",
                    "goal": goal,
                    "platform": platform
                })

                # Execute real campaign with streaming
                await execute_real_campaign(websocket, goal, platform, session_id)

            elif message.get("type") == "chat":
                # Direct chat with an agent
                agent_id = message.get("agent", "mab").lower()
                user_msg = message.get("message", "")
                session_id = message.get("session_id")
                history = message.get("history", [])

                if session_id:
                    db.save_message(session_id, agent_id.upper(), "user", user_msg)

                # Get the agent instance
                agent = None
                if agent_id == "mab": agent = get_mab()
                elif agent_id == "sab1": agent = get_sab1()
                elif agent_id == "sab2": agent = get_sab2()
                elif agent_id == "sab3": agent = get_sab3()

                if agent:
                    async def stream_callback(payload):
                        # Add agent_id to payload for the frontend to know which chat to update
                        payload["chat_agent"] = agent_id
                        await websocket.send_json(payload)

                    result = await agent.chat(
                        message=user_msg,
                        history=history,
                        stream_callback=stream_callback
                    )

                    # Final save to DB
                    if session_id and result.get("success"):
                        db.save_message(session_id, agent_id.upper(), "assistant", result.get("result", ""))
                    
                    # Final confirmation message
                    await websocket.send_json({
                        "type": "chat_done",
                        "agent": agent_id,
                        "result": result.get("result", "")
                    })

            elif message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})


async def execute_real_campaign(websocket: WebSocket, goal: str, platform: str, session_id: str = None):
    """Execute a real campaign workflow and stream updates to the websocket."""
    try:
        mab = get_mab()
        
        if session_id:
            db.save_message(session_id, "MAB", "user", goal)
            
        async def stream_callback(payload):
            # Send the payload directly to the websocket
            await websocket.send_json(payload)
            
        # Run real execution
        result = await mab.run(goal, stream_callback)
        
        if result.get("success"):
            final_output = result.get("final_output", "")
            
            # Save to session if provided
            if session_id:
                db.save_message(session_id, "MAB", "assistant", final_output)
            
            # Store in cross-session memory
            db.save_campaign_memory(goal, final_output)
            
            # Final output message for the frontend
            await websocket.send_json({
                "type": "final_output",
                "result": final_output
            })
            
            await websocket.send_json({
                "type": "sab_done",
                "agent": "MAB",
                "message": "✅ Campaign completed successfully!"
            })
        else:
            error_msg = result.get("error", "Unknown error")
            await websocket.send_json({
                "type": "error",
                "message": f"Campaign Failed: {error_msg}"
            })
            
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": f"Execution Error: {str(e)}"
        })


# Frontend file serving
@app.get("/app")
async def serve_app():
    """Serve the frontend application."""
    index_path = Path("frontend/index.html")
    if index_path.exists():
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Frontend not found")


# --- Tool Execution Endpoints ---

class ExecuteToolRequest(BaseModel):
    tool_name: str
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}


@app.post("/tools/execute")
async def execute_tool(request: ExecuteToolRequest):
    """Execute a registered tool with given arguments."""
    try:
        registry = ToolRegistry()
        result = await registry.execute_tool(request.tool_name, *request.args, **request.kwargs)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Performance Endpoints ---
@app.get("/performance/summary")
async def get_performance_summary():
    """Get live performance summary from all tracked inference requests."""
    try:
        from core.performance_logger import PerformanceLogger
        logger = PerformanceLogger()
        return {"success": True, "summary": logger.get_summary()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Benchmark Endpoints ---

@app.get("/benchmark/providers")
async def get_benchmark_providers():
    """Get list of providers available for benchmarking."""
    from core.benchmark_runner import BenchmarkRunner
    runner = BenchmarkRunner()
    return {"providers": runner.get_providers_to_benchmark()}


@app.get("/benchmark/run")
async def run_benchmark(
    provider: str,
    model: str,
    api_key: str = "",
    base_url: str = ""
):
    """Run benchmark for a specific provider/model."""
    try:
        from core.benchmark_runner import BenchmarkRunner
        runner = BenchmarkRunner()
        results = await runner.benchmark_provider(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url
        )
        return {"success": True, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/benchmark/comparison")
async def get_benchmark_comparison():
    """Get comparison across all benchmarked providers."""
    try:
        from core.benchmark_runner import BenchmarkRunner
        runner = BenchmarkRunner()
        comparisons = runner.get_comparison()
        return {"success": True, "comparisons": comparisons}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/benchmark/export")
async def export_benchmark_results():
    """Export benchmark results to markdown."""
    try:
        from core.benchmark_runner import BenchmarkRunner
        runner = BenchmarkRunner()
        content = runner.export_summary()
        return {"success": True, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Frontend file serving
@app.get("/app")
async def serve_app():
    """Serve the frontend application."""
    index_path = Path("frontend/index.html")
    if index_path.exists():
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Frontend not found")


# Start server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
