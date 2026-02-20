"""Observability setup for FastAPI services.
docker-compose sets 'OTEL_EXPORTER_OTLP_ENDPOINT'. This mismatch meant
Jaeger received ZERO traces from any service. Now reads the correct var,
with 'http://jaeger:4317' as the Docker-network default.
"""
import os
import logging
import structlog
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor


def add_otel_ids(logger, log_method, event_dict):
    """Inject active OpenTelemetry trace/span IDs into every log line."""
    span = trace.get_current_span()
    if span.is_recording():
        ctx = span.get_span_context()
        event_dict["trace_id"] = trace.format_trace_id(ctx.trace_id)
        event_dict["span_id"] = trace.format_span_id(ctx.span_id)
    return event_dict


def configure_logging():
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            add_otel_ids,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def configure_tracing(app: FastAPI, service_name: str):
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317")

    resource = Resource.create({SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))

    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()


def configure_metrics(app: FastAPI):
    Instrumentator().instrument(app).expose(app)


def setup_observability(app: FastAPI, service_name: str):
    """
    Bootstraps Logging, Tracing, and Metrics for a FastAPI app.
    Call once in each service's main.py before starting the server.
    """
    configure_logging()
    configure_tracing(app, service_name)
    configure_metrics(app)