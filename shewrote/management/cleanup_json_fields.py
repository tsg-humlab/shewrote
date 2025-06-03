from django.db.models import JSONField, F, Func, Value, UUIDField
from django.apps import apps

# Get all models from app
app_models = apps.get_app_config('shewrote').get_models()

for model in app_models:
    json_field_names = [field.name for field in model._meta.get_fields() if isinstance(field, JSONField)]
    for json_field_name in json_field_names:
        func = Func(F(json_field_name), Value('\\\\'), Value('\u005c'), function='replace')
        model.objects.update(**{json_field_name:  func})
    uuid_field_names = [field.name for field in model._meta.get_fields() if isinstance(field, UUIDField)]
    for uuid_field_name in uuid_field_names:
        func = Func(F(uuid_field_name), Value('-'), Value(''), function='replace')
        model.objects.update(**{uuid_field_name: func})

