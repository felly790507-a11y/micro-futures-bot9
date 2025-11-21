import typing
from enum import Enum
from pydantic import (
    BaseModel,
    conint,
    StrictInt,
    constr,
)

# _missing = object()


class BaseModelV10(BaseModel):
    def __repr_args__(self):
        return [(k, v) for k, v in self._iter(to_dict=False, exclude_defaults=True)]

    def _iter(
        self,
        to_dict: bool = False,
        by_alias: bool = False,
        allowed_keys: typing.Optional["SetStr"] = None,
        include: typing.Union["AbstractSetIntStr", "DictIntStrAny"] = None,
        exclude: typing.Union["AbstractSetIntStr", "DictIntStrAny"] = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        # exclude_none: bool = False,
    ):
        if not to_dict:
            if allowed_keys is None:
                allowed_keys = set(self.__fields__)
            if exclude:
                for k in exclude:
                    allowed_keys.discard(k)
        return super()._iter(
            to_dict,
            by_alias,
            allowed_keys,
            include,
            exclude,
            exclude_unset,
            exclude_defaults,
            # exclude_none,
        )

    @classmethod
    def _get_value(
        cls,
        v: typing.Any,
        to_dict: bool,
        by_alias: bool,
        include: typing.Optional[typing.Union["AbstractSetIntStr", "DictIntStrAny"]],
        exclude: typing.Optional[typing.Union["AbstractSetIntStr", "DictIntStrAny"]],
        exclude_unset: bool,
        exclude_defaults: bool,
        # exclude_none: bool,
    ) -> typing.Any:
        if to_dict and isinstance(v, Enum):
            return v.value
        return super()._get_value(
            v,
            to_dict,
            by_alias,
            include,
            exclude,
            exclude_unset,
            exclude_defaults,
            # exclude_none,
        )

    def keys(self) -> typing.List[typing.Any]:
        return self._calculate_keys(include=None, exclude=None, exclude_unset=True)

    def __getitem__(self, key: typing.Any) -> typing.Any:
        return self._get_value(
            self.__dict__[key],
            to_dict=True,
            by_alias=False,
            include=None,
            exclude=None,
            exclude_unset=True,
            exclude_defaults=True,
            # exclude_none=True,
        )

    def lazy_setter(self, **kwargs):
        [
            setattr(self, kwarg, value)
            for kwarg, value in kwargs.items()
            if hasattr(self, kwarg)
        ]

    def model_dump(self):
        return self.dict()

class BaseModelV15(BaseModel):
    def __repr_args__(self):
        return [(k, v) for k, v in self._iter(to_dict=False, exclude_defaults=True)]

    @classmethod
    def _get_value(
        cls,
        v: typing.Any,
        to_dict: bool,
        by_alias: bool,
        include: typing.Optional[typing.Union["AbstractSetIntStr", "DictIntStrAny"]],
        exclude: typing.Optional[typing.Union["AbstractSetIntStr", "DictIntStrAny"]],
        exclude_unset: bool,
        exclude_defaults: bool,
        exclude_none: bool,
    ) -> typing.Any:
        if to_dict and isinstance(v, Enum):
            return v.value
        return super()._get_value(
            v,
            to_dict,
            by_alias,
            include,
            exclude,
            exclude_unset,
            exclude_defaults,
            exclude_none,
        )

    def keys(self) -> typing.List[typing.Any]:
        return self._calculate_keys(include=None, exclude=None, exclude_unset=True)

    def __getitem__(self, key: typing.Any) -> typing.Any:
        return self._get_value(
            self.__dict__[key],
            to_dict=True,
            by_alias=False,
            include=None,
            exclude=None,
            exclude_unset=True,
            exclude_defaults=True,
            exclude_none=True,
        )

    def lazy_setter(self, **kwargs):
        [
            setattr(self, kwarg, value)
            for kwarg, value in kwargs.items()
            if hasattr(self, kwarg)
        ]

    def model_dump(self):
        return self.dict()

class BaseModelV20(BaseModel):
    __json__: dict = {}

    def __repr_args__(self):
        return [
            (k, getattr(self, k))
            for k, v in self.model_dump(exclude_defaults=True).items()
        ]

    def keys(self) -> typing.Set[str]:  # typing.List[typing.Any]:
        if not self.__json__:
            self.__json__ = self.model_dump(
                mode="json",
                by_alias=False,
                include=None,
                exclude=None,
                exclude_unset=True,
                exclude_defaults=True,
                exclude_none=True,
            )
        return self.__json__.keys()

    def __getitem__(self, key: str) -> typing.Any:
        if not self.__json__:
            self.__json__ = self.model_dump(
                mode="json",
                by_alias=False,
                include=None,
                exclude=None,
                exclude_unset=True,
                exclude_defaults=True,
                exclude_none=True,
            )
        return self.__json__[key]

    def lazy_setter(self, **kwargs):
        [
            setattr(self, kwarg, value)
            for kwarg, value in kwargs.items()
            if hasattr(self, kwarg)
        ]

    def _clean_cache(self):
        if self.__json__:
            object.__setattr__(self, "__json__", {})

    def __setattr__(self, name: str, value: typing.Any) -> None:
        self._clean_cache()
        return super().__setattr__(name, value)

    def dict(self):
        return self.model_dump(
            mode="json",
            include=None,
            exclude=None,
            by_alias=False,
            exclude_unset=False,
            exclude_defaults=False,
            exclude_none=True,
        )


class MetaProps(type):
    def __repr__(cls):
        attrs = [attr for attr in cls.__dict__ if not attr.startswith("_")]
        display_name = cls.__name__ if not cls.__name__.startswith("_") else ""
        return "{}({})".format(display_name, (", ").join(attrs))


class BaseProps(metaclass=MetaProps):
    pass


from importlib_metadata import version

if version("pydantic") >= "2.0":
    BaseModel = BaseModelV20
    ConStrAsciiMax6 = constr(max_length=6, pattern="^[ -~]*$")
elif version("pydantic") > "1.0":
    BaseModel = BaseModelV15
    ConStrAsciiMax6 = constr(max_length=6, regex="^[ -~]*$")
else:
    BaseModel = BaseModelV10
    ConStrAsciiMax6 = constr(max_length=6, regex="^[ -~]*$")
