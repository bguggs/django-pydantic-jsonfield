# Django Pydantic JSONField

## Description

Django Pydantic JSONField is a Django app that extends Django's native `JSONField` by integrating Pydantic models for data validation. This package allows developers to leverage Pydantic's powerful data validation and schema enforcement capabilities within their Django models, ensuring that data stored in JSONFields is validated against predefined Pydantic models.

## Features

- Seamless integration of Pydantic models with Django models.
- Customizable JSON serialization options via extendable encoders.
- Support for complex data types and validation provided by Pydantic.

## Installation

To install Django Pydantic JSONField, run the following command in your virtual environment:

```bash
pip install django-pydantic-jsonfield
```

## Quick Start

### Defining Your Pydantic Model

```python
from pydantic import BaseModel
from datetime import datetime

class ProductDetails(BaseModel):
    name: str
    description: str
    price: float
    tags: list[str]
    created: datetime
```

### Using PydanticJSONField in Your Django Model

Every `PydanticJSONField` requires a `pydantic_model` argument, which is the Pydantic model that will be used to validate the JSON data.

```python
from django.db import models
from django_pydantic_jsonfield.fields import PydanticJSONField

class Product(models.Model):
    details = PydanticJSONField(
        pydantic_model=ProductDetails,
    )
```

### Interacting with Your Model

```python
from datetime import datetime

product = Product(details={
    "name": "Smart Watch",
    "description": "A smart watch with health tracking features.",
    "price": 199.99,
    "tags": ["wearable", "health", "gadget"],
    "created": datetime.now(),
})
product.save()

# Accessing the details field will return a Pydantic model instance
print(product.details.name)
product.details.description = "My new description"
product.save()
```

## Advanced Usage

### Creating a Custom Encoder

Pydantic objects are serialized using the Pydantic [model_dump_json](https://docs.pydantic.dev/latest/api/base_model/#pydantic.BaseModel.model_dump_json) method which can handle complex data types. If you'd like to take advantage of some of the serialization options available on that method, you can use a CustomEncoder to pass in additional arguments.

```python
class CustomPydanticModelEncoder(PydanticModelEncoder):
    default_model_dump_json_options = {
        "indent": 2,
        "exclude_none": True,
    }

class Product(models.Model):
    details = PydanticJSONField(
        pydantic_model=ProductDetails,
        encoder=CustomPydanticModelEncoder,
    )
```


