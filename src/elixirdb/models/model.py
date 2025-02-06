"""
Base Models
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict


class StrictModel(BaseModel):
    """
    Set the default configuration for the BaseModel
    """

    # We allow here because we want to provide the validation error at the end
    model_config = ConfigDict(
        extra="forbid",
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )
