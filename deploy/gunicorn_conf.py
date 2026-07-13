"""Config do Gunicorn para a API do IALinkedyn (prod1)."""

bind = "127.0.0.1:8021"
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 60
graceful_timeout = 30
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = "info"
