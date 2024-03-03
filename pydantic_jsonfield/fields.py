import json
from json import JSONEncoder

from django.core.exceptions import ValidationError
from django.db import models
from pydantic import BaseModel, ValidationError as PydanticValidationError

from example_app.forms import PydanticJSONFormField


class PydanticJSONFieldDescriptor:
    """Descriptor for PydanticJSONField to ensure that the value is always a Pydantic model instance."""

    def __init__(self, field):
        self.field = field

    def __get__(self, instance, owner):
        if instance is None:
            return self.field
        value = instance.__dict__.get(self.field.name)
        if isinstance(value, dict):
            # Convert dict to the correct python format when accessed
            value = self.field.to_python(value)
            instance.__dict__[self.field.name] = value
        return value

    def __set__(self, instance, value):
        if not isinstance(value, self.field.pydantic_model):
            # Convert value to the correct python format upon assignment
            value = self.field.to_python(value)
        instance.__dict__[self.field.name] = value


def pydantic_model_encoder_factory(*, model_dump_options=None):
    class PydanticModelEncoder(JSONEncoder):
        def default(self, obj):
            if isinstance(obj, BaseModel):
                return json.loads(obj.model_dump_json(**model_dump_options))
            return JSONEncoder.default(self, obj)

    return PydanticModelEncoder


def pydantic_model_decoder_factory(*, pydantic_model=None):
    class PydanticModelDecoder(json.JSONDecoder):
        def object_hook(self, obj: dict):
            if pydantic_model:
                return pydantic_model(**obj)
            return obj

    return PydanticModelDecoder


class PydanticJSONField(models.JSONField):
    valid_model_dump_json_options = {
        "indent",
        "include",
        "exclude",
        "by_alias",
        "exclude_unset",
        "exclude_defaults",
        "exclude_none",
        "round_trip",
        "warnings",
    }

    def __init__(self, *args, pydantic_model: type[BaseModel], **kwargs):
        self.pydantic_model = pydantic_model

        # Grab kwargs relevant to model_dump_json
        self.model_dump_options = {
            key: value
            for key, value in kwargs.items()
            if key in self.valid_model_dump_json_options
        }
        for key in self.model_dump_options.keys():
            # Remove model dump options from the kwargs list
            kwargs.pop(key)

        super().__init__(
            *args,
            **kwargs,
            encoder=pydantic_model_encoder_factory(
                model_dump_options=self.model_dump_options
            ),
            decoder=pydantic_model_decoder_factory(pydantic_model=pydantic_model)
        )

    def prepare_value(self, value: BaseModel | dict | None) -> BaseModel | None:
        """Convert the value into a Pydantic model instance."""
        if isinstance(value, BaseModel):
            return value
        if isinstance(value, dict):
            return self.pydantic_model(**value)
        return value

    def from_db_value(self, value: str | None, expression, connection):
        """Convert the value from the database into a Pydantic model instance."""
        if value is None:
            return value
        try:
            return json.loads(value, cls=self.decoder)
        except (PydanticValidationError, json.JSONDecodeError) as e:
            raise ValidationError(str(e))

    def to_python(self, value: BaseModel | dict | str | None) -> BaseModel | None:
        """Convert the value into a Pydantic model instance."""
        try:
            if isinstance(value, str):
                return json.loads(value, cls=self.decoder)
            elif isinstance(value, dict):
                return self.pydantic_model(**value)
        except (PydanticValidationError, json.JSONDecodeError) as e:
            raise ValidationError(str(e))

        return value

    def deconstruct(self) -> tuple[str, str, list, dict]:
        name, path, args, kwargs = super().deconstruct()
        # Include 'pydantic_model' in the kwargs so Django knows about it during migrations
        kwargs["pydantic_model"] = self.pydantic_model
        return name, path, args, kwargs

    def formfield(self, **kwargs) -> PydanticJSONFormField:
        # Specify the custom form field for admin forms
        kwargs["form_class"] = PydanticJSONFormField
        return super().formfield(pydantic_model=self.pydantic_model, **kwargs)

    def contribute_to_class(self, cls, name, **kwargs) -> None:
        """Set the descriptor on the model field."""
        super().contribute_to_class(cls, name, **kwargs)
        setattr(cls, self.name, PydanticJSONFieldDescriptor(self))
