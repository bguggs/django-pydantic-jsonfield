import json

import django
if django.VERSION < (3, 1):
    from django_jsonfield_backport.forms import JSONField
else:
    from django.forms import JSONField
from django import forms
from pydantic import BaseModel


class PrettyJSONWidget(forms.widgets.Textarea):
    def format_value(self, value):
        try:
            value = json.dumps(json.loads(value), indent=4)
            # these lines will try to adjust size of TextArea to fit to content
            row_lengths = [len(r) for r in value.split("\n")]
            self.attrs["rows"] = min(max(len(row_lengths) + 2, 10), 60)
            self.attrs["cols"] = min(max(max(row_lengths) + 2, 40), 200)
            return value
        except (TypeError, ValueError):
            return super(PrettyJSONWidget, self).format_value(value)


class PydanticJSONFormField(JSONField):
    def __init__(self, *args, pydantic_model: type[BaseModel], **kwargs) -> None:
        self.pydantic_model = pydantic_model
        kwargs.setdefault("widget", PrettyJSONWidget)
        super().__init__(*args, **kwargs)
