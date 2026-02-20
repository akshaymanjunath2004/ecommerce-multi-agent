import os
import logging
import structlog
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

# OpenTelemetry
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

# 1. Structlog Processor: Injects Trace/Span IDs into every log line
def add_otel_ids(logger, log_method, event_dict):
    span = trace.get_current_span()
    if span.is_recording():
        ctx = span.get_span_context()
        event_dict["trace_id"] = trace.format_trace_id(ctx.trace_id)
        event_dict["span_id"] = trace.format_span_id(ctx.span_id)
    return event_dict

# 2. Configure Structlog for JSON output
def configure_logging():
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            add_otel_ids, # <-- Magic happens here
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

# 3. Configure OpenTelemetry Tracing
def configure_tracing(app: FastAPI, service_name: str):
    # Set the global tracer provider
    resource = Resource.create({SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    # Export to Jaeger via OTLP gRPC (defaults to localhost:4317)
    otlp_endpoint = os.getenv("OTLP_ENDPOINT", "http://localhost:4317")
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))

    # Auto-instrument FastAPI (creates spans for all incoming requests)
    FastAPIInstrumentor.instrument_app(app)
    
    # Auto-instrument HTTPX (creates child spans for all outgoing requests)
    HTTPXClientInstrumentor().instrument()

# 4. Configure Prometheus Metrics
def configure_metrics(app: FastAPI):
    # This automatically tracks HTTP request latency, status codes, etc.
    # and exposes them at the /metrics endpoint
    Instrumentator().instrument(app).expose(app)

# --- THE MASTER SETUP FUNCTION ---
def setup_observability(app: FastAPI, service_name: str):
    """
    Bootstraps Logging, Tracing, and Metrics for a FastAPI app.
    Call this once in main.py before starting the server.
    """
    configure_logging()
    configure_tracing(app, service_name)
    configure_metrics(app)