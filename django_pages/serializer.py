import os.path

import yaml

from django.apps import apps
from django.db import models
from django.core.exceptions import FieldDoesNotExist
from django.core.serializers.base import DeserializationError
from django.core.serializers.python import (
    Deserializer as PythonDeserializer, Serializer as PythonSerializer,
)
from django.core.serializers.pyyaml import DjangoSafeDumper


class Serializer(PythonSerializer):
    internal_use_only = False

    def end_serialization(self):
        assert len(self.objects) == 1
        obj = self.objects[0]

        app_label, model_name = obj['model'].split('.')
        model = apps.get_model(app_label, model_name)

        fields = {name: value for name, value in obj['fields'].items() if value}
        fields.pop('key')
        fields.pop('content_format', None)
        content = fields.pop('content', None)

        for field_name, field_value in fields.items():
            if is_fk_field_with_natural_key(model, field_name):
                if isinstance(field_value, tuple) and len(field_value) == 1:
                    fields[field_name] = field_value[0]

            if is_m2m_field_with_natural_key(model, field_name):
                if isinstance(field_value, list):
                    fields[field_name] = [v[0] for v in field_value]

        yaml.dump(fields, self.stream, Dumper=DjangoSafeDumper,
                  default_flow_style=False, **self.options)

        if content is not None:
            self.stream.write('---\n')
            self.stream.write(content)

    def getvalue(self):
        # Grand-parent super
        return super(PythonSerializer, self).getvalue()


# Built-in deserializers take either a stream or string, but we require a file,
# because we extract some of the data about the object deserialized in the file
# from its path.
def Deserializer(file, **options):
    path, filename = os.path.split(file.name)
    path_segments = path.split(os.path.sep)

    app_label = path_segments[-3]
    model_type = path_segments[-2]
    model_name = path_segments[-1]
    model = apps.get_model(app_label, model_name)

    data = file.read().decode('utf-8')

    separator = '\n---\n'

    parts = data.split(separator, 1)

    try:
        fields = yaml.load(parts[0], Loader=yaml.CSafeLoader)
    except yaml.YAMLError as e:
        raise DeserializationError(e)

    for field_name, field_value in fields.items():
        if is_fk_field_with_natural_key(model, field_name):
            if isinstance(field_value, str):
                fields[field_name] = [field_value]

        if is_m2m_field_with_natural_key(model, field_name):
            if isinstance(field_value, list):
                fields[field_name] = [[v] for v in field_value]

    if model_type == 'pages':
        if len(parts) == 1:
            raise DeserializationError('Missing content')

        fields['key'], fields['content_format'] = os.path.splitext(filename)
        fields['content'] = parts[1]

    elif model_type == 'metadata':
        fields['key'], _ = os.path.splitext(filename)

    else:
        assert False
    
    record = {
        'model': '{}.{}'.format(app_label, model_name),
        'fields': fields,
    }

    try:
        yield from PythonDeserializer([record], **options)
    except Exception as e:
        raise DeserializationError(e)


def is_fk_field_with_natural_key(model, field_name):
    try:
        field = model._meta.get_field(field_name)
    except FieldDoesNotExist:
        return False

    if field.remote_field and isinstance(field.remote_field, models.ManyToOneRel):
        default_manager = field.remote_field.model._default_manager
        if hasattr(default_manager, 'get_by_natural_key'):
            return  True

    return False


def is_m2m_field_with_natural_key(model, field_name):
    try:
        field = model._meta.get_field(field_name)
    except FieldDoesNotExist:
        return False

    if field.remote_field and isinstance(field.remote_field, models.ManyToManyRel):
        default_manager = field.remote_field.model._default_manager
        if hasattr(default_manager, 'get_by_natural_key'):
            return  True

    return False
