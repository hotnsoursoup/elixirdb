"""
Validation Module for database models.

This module provides a validator function for validating any db_models
against a given database configuration. It uses Pydantic for validation and

"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Type
from pydantic import Field
from pydantic import ValidationError
from pydantic_core import InitErrorDetails
from typing_extensions import Annotated


if TYPE_CHECKING:
    from elixirdb.types import M


PositiveInt = Annotated[int, Field(gt=0)]
ConnectArgsType = dict[str, Any]
ExecutionOptionsType = dict[str, Any]
JsonDeserializerType = Callable[[str], Any]
JsonSerializerType = Callable[[Any], str]
PluginListType = list[str]


def model_validator(db_config: dict[str, Any], models: list[Type[M]]) -> M | None:
    """
    Validates the given database configuration against a list of models.

    Args:
        config: The config to validate against the models.
        models: A list of model classes to validate against.

    Returns:
        The validated model instance or None if validation fails.
    """
    errors = []

    def validate_model(model_class: Type[M]) -> M | None:
        try:
            return model_class(**db_config)
        except ValidationError as e:
            errors.append(e.errors())
            return None

    for model in models:
        validated_model = validate_model(model)
        if validated_model:
            return validated_model
    if errors:
        raise ValidationError([InitErrorDetails(err) for err in errors])
