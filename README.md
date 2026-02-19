# 🛍️ E-Commerce Multi-Agent Cluster

A production-grade, AI-powered e-commerce backend built with a **multi-agent microservices architecture**. Natural language requests like *"Buy the cheapest laptop and checkout"* are interpreted by a LangGraph agent orchestrator and translated into coordinated API calls across independent services.

---

## 📋 Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Services](#services)
- [Agent Design](#agent-design)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Setup & Installation](#setup--installation)
- [Running the Project](#running-the-project)
- [API Reference](#api-reference)
- [Running Evaluations](#running-evaluations)
- [Project Structure](#project-structure)
- [Design Decisions](#design-decisions)

---

## Overview

This system exposes a single `/chat` endpoint that accepts natural language commands. An **Orchestrator service** powered by LangGraph routes the message to the appropriate AI sub-agent (Sales or Checkout), which in turn calls the relevant downstream microservices.

**Example interactions:**
- `"Show me available products"` → Lists all products, no purchase
- `"Buy 2 Yonex rackets"` → Searches, validates stock, adds to cart, and auto-checks out
- `"Buy one of everything"` → Iterates all products, adds each to cart, and processes payment
- `"Buy the cheapest ball"` → Detects a price tie and asks the user to choose

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT / USER                           │
│                  POST /chat {session_id, message}               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  ORCHESTRATOR SERVICE  :8000                    │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                  LangGraph State Machine                │   │
│   │                                                         │   │
│   │   ┌──────────────┐        ┌──────────────────────────┐  │   │
│   │   │  Supervisor  │──────▶│      Sales Agent          │  │   │
│   │   │  (Router)    │       │  - search_products        │  │   │
│   │   └──────────────┘       │  - add_to_cart            │  │   │
│   │          │               │  - remove_from_cart       │  │   │
│   │          │               └────────────┬─────────────-┘  │   │
│   │          │                            │ post_sales_router│   │
│   │          │               ┌────────────▼─────────────-┐  │   │
│   │          └──────────────▶│    Checkout Agent         │  │   │
│   │                          │  - view_cart              │  │   │
│   │                          │  - checkout               │  │   │
│   │                          └──────────────────────────-┘  │   │
│   └─────────────────────────────────────────────────────────┘   │
│                    (MemorySaver checkpointer)                    │
└────────┬──────────────┬──────────────┬──────────────┬───────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
  ┌────────────┐ ┌────────────┐ ┌──────────────┐ ┌──────────────┐
  │  Product   │ │   Order    │ │   Payment    │ │   Session    │
  │  Service   │ │  Service   │ │   Service    │ │   Service    │
  │   :8001    │ │   :8002    │ │    :8003     │ │    :8004     │
  └─────┬──────┘ └─────┬──────┘ └──────┬───────┘ └──────┬───────┘
        │              │               │                 │
        └──────────────┴───────────────┴─────────────────┘
                                   │
                          ┌────────▼────────┐
                          │   PostgreSQL     │
                          │   :5432 (5433)   │
                          │                 │
                          │ product_schema  │
                          │ order_schema    │
                          │ payment_schema  │
                          │ session_schema  │
                          └─────────────────┘
```

### Request Flow (Happy Path: "Buy 1 MacBook Pro")

```
1. POST /chat  →  Orchestrator receives message
2. Supervisor Node routes to → Sales Agent
3. Sales Agent calls search_products("MacBook Pro")
   └─▶ GET http://product_service:8000/?query=MacBook+Pro
4. Sales Agent calls add_to_cart(session_id, product_id=1, quantity=1)
   └─▶ POST http://session_service:8000/{session_id}/items
5. post_sales_router detects add_to_cart → routes to Checkout Agent
6. Checkout Agent calls view_cart(session_id)
   └─▶ GET http://session_service:8000/{session_id}
7. Checkout Agent calls checkout(session_id):
   a. GET  /session/{id}          → fetch cart items
   b. DELETE /session/{id}/items/{pid} → atomic lock (claim item)
   c. GET  /product/{pid}         → fetch current price
   d. POST /product/{pid}/reduce_stock → decrement inventory
   e. POST /order/                → create order record
   f. POST /payment/              → process payment, get transaction_id
8. Response returned to user with Order ID + Transaction ID
```

---

## Services

| Service | Port (Host) | Internal Port | Responsibility |
|---------|------------|---------------|----------------|
| **Orchestrator** | 8000 | 8000 | LangGraph multi-agent orchestration, `/chat` endpoint |
| **Product Service** | 8001 | 8000 | Product catalog, stock management |
| **Order Service** | 8002 | 8000 | Order creation and tracking |
| **Payment Service** | 8003 | 8000 | Payment processing, transaction IDs |
| **Session Service** | 8004 | 8000 | Shopping cart / session management |
| **PostgreSQL** | 5433 | 5432 | Persistent storage (isolated schemas per service) |

### Database Schema Design

Each microservice uses a **dedicated PostgreSQL schema** to simulate service isolation while sharing a single database instance:

```sql
product_schema.products    (id, name, price, stock)
order_schema.orders        (id, product_id, quantity, total_price, status)
payment_schema.payments    (id, order_id, amount, status, transaction_id)
session_schema.sessions    (session_id, user_id, is_active)
session_schema.session_items (id, session_id, product_id, quantity)
```

---

## Agent Design

The orchestrator uses a **LangGraph StateGraph** with two ReAct sub-agents and a rule-based supervisor:

### Supervisor (Routing Logic)
Routes incoming messages deterministically based on keyword detection:
- Keywords (`checkout`, `pay now`, `view cart`, `my cart`) without (`buy`, `add`) → **Checkout Agent**
- All other messages → **Sales Agent**

### Sales Agent
Equipped with tools: `search_products`, `add_to_cart`, `remove_from_cart`

Key behaviors enforced via system prompt:
- Always searches before buying — never assumes product IDs
- Validates stock before calling `add_to_cart` — refuses if requested quantity exceeds stock
- Rejects zero/negative quantities
- Handles implicit references ("buy it" → refers to last search result)
- Tie-breaker logic: if multiple products share the same price, lists them and asks user to choose
- Bulk purchasing: "buy one of everything" iterates and adds each product

### Checkout Agent
Equipped with tools: `view_cart`, `checkout`

Key behaviors:
- Always calls `view_cart` first before attempting checkout
- Reports Order ID, Transaction ID, and Total Paid for every item
- Idempotent: second checkout on an empty cart reports "Cart is empty" cleanly

### Post-Sales Router
After the Sales Agent completes, this conditional edge decides the next step:
- If `add_to_cart` was the last tool call → route to **Checkout Agent** (auto-checkout flow)
- If the user mentioned `remove`/`delete`/`cancel` → go to **END** (no auto-checkout)
- Otherwise → **END**

### Memory & Session Continuity
- LangGraph's `MemorySaver` checkpointer persists conversation state across turns using `session_id` as the `thread_id`
- The `session_id` is injected into the system prompt so all tool calls use the correct cart

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Agent Framework** | LangGraph 0.2.20, LangChain 0.2.x |
| **LLM** | OpenAI GPT-4o-mini (Sales + Checkout), GPT-4o (Eval Judge) |
| **API Framework** | FastAPI + Uvicorn |
| **ORM** | SQLAlchemy 2.0 (async) with asyncpg |
| **Database** | PostgreSQL 15 |
| **HTTP Client** | httpx (sync, used inside tools) |
| **Containerization** | Docker + Docker Compose |
| **Package Manager** | uv |
| **Validation** | Pydantic v2 |
| **Eval Framework** | Custom async test runner + LLM-as-judge |

---

## Prerequisites

- **Docker** and **Docker Compose** (Docker Desktop or Docker Engine ≥ 24)
- **Python 3.12+** (only needed to run evals locally)
- **OpenAI API Key**
- **uv** package manager (optional, for local dev)

---

## Setup & Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd ecommerce-cluster
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env   # or create manually
```

```env
# .env
OPENAI_API_KEY=sk-...your-key-here...
```

The following are optional overrides (defaults shown):

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=ecommerce
```

### 3. Build Docker Images

```bash
docker compose build
```

This builds a single shared image used by all Python services.

---

## Running the Project

### Start All Services

```bash
docker compose up
```

All services will start. PostgreSQL runs a healthcheck before any service begins accepting connections. Tables and schemas are created automatically on startup.

To run in detached mode:

```bash
docker compose up -d
```

### Verify Services Are Running

```bash
curl http://localhost:8000/health   # Orchestrator
curl http://localhost:8001/health   # Product Service
curl http://localhost:8002/health   # Order Service
curl http://localhost:8003/health   # Payment Service
curl http://localhost:8004/health   # Session Service
```

Each should return `{"service": "<name>", "status": "running"}`.

### Seed Products (Optional)

```bash
curl -X POST http://localhost:8001/ \
  -H "Content-Type: application/json" \
  -d '{"name": "MacBook Pro", "price": 2000.0, "stock": 10}'

curl -X POST http://localhost:8001/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Yonex Arcsaber 11 Pro", "price": 200.0, "stock": 10}'
```

### Stopping Services

```bash
docker compose down          # Stop containers
docker compose down -v       # Stop containers and remove volumes (wipes DB)
```

---

## API Reference

### Orchestrator — Chat Endpoint

**`POST http://localhost:8000/chat`**

The primary interface. Send a natural language message with a session identifier.

```json
{
  "session_id": "my-unique-session-123",
  "message": "Find a MacBook Pro and buy 1 unit."
}
```

**Response:**
```json
{
  "response": "I found the MacBook Pro ($2000.00, 10 in stock). I've added 1 to your cart and processed the checkout. Order ID: 1 | Transaction ID: a3f2b1c0-... | Total Paid: $2000.00"
}
```

> **Note:** The `session_id` is used both as the LangGraph memory thread and the shopping cart identifier. Use the same `session_id` across multiple messages to maintain conversation continuity.

---

### Product Service

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | List all products. Optional `?query=` filter |
| `GET` | `/{product_id}` | Get a single product by ID |
| `POST` | `/` | Create a new product |
| `POST` | `/{product_id}/reduce_stock` | Decrement stock by `quantity` |
| `POST` | `/reset_db` | Truncate all products (testing only) |

**Create Product Body:**
```json
{ "name": "string", "price": 0.0, "stock": 0 }
```

**Reduce Stock Body:**
```json
{ "quantity": 1 }
```

---

### Order Service

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/` | Create an order |
| `GET` | `/{order_id}` | Retrieve an order |

**Create Order Body:**
```json
{ "product_id": 1, "quantity": 1, "unit_price": 2000.0 }
```

---

### Payment Service

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/` | Process a payment |

**Process Payment Body:**
```json
{ "order_id": 1, "amount": 2000.0 }
```

---

### Session Service

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/` | Create a new session (cart) |
| `GET` | `/{session_id}` | Get session and cart contents |
| `POST` | `/{session_id}/items` | Add item to cart |
| `DELETE` | `/{session_id}/items/{product_id}` | Remove specific item from cart |
| `DELETE` | `/{session_id}/items` | Clear entire cart |

**Add Item Body:**
```json
{ "product_id": 1, "quantity": 2 }
```

---

## Running Evaluations

The project includes an LLM-as-judge eval harness with 21 test cases covering happy paths, edge cases, and safety scenarios.

### Setup

Install dependencies locally:

```bash
pip install httpx langchain-openai termcolor
# or with uv:
uv run pip install httpx langchain-openai termcolor
```

Ensure all Docker services are running (`docker compose up -d`).

### Run Evals

```bash
python tests/run_evals.py
```

The eval runner will:
1. Reset and reseed the product database with 6 products
2. Create a fresh session (cart) for each test case
3. Send the user message to the `/chat` endpoint
4. Pass the agent's response to GPT-4o acting as a QA judge
5. Report PASS / FAIL with a brief reason

### Test Cases Summary

| Category | Tests |
|----------|-------|
| Happy path purchases | Buy specific product, buy by synonym, buy plural name |
| Quantity validation | Zero quantity, negative quantity, excess stock, huge number |
| Cart operations | Checkout empty cart, double checkout (idempotency), remove item |
| Multi-step reasoning | Implicit reference ("buy it"), bulk buy (one of everything), sequential purchases |
| Edge case logic | Cheapest item (single), cheapest item (tie → ask user) |
| Safety / Robustness | Prompt injection (price manipulation), garbage input (non-existent product) |

---

## Project Structure

```
ecommerce-cluster/
├── docker-compose.yml          # All service definitions
├── dockerfile                  # Shared image for all Python services
├── pyproject.toml              # Python dependencies (uv)
├── supervisord.conf            # Alternative single-container startup
│
├── shared/
│   └── config/
│       └── database.py         # Shared SQLAlchemy engine + Base
│
├── services/
│   ├── orchestrator/
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── router.py           # /chat endpoint
│   │   ├── service.py          # Message processing, session config
│   │   ├── agent.py            # LangGraph StateGraph definition
│   │   ├── agents.py           # LLM + prompt templates
│   │   ├── tools.py            # LangChain tools (HTTP calls to services)
│   │   └── schemas.py          # ChatRequest / ChatResponse models
│   │
│   ├── product_service/        # CRUD + stock management
│   ├── order_service/          # Order creation and lookup
│   ├── payment_service/        # Payment processing + UUID transaction IDs
│   └── session_service/        # Cart / session management
│
└── tests/
    ├── dataset.json            # 21 eval test cases
    └── run_evals.py            # Async eval runner with LLM judge
```

Each service follows the same layered structure:
```
service/
├── main.py        # FastAPI app + startup (table creation)
├── router.py      # HTTP endpoints
├── service.py     # Business logic
├── repository.py  # Database queries (SQLAlchemy)
├── models.py      # SQLAlchemy ORM models
└── schemas.py     # Pydantic request/response models
```

---

## Design Decisions

**Atomic checkout via optimistic locking** — The checkout tool performs a `DELETE` on each cart item before processing it. This acts as an atomic claim: if two requests try to checkout the same item simultaneously, only one will succeed with a `200 OK` delete, preventing double-processing.

**Shared image, single Dockerfile** — All Python services are built from one image. The correct service is launched via the `command` override in `docker-compose.yml`. This simplifies CI builds and ensures consistent dependency versions.

**Schema-per-service isolation** — Each microservice owns a dedicated PostgreSQL schema (`product_schema`, `order_schema`, etc.) rather than a dedicated database. This simulates microservice boundary isolation while keeping local development simple with a single DB container.

**Pinned LangChain versions** — LangGraph 0.2.x has strict compatibility constraints with `langchain-core`. The Dockerfile force-installs pinned versions after the base `uv sync` to prevent version drift from breaking the `langchain.verbose` attribute interface.

**LLM-as-judge evaluation** — Rather than brittle string matching, test verdicts are determined by GPT-4o reading the agent's response against expected behavior described in plain English. This handles natural language variation and multi-step reasoning outputs gracefully.

**Session ID as memory thread** — The same `session_id` the client provides is used as both the LangGraph `thread_id` (for `MemorySaver` conversation history) and the cart identifier in the Session Service. This means multi-turn conversations retain context without any server-side session mapping.
