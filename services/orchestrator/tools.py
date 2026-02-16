import os
import httpx
from langchain_core.tools import tool

# Env Vars
PRODUCT_URL = os.getenv("PRODUCT_URL", "http://localhost:8001")
ORDER_URL = os.getenv("ORDER_URL", "http://localhost:8002")
PAYMENT_URL = os.getenv("PAYMENT_URL", "http://localhost:8003")
SESSION_URL = os.getenv("SESSION_URL", "http://localhost:8004")

class ECommerceTools:
    
    @tool
    def search_products(query: str) -> str:
        """Useful to find products by name. Returns JSON list of products."""
        try:
            with httpx.Client() as client:
                resp = client.get(f"{PRODUCT_URL}/", params={"query": query})
                return str(resp.json())
        except Exception as e:
            return f"Error connecting to Product Service: {e}"

    @tool
    def add_to_cart(session_id: str, product_id: int, quantity: int) -> str:
        """Adds a product to the user's cart. Requires session_id, product_id, quantity."""
        try:
            payload = {"product_id": product_id, "quantity": quantity}
            with httpx.Client() as client:
                resp = client.post(f"{SESSION_URL}/{session_id}/items", json=payload)
                resp.raise_for_status()
                return "Added to cart."
        except Exception as e:
            return f"Error connecting to Session Service: {e}"

    @tool
    def view_cart(session_id: str) -> str:
        """See what is inside the cart."""
        try:
            with httpx.Client() as client:
                resp = client.get(f"{SESSION_URL}/{session_id}")
                if resp.status_code == 404:
                    return "Cart is empty."
                return str(resp.json())
        except Exception as e:
            return f"Error: {e}"

    @tool
    def checkout(session_id: str) -> str:
        """
        Buys everything in the cart.
        """
        try:
            results = []
            with httpx.Client() as client:
                # 1. Get Cart
                cart = client.get(f"{SESSION_URL}/{session_id}").json()
                if not cart.get("items"):
                    return "Cart is empty."

                # 2. Loop through items
                for item in cart["items"]:
                    pid = item["product_id"]
                    qty = item["quantity"]
                    
                    # A. Get Price
                    product_resp = client.get(f"{PRODUCT_URL}/{pid}")
                    if product_resp.status_code != 200:
                         results.append(f"Error: Product {pid} not found. Skipping.")
                         continue
                    product = product_resp.json()
                    real_price = product["price"]

                    # B. Reduce Stock
                    stock_payload = {"quantity": qty}
                    stock_resp = client.post(f"{PRODUCT_URL}/{pid}/reduce_stock", json=stock_payload)
                    if stock_resp.status_code != 200:
                        results.append(f"Error: Could not reduce stock for Product {pid}. Skipping.")
                        continue 
                    
                    # C. Create Order
                    order_payload = {
                        "product_id": pid,
                        "quantity": qty,
                        "unit_price": real_price
                    }
                    order = client.post(f"{ORDER_URL}/", json=order_payload).json()
                    order_id = order["id"]
                    
                    # D. Pay
                    pay_payload = {"order_id": order_id, "amount": order["total_price"]}
                    payment = client.post(f"{PAYMENT_URL}/", json=pay_payload).json()
                    tx_id = payment.get("transaction_id", "Unknown")
                    
                    total_price = order["total_price"]
                    
                    # FIXED: Removed the backslash that caused the SyntaxWarning
                    results.append(f"Success! Order ID: {order_id} | Transaction ID: {tx_id} | Total Paid: ${total_price}")
                
                return "\n".join(results)
        except Exception as e:
            return f"Checkout failed: {e}"