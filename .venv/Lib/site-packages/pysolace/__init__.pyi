"""
Python client library for Solace PubSub+ event broker, enabling easy integration for messaging applications.
-----------------------

.. currentmodule:: pysolace

.. autosummary::
    :toctree: _generate

    SolClient
    SolLogLevel
    SolReturnCode
    run
    main
    DestinationType
    DeliveryMode
    Destination
    SolMsg
"""

from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Tuple

__version__: str
__doc__: str

class SolLogLevel:
    SOLCLIENT_LOG_CRIT: SolLogLevel = ...
    SOLCLIENT_LOG_ERROR: SolLogLevel = ...
    SOLCLIENT_LOG_WARNING: SolLogLevel = ...
    SOLCLIENT_LOG_NOTICE: SolLogLevel = ...
    SOLCLIENT_LOG_INFO: SolLogLevel = ...
    SOLCLIENT_LOG_DEBUG: SolLogLevel = ...

class SolReturnCode:
    SOLCLIENT_OK: SolReturnCode = ...
    SOLCLIENT_WOULD_BLOCK: SolReturnCode = ...
    SOLCLIENT_IN_PROGRESS: SolReturnCode = ...
    SOLCLIENT_NOT_READY: SolReturnCode = ...
    SOLCLIENT_EOF: SolReturnCode = ...
    SOLCLIENT_FAIL: SolReturnCode = ...
    # Add other specific return codes if known and used in the interface

class SolClient:
    def __init__(
        self,
        log_level: SolLogLevel = ...,
        debug: bool = False,
    ) -> None: ...
    def connect(
        self,
        host: str,
        vpn: str,
        user: str,
        password: str,
        clientname: str = "",
        connect_timeout_ms: int = 3000,
        reconnect_retries: int = 10,
        keep_alive_ms: int = 3000,
        reconnect_retry_wait: int = 3000,
        keep_alive_limit: int = 3,
    ) -> SolReturnCode: ...
    def set_client_name(self, clientname: str) -> int: ... # Assuming 0 for success, 1 for failure or similar int code
    def get_client_name(self) -> str: ...
    def subscribe(self, topic: str) -> None: ...
    def unsubscribe(self, topic: str) -> None: ...
    def publish(
        self, topic: str, msg: Dict[Any, Any], format: str = "msgpack", cos: int = 1
    ) -> SolReturnCode: ...
    def publish_raw(
        self, topic: str, content_type: str, buf: bytes, cos: int = 1
    ) -> SolReturnCode: ...
    def publish_multi_raw(
        self,
        msgs: List[Tuple[str, bytes]],
        content_type: str,
        cos: int = 1,
    ) -> SolReturnCode: ...
    def request(
        self,
        topic: str,
        payload: Dict[Any, Any],
        corrid: str = "",
        timeout: int = 5000,
        cos: int = 1,
        format: str = "msgpack",
        cb: Optional[Callable[[str, str, Dict[Any, Any]], int]] = None,
    ) -> Dict[Any, Any]: ...
    def reply(self, topic: str, header: Dict[Any, Any], body: Dict[Any, Any]) -> SolReturnCode: ...
    def get_msg_queue_size(self) -> int: ...
    def set_session(self, token: str) -> None: ...
    def set_msg_callback(self, callback_func: Callable[[str, Dict[Any, Any]], Any]) -> None: ...
    def set_event_callback(self, callback_func: Callable[[int, int, str, str], None]) -> None: ...
    def set_session_down_callback(self, callback_func: Callable[[], None]) -> None: ...
    def set_p2p_callback(self, func: Callable[[str, Dict[Any, Any]], None]) -> None: ...
    def set_reply_callback(
        self,
        callable_func: Callable[
            [str, Dict[Any, Any], Dict[Any, Any]], Tuple[int, Dict[Any, Any]]
        ],
    ) -> None: ...
    def set_onreply_callback(
        self, callable_func: Callable[[str, str, Dict[Any, Any]], Any]
    ) -> None: ...
    def disconnect(self) -> None: ...
    def cleanup(self) -> None: ...
    def __del__(self) -> None: ...

def run(
    host: str,
    vpn: str,
    user: str,
    password: str,
    clientname: str = "",
    connect_timeout_ms: int = 3000,
    reconnect_retries: int = 10,
    keep_alive_ms: int = 3000,
    reconnect_retry_wait: int = 3000,
    keep_alive_limit: int = 3,
    mode: str = "sub",
    topic: str = "",
) -> None: ...

def main() -> None: ...

__all__: List[str]
