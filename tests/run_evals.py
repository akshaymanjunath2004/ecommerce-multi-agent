import httpx
import json
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from termcolor import colored

# Configuration
AGENT_URL = "http://localhost:8000/chat"
PRODUCT_URL = "http://localhost:8001"
SESSION_URL = "http://localhost:8004"

judge_llm = ChatOpenAI(model="gpt-4o", temperature=0)

JUDGE_PROMPT = ChatPromptTemplate.from_template("""
You are a QA Auditor for an AI Agent.
Your job is to Grade the agent's performance based on the User's Request and the Expected Behavior.

---
User Request: {input}
Expected Behavior: {expected}
---
Actual Agent Response: {actual_response}
---

Did the agent meet the requirements? 
- If it performed the action correctly (or handled the error correctly), say "PASS".
- If it hallucinated, failed to buy when it should have, or bought the wrong thing, say "FAIL".
- Provide a brief 1-sentence reason.

Format: STATUS | Reason
Example: PASS | The agent successfully returned an order ID.
""")

async def setup_environment():
    print(colored("⚙️  Resetting Environment...", "cyan"))
    async with httpx.AsyncClient() as client:
        try:
            await client.post(f"{PRODUCT_URL}/reset_db")
        except:
            pass 
            
        # 1. Base Inventory
        await client.post(f"{PRODUCT_URL}/", json={"name": "MacBook Pro", "price": 2000.0, "stock": 10})
        await client.post(f"{PRODUCT_URL}/", json={"name": "Yonex Arcsaber 11 Pro", "price": 200.0, "stock": 10})
        
        # 2. Tie-Breaker Items ($5.00)
        await client.post(f"{PRODUCT_URL}/", json={"name": "Tennis Ball", "price": 5.0, "stock": 50})
        await client.post(f"{PRODUCT_URL}/", json={"name": "Ping Pong Ball", "price": 5.0, "stock": 50})
        
        # 3. NEW: Absolute Cheapest Item ($2.00)
        await client.post(f"{PRODUCT_URL}/", json={"name": "Rubber Keychain", "price": 2.0, "stock": 100})
        
        # Mid-range
        await client.post(f"{PRODUCT_URL}/", json={"name": "Water Bottle", "price": 10.0, "stock": 20})
        
        print("   ✅ Environment Restocked with 6 products.")

async def run_test_case(test_case):
    name = test_case["name"]
    user_input = test_case["inputs"]
    expected = test_case["expected_behavior"]

    print(f"\n🧪 Testing: {colored(name, 'yellow')}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        session_resp = await client.post(f"{SESSION_URL}/", json={"user_id": 1})
        session_id = session_resp.json()["session_id"]

        try:
            print(f"   User: {user_input}")
            response = await client.post(
                AGENT_URL, 
                json={"session_id": session_id, "message": user_input}
            )
            response.raise_for_status()
            agent_reply = response.json()["response"]
            print(f"   Agent: {colored(agent_reply, 'blue')}")
        except Exception as e:
            agent_reply = f"SYSTEM ERROR: {str(e)}"
            print(colored(f"   API Fail: {e}", "red"))

        print("   👨‍⚖️  Judging...", end="", flush=True)
        judge_resp = await judge_llm.ainvoke(JUDGE_PROMPT.format(
            input=user_input,
            expected=expected,
            actual_response=agent_reply
        ))
        
        verdict = judge_resp.content
        status, reason = verdict.split("|", 1) if "|" in verdict else (verdict, "No reason provided")
        
        if "PASS" in status.upper():
            print(f"\r   ✅ {colored('PASS', 'green')} | {reason.strip()}")
        else:
            print(f"\r   ❌ {colored('FAIL', 'red')} | {reason.strip()}")

async def main():
    with open("tests/dataset.json", "r") as f:
        dataset = json.load(f)

    await setup_environment()
    
    for test in dataset:
        await run_test_case(test)

if __name__ == "__main__":
    asyncio.run(main())