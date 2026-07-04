.PHONY: start-frontend-dev start-backend-dev start-frontend

# Runs backend (with reload) and frontend (Vite dev server) together.
# Ctrl+C stops both.
start-frontend-dev:
	@trap 'kill 0' EXIT INT TERM; \
	$(MAKE) start-backend-dev < /dev/null & \
	$(MAKE) start-frontend < /dev/null & \
	wait

start-backend-dev:
	python3 scripts/run_detached.py uv run fastapi dev backend/main.py --port 8000 --reload-dir backend < /dev/null

start-frontend:
	cd frontend && npm run dev < /dev/null
