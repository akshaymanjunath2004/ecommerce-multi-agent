from langchain_core.messages import SystemMessage, HumanMessage
from .agent import AgentFactory

class ChatService:
    def __init__(self):
        self.agent = AgentFactory.create_agent()

    async def process_message(self, session_id: str, message: str) -> str:
        # Config contains the session_id for memory (LangGraph Checkpointer)
        config = {"configurable": {"thread_id": session_id}}
        
        # FIX: We inject the session_id explicitly so the LLM knows it.
        # This prevents it from hallucinating "session_id" as the ID.
        system_instruction = f"You are a shopping assistant. Your current session_id is '{session_id}'. You MUST use this ID for all tool calls."
        
        inputs = {
            "messages": [
                SystemMessage(content=system_instruction),
                HumanMessage(content=message)
            ]
        }
        
        result = await self.agent.ainvoke(inputs, config=config)
        
        # Return the last message from the AI
        return result["messages"][-1].content