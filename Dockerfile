# Dockerfile - Week 01. BUILD THIS FILE.
#
# Package the service so it runs identically on your laptop and in the cloud.
# "Works on my machine" is not a deployment.
#
# What you need:
#
#   1. FROM python:3.12-slim
#      Slim, not full: a smaller image pulls faster on every cold start, and
#      carries fewer packages that could have a CVE.
#
#   2. WORKDIR /app
#
#   3. COPY requirements.txt .   THEN   RUN pip install -r requirements.txt
#      THEN   COPY . .
#
#      The order matters and it is the classic mistake. Docker caches each
#      layer and invalidates everything after the first change. Copy your code
#      first and every one-character edit reinstalls every dependency - turning
#      a 3-second rebuild into a 3-minute one. Use --no-cache-dir while you are
#      at it; a pip cache inside an image is dead weight.
#
#   4. ENV PORT=8080  and  EXPOSE 8080
#
#   5. CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
#
#      Three details in one line:
#        --host 0.0.0.0   bind all interfaces. The default 127.0.0.1 only
#                         accepts connections from inside the container, so
#                         the platform's health check can never reach you.
#        ${PORT}          every container platform tells your service where to
#                         listen through an env var. Hardcode it and you have
#                         a service that works locally and fails on deploy.
#        exec             replaces the shell with uvicorn as PID 1, so a
#                         shutdown signal reaches your process instead of the
#                         shell that ignores it. Without it, the platform waits
#                         out its grace period and then kills you - a slow,
#                         ugly deploy every time.
#
# Also write a .dockerignore. Without one you copy .venv/, .git/ and every
# __pycache__ into the image - and, worse, .env. Never bake a secret into an
# image layer: layers are cached, shared between builds, and pushed to
# registries where more people can read them than you think.
#
# Done when:  make check-week-01
#             make docker-build && make docker-run
#
# Stuck? git diff week-01-package..week-01-solution -- Dockerfile
