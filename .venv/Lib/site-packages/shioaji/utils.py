import os
import logging
import datetime as dt
from pathlib import Path
import sentry_sdk
from sentry_sdk.integrations.logging import SentryHandler

from pysolace import SolClient
from shioaji.error import TokenError, SystemMaintenance
from shioaji._version import __version__

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
SENTRY_URI = os.environ.get(
    "SENTRY_URI", "https://6aec6ef8db7148aa979a17453c0e44dd@sentry.io/1371618"
)
LOG_SENTRY = os.environ.get("LOG_SENTRY", "True")
SENTRY_LOG_LEVEL = os.environ.get("SENTRY_LOG_LEVEL", "ERROR").upper()
SJ_LOG_PATH = os.environ.get("SJ_LOG_PATH", "shioaji.log")
LEGACY_TEST = int(os.environ.get("LEGACY_TEST", 0))

allow_log_level = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
assert LOG_LEVEL in allow_log_level, "LOG_LEVEL not allow, choice {}".format(
    (", ").join(allow_log_level)
)
LOGGING_LEVEL = getattr(logging, LOG_LEVEL)

log = logging.getLogger("shioaji")
log.setLevel(LOGGING_LEVEL)

console_handler = logging.FileHandler(SJ_LOG_PATH)
console_handler.setLevel(LOGGING_LEVEL)
log_formatter = logging.Formatter(
    "[%(levelname)1.1s %(asctime)s %(pathname)s:%(lineno)d:%(funcName)s] %(message)s"
)
console_handler.setFormatter(log_formatter)
log.addHandler(console_handler)


def set_error_tracking(simulation: bool, error_tracking: bool):
    if LOG_SENTRY and not simulation and error_tracking:
        sentry_sdk.init(SENTRY_URI)
        sentry_handeler = SentryHandler()
        sentry_handeler.setLevel(SENTRY_LOG_LEVEL)
        sentry_handeler.setFormatter(log_formatter)
        log.addHandler(sentry_handeler)


def raise_resp_error(status_code: int, resp: dict, session: SolClient):
    log.error(resp)
    detail = resp.get("response", {}).get("detail", "")
    if status_code == 401:
        session.disconnect()
        raise TokenError(status_code, detail)
    elif status_code == 503:
        raise SystemMaintenance(status_code, detail)
    else:
        raise Exception(resp)


def clear_outdated_contract_cache(contract_path: Path, keep_days: int = 3):
    contract_dir = contract_path.parent
    utcnow = dt.datetime.utcnow()
    try:
        for file_path in contract_dir.iterdir():
            if file_path.suffix not in [".pkl", ".lock"]:
                continue
            if not file_path.name.startswith("contract"):
                continue
            file_datetime = dt.datetime.utcfromtimestamp(file_path.stat().st_mtime)
            if (utcnow - file_datetime).days > keep_days:
                file_path.unlink()
    except Exception as e:
        log.error("contract cache remove error | {}".format(e))


def check_contract_cache(contract_path: Path) -> bool:
    """check contract cache exists and is up-to-date.
    Contracts will be update at 8 am and 2 pm.
    Returns:
        bool: True if cache exists and is up-to-date, else False.
    """
    if contract_path.exists():
        contract_file_datetime = dt.datetime.utcfromtimestamp(
            contract_path.stat().st_mtime
        )
        utcnow = dt.datetime.utcnow()
        pm_target_time = dt.datetime.combine(dt.datetime.now().date(), dt.time(6, 45))
        if utcnow.date() > contract_file_datetime.date():
            return False
        elif utcnow >= pm_target_time:
            if contract_file_datetime < pm_target_time:
                return False
        return True
    else:
        return False
