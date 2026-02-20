from prometheus_client import Counter, Histogram, Gauge

# Business Metrics
ecomm_checkout_total = Counter(
    "ecomm_checkout_total", 
    "Total checkouts processed", 
    ["status"] # Labels: 'success', 'failed'
)

ecomm_checkout_duration_seconds = Histogram(
    "ecomm_checkout_duration_seconds", 
    "Checkout duration in seconds"
)

ecomm_saga_compensation_total = Counter(
    "ecomm_saga_compensation_total", 
    "Total saga compensations triggered", 
    ["step_name"] # Labels: 'lock_cart_item', 'reduce_stock', etc.
)

ecomm_llm_tokens_total = Counter(
    "ecomm_llm_tokens_total", 
    "Total LLM tokens used", 
    ["model", "type"] # Labels: type='prompt' or 'completion'
)

ecomm_active_carts = Gauge(
    "ecomm_active_carts", 
    "Number of currently active carts"
)