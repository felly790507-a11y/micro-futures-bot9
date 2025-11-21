"""
Python Solace Message Module (solmsg)
-------------------------------------

.. currentmodule:: pysolace.solmsg

.. autosummary::
    :toctree: _generate

    DestinationType
    DeliveryMode
    Destination
    SolMsg
"""
from enum import Enum
from typing import Any, Dict

class DestinationType(Enum):
    Null: 'DestinationType'
    Topic: 'DestinationType'
    Queue: 'DestinationType'
    TopicTemp: 'DestinationType'
    QueueTemp: 'DestinationType'

    def __int__(self) -> int: ...

class DeliveryMode(Enum):
    Direct: 'DeliveryMode'
    Persistent: 'DeliveryMode'
    NonPersistent: 'DeliveryMode'

    def __int__(self) -> int: ...

class Destination:
    dest_type: DestinationType
    dest: str

    def __init__(self, dest: str, dest_type: DestinationType = ...) -> None: ...

class SolMsg:
    def __init__(self) -> None: ...
    def __repr__(self) -> str: ...

    dest: Destination
    reply2: Destination
    is_reply: bool
    is_request: bool  # Readonly
    is_p2p: bool      # Readonly
    delivery_mode: DeliveryMode
    content_type: str
    elide: bool
    cos: int
    json: Dict[Any, Any]
    msgpack: Dict[Any, Any]
    body: bytes
