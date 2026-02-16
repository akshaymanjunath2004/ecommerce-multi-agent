from typing import Literal, TypedDict, List
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from .agents import llm, sales_prompt, checkout_prompt
from .tools import ECommerceTools

# --- Define Tools ---
sales_tools = [ECommerceTools.search_products]
checkout_tools = [ECommerceTools.view_cart, ECommerceTools.add_to_cart, ECommerceTools.checkout]

# --- Create Nodes (Using state_modifier for LangGraph 0.2.x) ---
sales_node = create_react_agent(llm, tools=sales_tools, state_modifier=sales_prompt)
checkout_node = create_react_agent(llm, tools=checkout_tools, state_modifier=checkout_prompt)

# --- Define State ---
class AgentState(TypedDict):
    messages: List[BaseMessage]

# --- Supervisor Logic ---
def supervisor_node(state: AgentState) -> Literal["Sales", "Checkout", "__end__"]:
    messages = state["messages"]
    if not messages:
        return "__end__"
        
    last_msg = messages[-1].content.lower()
    
    # --- SMART ROUTING ---
    # If the user wants to "Buy" but hasn't specified exactly what from the catalog,
    # or if they are asking to "Find" anything, send them to Sales first.
    if any(k in last_msg for k in ["find", "search", "show", "list", "looking for", "what is"]):
        return "Sales"
    
    # If the message contains "buy" or "add" but also a specific product name 
    # that hasn't been 'found' in the conversation yet, Sales should still handle it 
    # to fetch the correct Product ID for the Checkout tool.
    if any(k in last_msg for k in ["buy", "purchase", "order", "add to cart"]):
        # If we have no prior tool outputs in history, Sales must find the item ID first.
        return "Checkout" 

    return "Sales"

class AgentFactory:
    @staticmethod
    def create_agent():
        workflow = StateGraph(AgentState)
        workflow.add_node("Sales", sales_node)
        workflow.add_node("Checkout", checkout_node)
        
        workflow.add_conditional_edges(
            START,
            supervisor_node,
            {
                "Sales": "Sales",
                "Checkout": "Checkout",
                "__end__": END
            }
        )
        
        workflow.add_edge("Sales", END)
        workflow.add_edge("Checkout", END)
        
        checkpointer = MemorySaver()
        return workflow.compile(checkpointer=checkpointer)