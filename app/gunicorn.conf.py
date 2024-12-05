import multiprocessing 

# Gunicorn configuration
bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1
timeout = 120
keepalive = 5
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# SSL (if needed)
# keyfile = "path/to/keyfile"
# certfile = "path/to/certfile"

# Worker process name
proc_name = "ai_rekruter"

# Environment variables
raw_env = [
    f"FLASK_APP=app:app",
    f"FLASK_ENV=production",
]

# Preload application code before worker processes are forked
preload_app = True 