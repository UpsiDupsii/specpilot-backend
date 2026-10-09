import os
from typing import Literal
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode

from .tools import search_documents, create_actionable_task, send_webhook_notification

AGENT_TOOLS = [search_documents, create_actionable_task, send_webhook_notification]

SYSTEM_PROMPT = """You are SpecPilot Agent, an autonomous enterprise compliance and audit coordinator.
You have access to tools to:
1. Search indexed documents and standards (`search_documents`).
2. Create tracked remediation tasks (`create_actionable_task`).
3. Send external webhook notifications via n8n (`send_webhook_notification`).

Reason step-by-step:
- First search for necessary facts if context is required.
- If you find compliance gaps or user-requested action items, create actionable tasks.
- If high-severity issues exist or notification is explicitly requested, dispatch a webhook.
- Summarize your final actions clearly to the user.
"""


def should_continue(state: MessagesState) -> Literal["tools", "__end__"]:
    """Determines whether to call a tool or finish the conversation."""
    messages = state["messages"]
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


def call_model(state: MessagesState):
    """Invokes the Ollama model with bound tools."""
    ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
    ollama_model = os.getenv('OLLAMA_MODEL', 'qwen2.5:3b')

    llm = ChatOllama(
        model=ollama_model,
        base_url=ollama_base_url,
        temperature=0.0
    ).bind_tools(AGENT_TOOLS)

    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}


def build_specpilot_agent():
    """Compiles the explicit LangGraph state machine without deprecated wrappers."""
    workflow = StateGraph(MessagesState)

    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(AGENT_TOOLS))

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, ["tools", END])
    workflow.add_edge("tools", "agent")

    return workflow.compile()


def execute_agent_workflow(prompt: str) -> dict:
    """Executes the LangGraph agent for a user prompt and returns the output summary."""
    agent = build_specpilot_agent()
    result = agent.invoke({"messages": [("user", prompt)]})
    final_message = result["messages"][-1]
    return {
        "output": final_message.content,
        "total_messages": len(result["messages"])
    }