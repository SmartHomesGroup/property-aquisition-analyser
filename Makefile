# Developer entry points. See AGENTS.md for the architecture and backend/README.md for the pipeline.

.PHONY: up down logs api web check test build-data

up:            ## start PostGIS + Martin
	docker compose -f infra/docker-compose.yml up -d

down:          ## stop them (data volume kept)
	docker compose -f infra/docker-compose.yml down

logs:
	docker compose -f infra/docker-compose.yml logs -f

api:           ## run the API locally with reload
	cd backend && uv run paa serve --reload

web:           ## run the SvelteKit dev server
	cd web && npm run dev

check:         ## lint + types, both halves
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy
	cd web && npm run lint && npm run check

test:
	cd backend && uv run pytest -q
	cd web && npm test

build-data:    ## rebuild derived tables after loading sources, then restart Martin
	cd backend && uv run paa build
	docker compose -f infra/docker-compose.yml restart tiles

shot:          ## screenshot the dev server: make shot OUT=/tmp/x.png ARGS='--type "#postcode=N11 2AB" --click "button[type=submit]"'
	node tools/shot.mjs http://127.0.0.1:5173/ $(OUT) $(ARGS)

help:
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'
