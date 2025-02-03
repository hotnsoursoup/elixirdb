"Metadata updator for Pydantic models."
# pylint: disable=C0301
# flake8: noqa E501
# ruff: noqa: E501

from pydantic import Field


def update_model_meta(metadata_dict: dict):
    """
    Updates the fields of a Pydantic model class with metadata from
    a dictionary.

    Args:
        cls (BaseModel): A Pydantic model class.
        metadata_dict (dict): A dictionary containing field metadata,
            where each key is a field name and each value is a
            dictionary of metadata.
    """

    def decorator(cls):
        for field_name, metadata in metadata_dict.items():
            if field_name in cls.model_fields:
                cls.model_fields[field_name] = Field(
                    title=metadata.get("title"),
                    description=metadata.get("description"),
                    json_schema_extra={"example": metadata.get("example")},
                )
        cls.model_rebuild()
        return cls

    return decorator
