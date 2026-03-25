---
sidebar_position: 99
---

# Contributing

Thanks for your interest in contributing to RealCRM! See our full [CONTRIBUTING.md](https://github.com/sneg55/pingcrm/blob/main/CONTRIBUTING.md) for detailed instructions.

## Quick Start

1. Fork and clone the repo
2. Start PostgreSQL and Redis: `docker-compose up -d db redis`
3. Backend: `cd backend && pip install -r requirements.txt && alembic upgrade head && uvicorn app.main:app --reload`
4. Frontend: `cd frontend && npm install && npm run dev`
5. Run tests: `cd backend && pytest` / `cd frontend && npm test`

## Pull Request Process

1. Fork the repo and create a branch from `main`
2. Make your changes with tests
3. Ensure all tests pass
4. Submit a PR with a clear description

## Code Style

- **Python:** snake_case, type hints, async where appropriate
- **TypeScript:** camelCase for variables/functions, PascalCase for components

See [CLAUDE.md](https://github.com/sneg55/pingcrm/blob/main/CLAUDE.md) for the full conventions guide.
