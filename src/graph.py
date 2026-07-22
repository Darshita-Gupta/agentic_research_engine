import json
from langchain_core.messages import SystemMessage, ToolMessage, AIMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph

# Ensure config module is loaded first to populate default variables/environment
import src.config
from src.state import AgentState
from src.schemas import DecisionMakingOutput, JudgeOutput
from src.tools import tools, tools_dict
from src.utils import format_tools_description
from src import prompts

# ==========================================
# LLM SETUP
# ==========================================

# Initialize the Groq model for all nodes
base_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.0)

# Configure nodes with specific schemas and tool sets
decision_making_llm = base_llm.with_structured_output(DecisionMakingOutput)
agent_llm = base_llm.bind_tools(tools)
judge_llm = base_llm.with_structured_output(JudgeOutput)

# ==========================================
# NODE FUNCTIONS
# ==========================================

# Decision making node
def decision_making_node(state: AgentState):
    """Entry point of the workflow. Decides if a query needs research or direct conversational answer."""
    system_prompt = SystemMessage(content=prompts.decision_making_prompt)
    response: DecisionMakingOutput = decision_making_llm.invoke([system_prompt] + state["messages"])
    output = {"requires_research": response.requires_research}
    if response.answer:
        output["messages"] = [AIMessage(content=response.answer)]
    return output

# Planning node
def planning_node(state: AgentState):
    """Creates a step-by-step plan to resolve the user's scientific query."""
    system_prompt = SystemMessage(content=prompts.planning_prompt.format(tools=format_tools_description(tools)))
    response = base_llm.invoke([system_prompt] + state["messages"])
    return {"messages": [response]}

# Tool execution node
def tools_node(state: AgentState):
    """Executes selected tools based on the final message instructions."""
    outputs = []
    for tool_call in state["messages"][-1].tool_calls:
        tool_result = tools_dict[tool_call["name"]].invoke(tool_call["args"])
        outputs.append(
            ToolMessage(
                content=json.dumps(tool_result),
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
        )
    return {"messages": outputs}

# Agent response node
def agent_node(state: AgentState):
    """Produces the final or intermediate research response."""
    system_prompt = SystemMessage(content=prompts.agent_prompt)
    response = agent_llm.invoke([system_prompt] + state["messages"])
    return {"messages": [response]}

# Judge node
def judge_node(state: AgentState):
    """Evaluates the final summary for quality, accuracy, and citation compliance."""
    num_feedback_requests = state.get("num_feedback_requests", 0)
    if num_feedback_requests >= 2:
        return {"is_good_answer": True}

    system_prompt = SystemMessage(content=prompts.judge_prompt)
    response: JudgeOutput = judge_llm.invoke([system_prompt] + state["messages"])
    output = {
        "is_good_answer": response.is_good_answer,
        "num_feedback_requests": num_feedback_requests + 1
    }
    if response.feedback:
        output["messages"] = [AIMessage(content=response.feedback)]
    return output

# ==========================================
# GRAPH ROUTERS & CONDITIONAL EDGES
# ==========================================

def router(state: AgentState):
    if state.get("requires_research"):
        return "planning"
    else:
        return "end"

def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "continue"
    else:
        return "end"

def final_answer_router(state: AgentState):
    if state.get("is_good_answer"):
        return "end"
    else:
        return "planning"

# ==========================================
# WORKFLOW COMPILATION
# ==========================================

# Initialize the StateGraph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("decision_making", decision_making_node)
workflow.add_node("planning", planning_node)
workflow.add_node("tools", tools_node)
workflow.add_node("agent", agent_node)
workflow.add_node("judge", judge_node)

# Set entry point
workflow.set_entry_point("decision_making")

# Map conditional routing and transitions
workflow.add_conditional_edges(
    "decision_making",
    router,
    {
        "planning": "planning",
        "end": END,
    }
)
workflow.add_edge("planning", "agent")
workflow.add_edge("tools", "agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "tools",
        "end": "judge",
    },
)
workflow.add_conditional_edges(
    "judge",
    final_answer_router,
    {
        "planning": "planning",
        "end": END,
    }
)

app = workflow.compile()
