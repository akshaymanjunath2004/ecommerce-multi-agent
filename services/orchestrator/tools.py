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
                cart_resp = client.get(f"{SESSION_URL}/{session_id}")
                if cart_resp.status_code != 200:
                    return "Cart is empty."

                cart = cart_resp.json()
                if not cart.get("items"):
                    return "Cart is empty."

                for item in cart["items"]:
                    pid = item["product_id"]
                    qty = item["quantity"]

                    # Fetch product (STRICT)
                    product_resp = client.get(f"{PRODUCT_URL}/{pid}")
                    if product_resp.status_code != 200:
                        return f"Error: Product with ID {pid} does not exist."

                    product = product_resp.json()
                    real_price = product["price"]

                    # Reduce stock
                    stock_payload = {"quantity": qty}
                    stock_resp = client.post(
                        f"{PRODUCT_URL}/{pid}/reduce_stock",
                        json=stock_payload
                    )

                    if stock_resp.status_code != 200:
                        return f"Error: Could not reduce stock for Product {pid}."

                    # Create order
                    order_payload = {
                        "product_id": pid,
                        "quantity": qty,
                        "unit_price": real_price
                    }

                    order_resp = client.post(f"{ORDER_URL}/", json=order_payload)
                    order_resp.raise_for_status()
                    order = order_resp.json()

                    order_id = order["id"]

                    # Process payment
                    pay_payload = {
                        "order_id": order_id,
                        "amount": order["total_price"]
                    }

                    payment_resp = client.post(f"{PAYMENT_URL}/", json=pay_payload)
                    payment_resp.raise_for_status()
                    payment = payment_resp.json()

                    tx_id = payment.get("transaction_id")

                    total_price = order["total_price"]

                    results.append(
                        f"Success! Order ID: {order_id} | Transaction ID: {tx_id} | Total Paid: ${total_price}"
                    )

                return "\n".join(results)

        except Exception as e:
            return f"Checkout failed: {e}"
