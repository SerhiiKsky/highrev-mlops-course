# Session 09 checklist

An ungraded self-check and the basis of the L09-E6 acceptance review. The
[final project rubric](../../FINAL_PROJECT_RUBRIC.md) governs project grading.

Inventory (E1)

- [ ] I can name each service and job, its image, the user it runs as, its ports and its mounts.
- [ ] I can say where the served model, the pointer, the MLflow runs and the monitoring reports live, and which of them a container could lose.

Running, live, ready (E2)

- [ ] I can show the difference between a running container, a live API and a ready API with one command each.
- [ ] The API's health check fails when no model is loaded and passes when one is.

Configuration and lifecycle (E3)

- [ ] `docker inspect` shows that the API mounts the folder I deploy into, and the API sees my model there.
- [ ] I know which of my changes recreated a container, and why Compose decided to.
- [ ] My one-off jobs never recreate a running service.

Monitoring in containers (E4)

- [ ] The Lab 08 cycle runs end to end in containers and ends with "served = scored".
- [ ] I can explain why the cycle first stopped, and why my repair does not depend on what a library prints.
- [ ] I found the cycle's MLflow run and its report after the job containers were gone.
- [ ] I can explain what `localhost` means inside a container.

Deploy and roll back (E5)

- [ ] I deployed a second model and rolled back without rebuilding an image, and measured the rollback.
- [ ] I verified which model serves by its identity, not by its predictions.
- [ ] A broken deploy was refused, the old model kept serving, and I restored the pointer.
- [ ] Serving state and MLflow runs survived `docker compose down` and `up`.

Handoff

- [ ] `compose.yaml`, `docker/`, `.dockerignore`, `scripts/cycle.sh`, `src/highrev/monitoring/track.py`, `lab07/lab07/live_api.py`, `.gitignore` and `notes/session-09.md` are committed; `serving/`, streams and reports are not.
