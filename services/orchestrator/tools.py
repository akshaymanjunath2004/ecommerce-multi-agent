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
    def search_products(query: str = "") -> str:
        """Useful to find products by name. If the query is empty or 'all', it returns all available products."""
        try:
            search_query = "" if query.lower() in ["", "all", "available", "products"] else query
            with httpx.Client() as client:
                resp = client.get(f"{PRODUCT_URL}/", params={"query": search_query})
                resp.raise_for_status()
                products = resp.json()
                
                # SENIOR ENG FIX: Sort by price (Ascending) so cheapest is always first.
                if isinstance(products, list):
                    products.sort(key=lambda x: x.get('price', 0))
                    # Safety Limit to prevent Context Window overflow
                    if len(products) > 20:
                        products = products[:20]
                        
                return str(products)
        except Exception as e:
            return f"Error connecting to Product Service: {e}"

    @tool
    def add_to_cart(session_id: str, product_id: int, quantity: int) -> str:
        """Adds a product to the user's cart. Requires session_id, product_id, quantity."""
        if quantity <= 0:
            return "Error: Quantity must be a positive integer greater than zero."
            
        try:
            payload = {"product_id": int(product_id), "quantity": int(quantity)}
            with httpx.Client() as client:
                resp = client.post(f"{SESSION_URL}/{session_id}/items", json=payload)
                resp.raise_for_status()
                return f"Successfully added {quantity} of product {product_id} to cart."
        except Exception as e:
            return f"Error connecting to Session Service: {e}"
        
    @tool
    def remove_from_cart(session_id: str, product_id: int) -> str:
        """Removes a product from the user's cart. Requires session_id and product_id."""
        try:
            with httpx.Client() as client:
                resp = client.delete(f"{SESSION_URL}/{session_id}/items/{int(product_id)}")
                resp.raise_for_status()
                return f"Successfully removed product {product_id} from cart."
        except Exception as e:
            return f"Error connecting to Session Service: {e}"

    @tool
    def view_cart(session_id: str) -> str:
        """See what is inside the cart. Useful for the Checkout Agent to verify items."""
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
        """Buys everything in the cart. Processes stock, creates orders, and handles payment."""
        try:
            results = []
            with httpx.Client() as client:
                # 1. Get Cart
                cart_resp = client.get(f"{SESSION_URL}/{session_id}")
                if cart_resp.status_code != 200:
                    return "Cart is empty."

                cart = cart_resp.json()
                items = cart.get("items", [])
                if not items:
                    return "Cart is empty."

                # ATOMIC PROCESSING LOOP
                for item in items:
                    pid = int(item["product_id"])
                    qty = int(item["quantity"])

                    # 2. ATOMIC LOCK: Try to DELETE the item first.
                    # This guarantees we only process items we successfully claimed from the DB.
                    del_resp = client.delete(f"{SESSION_URL}/{session_id}/items/{pid}")
                    
                    if del_resp.status_code != 200:
                        # Item already gone (processed by parallel thread?), skip it.
                        continue

                    # 3. Fetch product details
                    product_resp = client.get(f"{PRODUCT_URL}/{pid}")
                    if product_resp.status_code != 200:
                        results.append(f"Error: Product {pid} not found (but was in cart).")
                        continue

                    product = product_resp.json()
                    product_name = product.get("name", "Unknown Product") 
                    real_price = product["price"]

                    # 4. Reduce stock
                    stock_payload = {"quantity": qty}
                    stock_resp = client.post(
                        f"{PRODUCT_URL}/{pid}/reduce_stock",
                        json=stock_payload
                    )

                    if stock_resp.status_code != 200:
                        try:
                            error_detail = stock_resp.json().get('detail', stock_resp.text)
                        except:
                            error_detail = "Unknown error"
                        results.append(f"Error: Could not reduce stock for Product {pid}. Reason: {error_detail}")
                        continue

                    # 5. Create order
                    order_payload = {
                        "product_id": pid,
                        "quantity": qty,
                        "unit_price": real_price
                    }

                    order_resp = client.post(f"{ORDER_URL}/", json=order_payload)
                    order_resp.raise_for_status()
                    order = order_resp.json()
                    order_id = order["id"]

                    # 6. Process payment
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
                        f"Success! Ordered {product_name}. Order ID: {order_id} | Transaction ID: {tx_id} | Total Paid: ${total_price}"
                    )
                
                if not results:
                    return "Cart is empty (or items were already processed)."
                
                return "\n".join(results)

        except Exception as e:
            return f"Checkout failed: {e}"