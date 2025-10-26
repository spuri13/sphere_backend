import multiprocessing

# Worker configuration
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000

# Timeout configuration (3 minutes to handle long AI API calls)
timeout = 180
graceful_timeout = 180
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "studysphere-backend"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Server hooks
def on_starting(server):
    print("="*60)
    print("StudySphere Backend Starting")
    print(f"Workers: {workers}")
    print(f"Timeout: {timeout}s")
    print("="*60)

def worker_exit(server, worker):
    print(f"Worker {worker.pid} exited")

def worker_abort(worker):
    print(f"Worker {worker.pid} aborted - likely due to timeout")