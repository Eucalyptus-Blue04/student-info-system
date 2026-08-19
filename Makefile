.PHONY: help install run test lint docker-up docker-down migrate

help: ## 显示帮助信息
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## 安装依赖
	pip install -r requirements.txt

run: ## 运行开发服务器
	python app.py

test: ## 运行测试
	pytest

test-cov: ## 运行测试并生成覆盖率报告
	pytest --cov=. --cov-report=html

lint: ## 代码检查
	pylint *.py

docker-up: ## 启动Docker容器
	docker-compose up -d --build

docker-down: ## 停止Docker容器
	docker-compose down

docker-logs: ## 查看Docker日志
	docker-compose logs -f

migrate: ## 初始化数据库迁移
	flask db init
	flask db migrate -m "Initial migration"
	flask db upgrade

migrate-upgrade: ## 执行数据库迁移
	flask db upgrade

migrate-downgrade: ## 回滚数据库迁移
	flask db downgrade

init-db: ## 初始化数据库
	python reset_db.py

init-admin: ## 初始化管理员账户
	python init_admin.py

init-data: ## 初始化测试数据
	python test_data.py

celery-worker: ## 启动Celery Worker
	celery -A tasks.celery worker --loglevel=info

celery-beat: ## 启动Celery Beat
	celery -A tasks.celery beat --loglevel=info

redis-start: ## 启动Redis
	redis-server

clean: ## 清理缓存文件
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage