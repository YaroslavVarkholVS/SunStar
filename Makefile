.PHONY: start-frontend-dev start-backend-dev start-frontend \
        stop-frontend-dev stop-backend-dev stop-frontend

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

stop-frontend-dev:
	@$(MAKE) stop-backend-dev < /dev/null & \
	$(MAKE) stop-frontend < /dev/null & \
	wait

stop-backend-dev:
	@lsof -ti :8000 | xargs -r kill

stop-frontend:
	@pkill -f "vite"