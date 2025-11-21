import os

SOL_CONNECT_TIMEOUT_MS = int(
    os.environ.get("SOL_CONNECT_TIMEOUT_MS", 3000)
)
SOL_RECONNECT_RETRIES = int(
    os.environ.get("SOL_RECONNECT_RETRIES", 10)
)
SOL_KEEP_ALIVE_MS = int(os.environ.get("SOL_KEEP_ALIVE_MS", 3000))
SOL_RECONNECT_RETRY_WAIT = int(
    os.environ.get("SOL_RECONNECT_RETRY_WAIT", 3000)
)
SOL_KEEP_ALIVE_LIMIT = int(os.environ.get("SOL_KEEP_ALIVE_LIMIT", 3))
