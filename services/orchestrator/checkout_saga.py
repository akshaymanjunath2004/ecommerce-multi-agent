import os
import logging
from .saga import SagaOrchestrator

logger = logging.getLogger(__name__)

# Env Vars
PRODUCT_URL = os.getenv("PRODUCT_URL", "http://localhost:8001")
ORDER_URL = os.getenv("ORDER_URL", "http://localhost:8002")
PAYMENT_URL = os.getenv("PAYMENT_URL", "http://localhost:8003")
SESSION_URL = os.getenv("SESSION_URL", "http://localhost:8004")

# Security Headers for internal service-to-service communication
API_HEADERS = {"X-Internal-API-Key": os.getenv("INTERNAL_API_KEY", "internal-cluster-key-change-me")}

# --- ACTIONS ---

async def lock_cart_item(ctx: dict):
    client, session_id, pid = ctx["client"], ctx["session_id"], ctx["pid"]
    resp = await client.delete(f"{SESSION_URL}/{session_id}/items/{pid}", headers=API_HEADERS)
    if resp.status_code != 200:
        raise Exception("Item already processed or removed")

async def fetch_product(ctx: dict):
    client, pid = ctx["client"], ctx["pid"]
    resp = await client.get(f"{PRODUCT_URL}/{pid}", headers=API_HEADERS)
    resp.raise_for_status()
    product = resp.json()
    ctx["product_name"] = product.get("name", "Unknown Product")
    ctx["unit_price"] = product["price"]

async def reduce_stock(ctx: dict):
    client, pid, qty = ctx["client"], ctx["pid"], ctx["qty"]
    resp = await client.post(f"{PRODUCT_URL}/{pid}/reduce_stock", json={"quantity": qty}, headers=API_HEADERS)
    resp.raise_for_status()

async def create_order(ctx: dict):
    client, pid, qty, price = ctx["client"], ctx["pid"], ctx["qty"], ctx["unit_price"]
    payload = {"product_id": pid, "quantity": qty, "unit_price": price}
    resp = await client.post(f"{ORDER_URL}/", json=payload, headers=API_HEADERS)
    resp.raise_for_status()
    order = resp.json()
    ctx["order_id"] = order["id"]
    ctx["total_price"] = order["total_price"]

async def process_payment(ctx: dict):
    client, order_id, amount = ctx["client"], ctx["order_id"], ctx["total_price"]
    payload = {"order_id": order_id, "amount": amount}
    resp = await client.post(f"{PAYMENT_URL}/", json=payload, headers=API_HEADERS)
    resp.raise_for_status()
    payment = resp.json()
    ctx["transaction_id"] = payment.get("transaction_id")


# --- COMPENSATIONS (Rollbacks) ---

async def rollback_cart_item(ctx: dict):
    client, session_id, pid, qty = ctx["client"], ctx["session_id"], ctx["pid"], ctx["qty"]
    payload = {"product_id": pid, "quantity": qty}
    await client.post(f"{SESSION_URL}/{session_id}/items", json=payload, headers=API_HEADERS)

async def rollback_stock(ctx: dict):
    client, pid, qty = ctx["client"], ctx["pid"], ctx["qty"]
    await client.post(f"{PRODUCT_URL}/{pid}/restore_stock", json={"quantity": qty}, headers=API_HEADERS)

async def rollback_order(ctx: dict):
    client, order_id = ctx["client"], ctx.get("order_id")
    if order_id:
        await client.patch(f"{ORDER_URL}/{order_id}/cancel", headers=API_HEADERS)

async def rollback_payment(ctx: dict):
    tx_id = ctx.get("transaction_id")
    if tx_id:
        logger.info(f"Logging Refund Intent for Transaction: {tx_id}")
        # In a real app, hit Stripe/Razorpay refund webhook here (just simulating a gateway call)


# --- BUILDER FACTORY ---

def build_checkout_saga() -> SagaOrchestrator:
    saga = SagaOrchestrator()
    saga.add_step("lock_cart_item", lock_cart_item, rollback_cart_item)
    saga.add_step("fetch_product", fetch_product, None) # Read-only, no rollback needed
    saga.add_step("reduce_stock", reduce_stock, rollback_stock)
    saga.add_step("create_order", create_order, rollback_order)
    saga.add_step("process_payment", process_payment, rollback_payment)
    return saga