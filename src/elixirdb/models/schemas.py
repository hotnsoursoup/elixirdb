from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from pydantic_core import core_schema
from sqlalchemy.engine import Engine


if TYPE_CHECKING:
    from pydantic.json_schema import JsonSchemaValue


ConnectArgsType = dict[str, Any]
ExecutionOptionsType = dict[str, Any]
JsonDeserializerType = Callable[[str], Any]
JsonSerializerType = Callable[[Any], str]
PluginListType = list[str]


class EngineSchema:
    @classmethod
    def __get_pydantic_core_schema__(  # noqa: PLW3201
        cls,
        source_type: type[Engine],
        handler: Callable[[type[Any]], core_schema.CoreSchema],
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, v: Any) -> Engine:
        if not isinstance(v, Engine):
            raise TypeError("value is not an Engine instance")
        return v

    @classmethod
    def __get_pydantic_json_schema__(  # noqa: PLW3201
        cls,
        schema: core_schema.CoreSchema,
        handler: Callable[[core_schema.CoreSchema], JsonSchemaValue],
    ) -> JsonSchemaValue:
        return {
            "type": "sqlalchemy.engine.Engine",
            "title": "Engine",
            "description": "SQLAlchemy Engine object as a string",
            "examples": ["Engine(postgresql//user:pass@localhost/dbname)"],
        }


class CallableSchema:
    @classmethod
    def __get_pydantic_core_schema__(  # noqa: PLW3201
        cls,
        source_type: Callable,
        handler: Callable[[type[Any]], core_schema.CoreSchema],
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, v: Any) -> Callable:
        if not callable(v):
            raise TypeError("value is not a callable")
        return v

    @classmethod
    def __get_pydantic_json_schema__(  # noqa: PLW3201
        cls,
        schema: core_schema.CoreSchema,
        handler: Callable[[core_schema.CoreSchema], JsonSchemaValue],
    ) -> JsonSchemaValue:
        return {
            "type": "callable",
            "title": "Callable",
            "description": "Callable object as a string",
            "examples": ["Callable(lambda x: x + 1)"],
        }
