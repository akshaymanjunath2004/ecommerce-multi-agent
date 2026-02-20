import os
import httpx
import asyncio
from .checkout_saga import build_checkout_saga
from langchain_core.tools import tool

# Env Vars
PRODUCT_URL = os.getenv("PRODUCT_URL", "http://localhost:8001")
ORDER_URL = os.getenv("ORDER_URL", "http://localhost:8002")
PAYMENT_URL = os.getenv("PAYMENT_URL", "http://localhost:8003")
SESSION_URL = os.getenv("SESSION_URL", "http://localhost:8004")

# Security Headers for internal service-to-service communication
API_HEADERS = {"X-Internal-API-Key": os.getenv("INTERNAL_API_KEY", "internal-cluster-key-change-me")}

# Application-layer lock to prevent parallel double-spends by the LLM
active_checkouts = set()

class ECommerceTools:
    
    @tool
    async def search_products(query: str = "") -> str:
        """Useful to find products by name. If the query is empty or 'all', it returns all available products."""
        try:
            search_query = "" if query.lower() in ["", "all", "available", "products"] else query
            async with httpx.AsyncClient(headers=API_HEADERS, timeout=10.0) as client:
                resp = await client.get(f"{PRODUCT_URL}/", params={"query": search_query})
                resp.raise_for_status()
                products = resp.json()
                
                # SENIOR ENG FIX: Safely cast prices to float to prevent TypeError crashes during sorting
                if isinstance(products, list):
                    for p in products:
                        try:
                            p['_sort_price'] = float(p.get('price', 0))
                        except (ValueError, TypeError):
                            p['_sort_price'] = float('inf')
                            
                    products.sort(key=lambda x: x['_sort_price'])
                    
                    # Cleanup temporary sort key and truncate to prevent token overflow
                    for p in products:
                        p.pop('_sort_price', None)
                        
                    if len(products) > 20:
                        products = products[:20]
                        
                return str(products)
        except Exception as e:
            return f"Error connecting to Product Service: {e}"

    @tool
    async def add_to_cart(session_id: str, product_id: int, quantity: int) -> str:
        """Adds a product to the user's cart. Requires session_id, product_id, quantity."""
        if quantity <= 0:
            return "Error: Quantity must be a positive integer greater than zero."
            
        try:
            payload = {"product_id": int(product_id), "quantity": int(quantity)}
            async with httpx.AsyncClient(headers=API_HEADERS, timeout=10.0) as client:
                resp = await client.post(f"{SESSION_URL}/{session_id}/items", json=payload)
                resp.raise_for_status()
                return f"Successfully added {quantity} of product {product_id} to cart."
        except Exception as e:
            return f"Error connecting to Session Service: {e}"
        
    @tool
    async def remove_from_cart(session_id: str, product_id: int) -> str:
        """Removes a product from the user's cart. Requires session_id and product_id."""
        try:
            async with httpx.AsyncClient(headers=API_HEADERS, timeout=10.0) as client:
                resp = await client.delete(f"{SESSION_URL}/{session_id}/items/{int(product_id)}")
                resp.raise_for_status()
                return f"Successfully removed product {product_id} from cart."
        except Exception as e:
            return f"Error connecting to Session Service: {e}"

    @tool
    async def view_cart(session_id: str) -> str:
        """See what is inside the cart. Useful for the Checkout Agent to verify items."""
        try:
            async with httpx.AsyncClient(headers=API_HEADERS, timeout=10.0) as client:
                resp = await client.get(f"{SESSION_URL}/{session_id}")
                if resp.status_code == 404:
                    return "Cart is empty."
                return str(resp.json())
        except Exception as e:
            return f"Error: {e}"

    @tool
    async def checkout(session_id: str) -> str:
        """Buys everything in the cart. Processes stock, creates orders, and handles payment."""
        
        # MUTEX LOCK: Prevents the LLM from executing parallel checkout tool calls
        if session_id in active_checkouts:
            return "Error: A checkout is already in progress for this session. Please wait."
        active_checkouts.add(session_id)
        
        try:
            results = []
            async with httpx.AsyncClient(headers=API_HEADERS, timeout=15.0) as client:
                # 1. Get Cart
                cart_resp = await client.get(f"{SESSION_URL}/{session_id}")
                if cart_resp.status_code != 200:
                    return "Cart is empty."

                cart = cart_resp.json()
                items = cart.get("items", [])
                if not items:
                    return "Cart is empty."

                # 2. Process Items USING THE SAGA
                for item in items:
                    ctx = {
                        "client": client,
                        "session_id": session_id,
                        "pid": int(item["product_id"]),
                        "qty": int(item["quantity"])
                    }
                    
                    saga = build_checkout_saga()
                    
                    try:
                        await saga.execute(ctx)
                        results.append(
                            f"Success! Ordered {ctx['product_name']}. "
                            f"Order ID: {ctx['order_id']} | "
                            f"Transaction ID: {ctx['transaction_id']} | "
                            f"Total Paid: ${ctx['total_price']}"
                        )
                    except Exception as e:
                        # If saga rolls back, continue to next item
                        results.append(f"Error processing Product {ctx['pid']}: Transaction aborted and rolled back.")
                
                # 3. CLEAR CART 
                del_resp = await client.delete(f"{SESSION_URL}/{session_id}/items")
                del_resp.raise_for_status()
                
                if not results:
                    return "Cart is empty (or items were already processed)."
                
                return "\n".join(results)

        except Exception as e:
            return f"Checkout failed: {e}"
        finally:
            # RELEASE MUTEX
            active_checkouts.remove(session_id)