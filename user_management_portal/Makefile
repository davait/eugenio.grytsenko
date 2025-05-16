# Makefile for User Management Portal

.PHONY: clean clean-backend clean-frontend

clean: clean-backend clean-frontend
	@echo "Project cleaned."

clean-backend:
	cd backend && \
	find . -type d -name '__pycache__' -exec rm -rf {} + && \
	find . -type d -name '.pytest_cache' -exec rm -rf {} + && \
	find . -type d -name '.mypy_cache' -exec rm -rf {} + && \
	find . -type d -name '.cache' -exec rm -rf {} + && \
	find . -type d -name '.coverage' -exec rm -rf {} + && \
	find . -name '*.pyc' -delete && \
	rm -rf .pytest_cache .mypy_cache .cache .coverage
	@echo "Backend cleaned."

clean-frontend:
	cd frontend 2>/dev/null && \
	rm -rf node_modules .next .cache dist build coverage || true
	@echo "Frontend cleaned (if exists)."
