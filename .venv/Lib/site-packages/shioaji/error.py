from shioaji.base import BaseModel
from shioaji.account import Account
from shioaji.contracts import Contract


class BaseError(Exception):
    def __init__(self, code, message):
        formated_mes = "StatusCode: {}, Detail: {}".format(code, message)
        super().__init__(formated_mes)
        self.code = code
        self.message = message


class TokenError(BaseError):
    """Raise when token error."""


class SystemMaintenance(BaseError):
    """Raise when system maintenance an error."""


class TimeoutError(BaseError):
    """Timeout Error"""

    def __init__(self, topic: str, extra_info: dict):
        formated_mes = "Timeout 408 Topic: {}, ExtraInfo: {}".format(topic, extra_info)
        super().__init__("408", formated_mes)
        self.topic = topic
        self.extra_info = extra_info


class AccountError(Exception):
    """Account Error"""

    def __init__(self, account: Account):
        message = "{} Account({})".format(self.__class__.__name__, account)
        super().__init__(message)
        self.account = account


class AccountNotSignError(AccountError):
    """Account not sign"""

    def __init__(self, account: Account):
        super().__init__(account)


class AccountNotProvideError(ValueError):
    """Account not provide"""


class ContractError(Exception):
    """Contract Error"""

    def __init__(self, contract: Contract, message: str):
        self.contract = contract
        message = "Contract({})\n{}".format(contract, message)
        super().__init__(message)


class TargetContractNotExistError(ContractError):
    """Target Contract Not Exist Error"""

    def __init__(self, contract: Contract):
        message = "please update contracts with command `api.fetch_contracts(contract_download=True)`."
        super().__init__(contract, message)

class CaError(ValueError):
    pass