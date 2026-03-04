.PHONY: install dev backend frontend init-db import-jcr lint typecheck

install:
	cd backend && python -m venv .venv && .venv/bin/pip install -r requirements.txt
	cd frontend && npm install

dev:
	@echo "Iniciando backend y frontend..."
	@tmux new-session -d -s cecan-backend "cd backend && .venv/bin/uvicorn main:app --reload --port 8000" 2>/dev/null || true
	@tmux new-session -d -s cecan-frontend "cd frontend && npm run dev" 2>/dev/null || true
	@echo "Backend: http://localhost:8000/docs"
	@echo "Frontend: http://localhost:5173"
	@echo "Para ver logs: tmux attach -t cecan-backend | cecan-frontend"

backend:
	cd backend && .venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

init-db:
	cd backend && .venv/bin/alembic upgrade head

import-jcr:
	@echo "Uso: make import-jcr FILE=data/jcr_update.xlsx"
	cd backend && .venv/bin/python ../scripts/import_jcr.py --file $(FILE)

lint:
	cd frontend && npm run lint

typecheck:
	cd frontend && npm run type-check

kill:
	@tmux kill-session -t cecan-backend 2>/dev/null || true
	@tmux kill-session -t cecan-frontend 2>/dev/null || true
