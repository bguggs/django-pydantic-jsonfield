from django.core.exceptions import ValidationError
from django.db import models
from pydantic import BaseModel, ValidationError as PydanticValidationError


class PydanticJSONField(models.JSONField):
    def __init__(self, *args, pydantic_model: type[BaseModel], **kwargs):
        self.pydantic_model = pydantic_model
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value):
        # Validate the value using the provided Pydantic model.
        # If validation fails, raise the ValidationError as a Django ValidationError.
        if value is not None:
            try:
                # Validate the value against the Pydantic model's schema.
                value = self.pydantic_model(**value).dict()
            except PydanticValidationError as e:
                raise ValidationError(e.errors())
        return super().get_prep_value(value)

    def from_db_value(self, value, expression, connection):
        if value is not None:
            return self.pydantic_model(**value)
        return value

    def to_python(self, value):
        # Convert the value into a Pydantic model instance.
        if value is not None and not isinstance(value, self.pydantic_model):
            return self.pydantic_model(**value)
        return value
