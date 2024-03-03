from django.test import TestCase
from pydantic import BaseModel, ValidationError

from pydantic_jsonfield.fields import PydanticJSONField


class ItemModel(BaseModel):
    name: str
    description: str
    price: float


class PydanticJSONFieldTest(TestCase):
    def test_valid_data(self):
        """Test PydanticJSONField with valid data."""
        field = PydanticJSONField(pydantic_model=ItemModel)
        value = field.to_python(
            {"name": "Test Item", "description": "A test item.", "price": 19.99}
        )
        assert isinstance(value, ItemModel)

    def test_invalid_data(self):
        """Test PydanticJSONField with invalid data raises ValidationError."""
        field = PydanticJSONField(pydantic_model=ItemModel)
        with self.assertRaises(ValidationError):
            field.to_python(
                {
                    "name": "Test Item",
                    "description": "A test item.",
                    "price": "expensive",
                }
            )
