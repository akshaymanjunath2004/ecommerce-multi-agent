from typing import Literal, TypedDict, List
from langchain_core.messages import BaseMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from .agents import llm, sales_prompt, checkout_prompt
from .tools import ECommerceTools


# -----------------------------
# TOOLS
# -----------------------------
sales_tools = [
    ECommerceTools.search_products,
    ECommerceTools.add_to_cart,
]

checkout_tools = [
    ECommerceTools.view_cart,
    ECommerceTools.checkout,
]


# -----------------------------
# NODES
# -----------------------------
sales_node = create_react_agent(
    llm,
    tools=sales_tools,
    state_modifier=sales_prompt,
)

checkout_node = create_react_agent(
    llm,
    tools=checkout_tools,
    state_modifier=checkout_prompt,
)


class AgentState(TypedDict):
    messages: List[BaseMessage]


# -----------------------------
# SUPERVISOR
# -----------------------------
def supervisor_node(state: AgentState) -> Literal["Sales", "__end__"]:
    messages = state["messages"]
    if not messages:
        return "__end__"
    return "Sales"


# -----------------------------
# ROUTING AFTER SALES
# -----------------------------
def post_sales_router(state: AgentState) -> Literal["Checkout", "__end__"]:
    """
    Decide whether to proceed to Checkout
    ONLY if add_to_cart was successfully called.
    """

    for msg in state["messages"]:
        # ToolMessage means tool executed
        if isinstance(msg, ToolMessage):
            if msg.name == "add_to_cart":
                return "Checkout"

    return "__end__"


# -----------------------------
# AGENT FACTORY
# -----------------------------
class AgentFactory:
    @staticmethod
    def create_agent():
        workflow = StateGraph(AgentState)

        workflow.add_node("Sales", sales_node)
        workflow.add_node("Checkout", checkout_node)

        # Start → Sales
        workflow.add_conditional_edges(
            START,
            supervisor_node,
            {
                "Sales": "Sales",
                "__end__": END,
            },
        )

        # After Sales → Conditional
        workflow.add_conditional_edges(
            "Sales",
            post_sales_router,
            {
                "Checkout": "Checkout",
                "__end__": END,
            },
        )

        # Checkout → End
        workflow.add_edge("Checkout", END)

        checkpointer = MemorySaver()
        return workflow.compile(checkpointer=checkpointer)