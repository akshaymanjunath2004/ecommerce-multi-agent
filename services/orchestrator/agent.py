from typing import Literal, TypedDict, List
from langchain_core.messages import BaseMessage, ToolMessage, HumanMessage
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
    ECommerceTools.remove_from_cart,
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
def supervisor_node(state: AgentState) -> Literal["Sales", "Checkout", "__end__"]:
    messages = state["messages"]
    if not messages:
        return "__end__"
    
    last_message = messages[-1]
    if not isinstance(last_message, HumanMessage):
        return "Sales"
    
    content = last_message.content.lower()
    
    # Direct routing for checkout/cart intents
    if any(keyword in content for keyword in ["checkout", "pay now", "view cart", "my cart"]):
        # If they say "Buy [Product] and checkout", we should still go to Sales first.
        # But if they JUST say "checkout", go to Checkout.
        if "buy" not in content and "add" not in content:
            return "Checkout"
            
    return "Sales"


# -----------------------------
# ROUTING AFTER SALES
# -----------------------------
def post_sales_router(state: AgentState) -> Literal["Checkout", "__end__"]:
    """
    Decide whether to proceed to Checkout.
    Proceed if 'add_to_cart' was called in the latest turn,
    UNLESS the user also signaled an intent to remove items.
    """
    messages = state["messages"]
    
    # 1. Safety Check: Find the last Human Message to check intent
    last_human_content = ""
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            last_human_content = m.content.lower()
            break
            
    # If the user explicitly mentioned removing/deleting, DO NOT auto-checkout.
    if any(w in last_human_content for w in ["remove", "delete", "cancel"]):
        return "__end__"

    # 2. Look for recent add_to_cart call to trigger auto-checkout
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            # Auto-checkout only on ADD
            if msg.name == "add_to_cart":
                return "Checkout"
        # Stop looking if we hit the user's input (don't look at previous turns)
        if isinstance(msg, HumanMessage):
            break

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

        # Start → Supervisor Choice
        workflow.add_conditional_edges(
            START,
            supervisor_node,
            {
                "Sales": "Sales",
                "Checkout": "Checkout",
                "__end__": END,
            },
        )

        # After Sales → Decide if Checkout is needed
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