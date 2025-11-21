"""
Python Solace Client Core (_core)
---------------------------------

.. currentmodule:: pysolace._core

.. autosummary::
    :toctree: _generate

    client
    connect
    set_callback
    set_p2p_callback
    set_event_callback
    set_session_down_callback
    set_reply_callback
    set_onreply_callback
    publish
    publish_raw
    publish_multi_raw
    request
    reply
    subscribe
    unsubscribe
    get_msg_queue_size
    disconnect
    set_client_name
    _del
    SolLogLevel
    SolReturnCode
"""
from enum import Enum
from typing import Any, Callable, Dict, List, Tuple, Optional

__version__: str

class SolLogLevel(Enum):
    SOLCLIENT_LOG_EMERGENCY: 'SolLogLevel'
    SOLCLIENT_LOG_ALERT: 'SolLogLevel'
    SOLCLIENT_LOG_CRITICAL: 'SolLogLevel'
    SOLCLIENT_LOG_ERROR: 'SolLogLevel'
    SOLCLIENT_LOG_WARNING: 'SolLogLevel'
    SOLCLIENT_LOG_NOTICE: 'SolLogLevel'
    SOLCLIENT_LOG_INFO: 'SolLogLevel'
    SOLCLIENT_LOG_DEBUG: 'SolLogLevel'

    def __int__(self, value: int) -> SolLogLevel: ...

class SolReturnCode(Enum):
    SOLCLIENT_OK: 'SolReturnCode'
    SOLCLIENT_WOULD_BLOCK: 'SolReturnCode'
    SOLCLIENT_IN_PROGRESS: 'SolReturnCode'
    SOLCLIENT_NOT_READY: 'SolReturnCode'
    SOLCLIENT_EOS: 'SolReturnCode'
    SOLCLIENT_NOT_FOUND: 'SolReturnCode'
    SOLCLIENT_NOEVENT: 'SolReturnCode'
    SOLCLIENT_INCOMPLETE: 'SolReturnCode'
    SOLCLIENT_ROLLBACK: 'SolReturnCode'
    SOLCLIENT_FAIL: 'SolReturnCode'

    def __int__(self, value: int) -> SolReturnCode: ...

def client(log_level: SolLogLevel = ..., debug: bool = ...) -> int: ...

def connect(
    sol: int,
    host: str,
    vpn: str,
    user: str,
    pass_param: str,
    clientname: str = ...,
    connect_timeout_ms: int = ...,
    reconnect_retries: int = ...,
    keep_alive_ms: int = ...,
    reconnect_retry_wait: int = ...,
    keep_alive_limit: int = ...
) -> int: ...

def set_callback(sol: int, func: Optional[Callable[[str, Any], int]]) -> None: ...
def set_p2p_callback(sol: int, func: Optional[Callable[[str, Dict[Any, Any]], None]]) -> None: ...
def set_event_callback(sol: int, func: Optional[Callable[[Any, Any, str, str], None]]) -> None: ...
def set_session_down_callback(sol: int, func: Optional[Callable[[], None]]) -> None: ...
def set_reply_callback(sol: int, func: Optional[Callable[[str, Dict[Any, Any], Dict[Any, Any]], Tuple[Any, ...]]]) -> None: ...
def set_onreply_callback(sol: int, func: Optional[Callable[[str, str, Dict[Any, Any]], int]]) -> None: ...

def publish(sol: int, topic: str, msg_dict: Dict[Any, Any], format: str, cos: int) -> SolReturnCode: ...
def publish_raw(sol: int, topic: str, content_type: str, buf_p: bytes, cos: int) -> SolReturnCode: ...
def publish_multi_raw(sol: int, msgs: List[Tuple[str, bytes]], content_type: str, cos: int) -> SolReturnCode: ...

def request(sol: int, topic: str, correlationid: str, request_payload: Dict[Any, Any], timeout: int, cos: int, format: str) -> Dict[Any, Any]: ...

def reply(sol: int, topic: str, header: Dict[Any, Any], body: Dict[Any, Any]) -> int: ...

def subscribe(sol: int, topic: str) -> None: ...
def unsubscribe(sol: int, topic: str) -> None: ...

def get_msg_queue_size(sol: int) -> int: ...
def disconnect(sol: int) -> int: ...
def set_client_name(sol: int, clientname: str) -> bool: ...
def _del(sol: int) -> None: ...
