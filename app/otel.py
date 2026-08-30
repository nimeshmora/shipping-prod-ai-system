"""Week 05b: the same trace, in the industry-standard shape.

Everything in app/trace.py is already a trace. This file does not replace it -
it publishes the same information again in the format the rest of the industry
speaks, so it lands in Grafana, Honeycomb, Datadog, Jaeger or Cloud Trace
without you writing an adapter for each one.

The vocabulary maps one-to-one onto what you already built:

    our trace dict     ->  a SPAN          (one unit of work, with a duration)
    turn_id            ->  trace_id        (ties spans from one turn together)
    each loop step     ->  a child span    (nested inside the turn)
    each tool call     ->  a child span
    cost_usd, tokens   ->  span attributes (labelled facts about the work)
    error              ->  span status     (OK or ERROR)
    print(json)        ->  an exporter     (where finished spans get sent)

Off by default, and silent if the packages are missing. That is deliberate:
Week 05 must keep working on a laptop with no key, no cloud and no internet.

Two places to look at your traces, and the point is that the code below does
not change between them:

  1. On your laptop - Grafana, which is what most teams actually use:

        make trace-ui                            # grafana + tempo
        export OTEL_ENABLED=1
        export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
        make run
        # then open http://localhost:3000 -> Explore -> Tempo

  2. In production - Google Cloud Trace, which you already have because your
     agent runs on Cloud Run. Nothing to install and nothing to run:

        OTEL_ENABLED=1
        OTEL_TARGET=gcp

That is the whole promise of OpenTelemetry: you instrument once, and the
place you send it to becomes a setting rather than a rewrite.
"""
import os

ENABLED = os.environ.get("OTEL_ENABLED", "").lower() in ("1", "true", "yes")
SERVICE_NAME = os.environ.get("OTEL_SERVICE_NAME", "ship-agent")

_tracer = None
_ready = False


def _setup():
    """Build a tracer once. Never raises - observability must not break the app."""
    global _tracer, _ready
    _ready = True
    if not ENABLED:
        return None
    try:
        from opentelemetry import trace as ot
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor, ConsoleSpanExporter)

        provider = TracerProvider(
            resource=Resource.create({"service.name": SERVICE_NAME}))

        # Where finished spans go. This is the only part that changes between
        # your laptop and production - the instrumentation above never does.
        target = os.environ.get("OTEL_TARGET", "").lower()
        endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")

        if target == "gcp":
            # Google Cloud Trace. Free with your project, already collecting.
            from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
            exporter = CloudTraceSpanExporter()
        elif endpoint:
            # Anything that speaks OTLP: Tempo, Jaeger, Honeycomb, Datadog...
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter)
            exporter = OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces")
        else:
            # No destination configured: print them, so you can see the shape.
            exporter = ConsoleSpanExporter()

        provider.add_span_processor(BatchSpanProcessor(exporter))
        ot.set_tracer_provider(provider)
        _tracer = ot.get_tracer(SERVICE_NAME)
    except ImportError:
        _tracer = None      # packages not installed: carry on without it
    return _tracer


def tracer():
    if not _ready:
        _setup()
    return _tracer


class span:
    """A span, or a no-op if OTel is off. Use it as a context manager:

        with otel.span("tool", {"tool.name": "lookup_order"}):
            ...

    When OTel is disabled this does nothing at all - no imports, no cost.
    """

    def __init__(self, name, attributes=None):
        self.name = name
        self.attributes = attributes or {}
        self._cm = None
        self._span = None

    def __enter__(self):
        t = tracer()
        if t is None:
            return self
        self._cm = t.start_as_current_span(self.name)
        self._span = self._cm.__enter__()
        for k, v in self.attributes.items():
            self._span.set_attribute(k, v)
        return self

    def set(self, key, value):
        if self._span is not None and value is not None:
            self._span.set_attribute(key, value)
        return self

    def failed(self, message):
        if self._span is not None:
            from opentelemetry.trace import Status, StatusCode
            self._span.set_status(Status(StatusCode.ERROR, str(message)))
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._cm is None:
            return False
        if exc is not None:
            self.failed(exc)
        return self._cm.__exit__(exc_type, exc, tb)
