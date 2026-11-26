# Lab 09 optional challenges

Do these only after L09-E6, on a repaired and committed system. Each challenge breaks
one thing on purpose. Record it as an extra row of your incident table (Observe →
Prevent), then restore the committed file with `git checkout -- <file>` and recreate
the affected service. They are not graded.

## C1 — A job that cannot read its own data

**Break:** in `compose.yaml`, delete the line `user: "0:0"` from the `ag` service. Then
run the cycle for an incident you have not simulated yet:

```bash
bash scripts/cycle.sh covariate      # uses the run you exported in Before class
```

**Questions:** which stage fails, and with which error? Run
`ls -ld data/05_serving/lab09/covariate` on your machine, then the same inside a
container:

```bash
docker compose run --rm -T --no-deps --entrypoint sh ag -c 'id; ls -ld ../data/05_serving/lab09/covariate'
```

Which user created the folder, which user tried to read it, and which permissions
does the folder have *inside* the container? Why does your machine's view not show
the problem? Name two repairs other than `chmod -R 777`.

**Restore:** `git checkout -- compose.yaml`. Remove the stream only if you created
it in this challenge.

## C2 — A health check that never succeeds

**Break:** in the `api` health check, change the port `10000` to `8007`, then
`docker compose up -d api`.

**Questions:** `curl http://127.0.0.1:8007/ready` from your machine answers 200, yet
the container turns unhealthy. Why does the same port work from your machine and
fail inside the container? What does
`docker inspect --format '{{json .State.Health}}' highrev-api-1` report, and why
does the API log show no request at all? Compare with a wrong path (`/readyz`):
which of the two leaves a trace in `docker compose logs api`?

**Restore:** `git checkout -- compose.yaml`, `docker compose up -d api`.

## C3 — Refuse to start without a model

**Break:** add `STRICT_STARTUP: "1"` to the `api` service's `environment`, empty the
pointer (`mv serving/current.json serving/current.json.off`), and
`docker compose up -d api`.

**Questions:** what does `docker compose ps` show over a minute, and why is the
container never simply "exited"? Where is the cause now: in `/health` or in
`docker compose logs api`? Run the same image with `docker run` (no restart
policy) and compare. When would you choose strict startup for a real service, and
what does it cost?

**Restore:** `mv serving/current.json.off serving/current.json`,
`git checkout -- compose.yaml`, `docker compose up -d api`.
