import json
from json import JSONDecoder, JSONEncoder

from django.core.exceptions import ValidationError
from django.db import models
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from pydantic_jsonfield.forms import PydanticJSONFormField


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


class PydanticModelEncoder(JSONEncoder):
    default_model_dump_json_options = {
        "indent": None,
        "include": None,
        "exclude": None,
        "by_alias": False,
        "exclude_unset": False,
        "exclude_defaults": False,
        "exclude_none": False,
        "round_trip": False,
        "warnings": True,
    }

    def __init__(self, *args, **kwargs):
        self.model_dump_json_options = self.default_model_dump_json_options.copy()
        for key, value in kwargs.copy().items():
            # Update the default options with any provided options
            if key in self.model_dump_json_options:
                self.model_dump_json_options[key] = value
            del kwargs[key]
        super().__init__(*args, **kwargs)

    def default(self, obj):
        if isinstance(obj, BaseModel):
            return json.loads(obj.model_dump_json(**self.model_dump_json_options))
        return super().default(obj)


class PydanticModelDecoder(JSONDecoder):
    def __init__(self, *args, pydantic_model=None, **kwargs):
        self.pydantic_model = pydantic_model
        super().__init__(*args, **kwargs)

    def object_hook(self, obj: dict):
        if self.pydantic_model:
            return self.pydantic_model(**obj)
        return obj


class PydanticJSONField(models.JSONField):
    def __init__(self, *args, pydantic_model: type[BaseModel], **kwargs):
        self.pydantic_model = pydantic_model
        kwargs["encoder"] = kwargs.pop("encoder", PydanticModelEncoder)
        kwargs["decoder"] = kwargs.pop("decoder", PydanticModelDecoder)
        super().__init__(*args, **kwargs)

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
