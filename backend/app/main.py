from enum import Enum
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.agent.PlanExecute import plan_execute_agent
from app.agent.ReAct_agent import run_agent
from app.tools.registry import TOOL_REGISTRY

app = FastAPI(
    title="Aegis Agent API",
    description="Resilient Tool-Using Autonomous Agent with ReAct and Plan-and-Execute modes.",
    version="0.1.0",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AgentMode(str, Enum):
    REACT = "react"
    PLAN_EXECUTE = "plan_execute"


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Task or question for the agent")
    mode: AgentMode = Field(
        default=AgentMode.REACT,
        description="Agent execution mode: 'react' or 'plan_execute'",
    )
    max_iterations: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum iterations for ReAct mode",
    )
    allow_replan: bool = Field(
        default=True,
        description="Whether to permit dynamic replanning in Plan-Execute mode",
    )


class ChatResponse(BaseModel):
    success: bool
    mode: str
    query: str
    answer: str
    plan: Optional[List[str]] = None
    trace: List[Dict[str, Any]] = Field(default_factory=list)
    usage: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


@app.get("/")
@app.get("/health")
def health_check() -> Dict[str, Any]:
    """Health check endpoint returning system status and registered tools."""
    return {
        "status": "healthy",
        "service": "Aegis-Agent API",
        "version": "0.1.0",
        "available_modes": [m.value for m in AgentMode],
        "available_tools": list(TOOL_REGISTRY.keys()),
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Execute a task using the selected agent mode and return the final answer along with execution traces."""
    try:
        if request.mode == AgentMode.PLAN_EXECUTE:
            result = plan_execute_agent(
                task=request.message,
                allow_replan=request.allow_replan,
                return_trace=True,
            )
            return ChatResponse(
                success=True,
                mode=request.mode.value,
                query=request.message,
                answer=result.get("answer", ""),
                plan=result.get("plan", []),
                trace=result.get("trace", []),
                usage=result.get("usage", {}),
            )
        else:
            result = run_agent(
                user_prompt=request.message,
                max_iterations=request.max_iterations,
                return_trace=True,
            )
            return ChatResponse(
                success=True,
                mode=request.mode.value,
                query=request.message,
                answer=result.get("answer", ""),
                trace=result.get("trace", []),
                usage=result.get("usage", {}),
            )
    except Exception as e:
        return ChatResponse(
            success=False,
            mode=request.mode.value,
            query=request.message,
            answer="Agent execution encountered an error.",
            trace=[],
            usage={},
            error=str(e),
        )
