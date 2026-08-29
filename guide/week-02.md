# Guide Week 2 · Deploy

**Goal:** put the container online on Cloud Run, then move memory to Redis so it
survives updates.

## The idea

Cloud Run gives your container a public address and throws the container away on
every update. If memory lives inside the container, it dies. So you move it to
Redis, which sits outside and stays put. You only swap the inside of `load` and
`save`; nothing else changes.

## Do this

1. Deploy by hand once (see the curriculum for the exact `gcloud` commands).
2. Watch memory break: say your name, redeploy, ask your name. It forgot.
3. Turn on Redis by setting `REDIS_URL` in your environment. The Redis path is
   already in `app/memory.py`.
4. Deploy again. Now it remembers.

Test the Redis path locally without the cloud:

```bash
docker run -d -p 6379:6379 --name dev-redis redis:7-alpine
export REDIS_URL=redis://localhost:6379
make run
```

## Check it works

```bash
make check-week-02
```

## Done when

- A public address answers `/chat`.
- A conversation survives an update.

**Pull request:** `week-02-<your-name>`, `week 02: deploy and move memory out`.
