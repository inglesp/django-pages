import os

from django.apps import apps
from django.db import models

from .serializer import Serializer


class PagesManager(models.Manager):
    def get_by_natural_key(self, key):
        return self.get(key=key)


class DjangoPagesModel(models.Model):
    objects = PagesManager()

    class Meta:
        abstract = True

    @classmethod
    def dump_dir_path(cls):
        app_config = apps.get_app_config(cls._meta.app_label)
        return os.path.join(app_config.path, cls.model_type, cls._meta.model_name)

    def dump_to_file(self):
        filename = '{}{}'.format(self.key, self.content_format)
        dir_path = self.dump_dir_path()
        os.makedirs(dir_path, exist_ok=True)
        path = os.path.join(dir_path, filename)

        serializer = Serializer()
        serializer.serialize([self], use_natural_foreign_keys=True)
        data = serializer.getvalue()

        with open(path, 'w') as f:
            f.write(data)

    def natural_key(self):
        return (self.key,)

    def __str__(self):
        return self.key


class MetadataModel(DjangoPagesModel):
    key = models.CharField(max_length=255)

    content_format = '.yml'

    model_type = 'metadata'

    class Meta:
        abstract = True


class PageModel(DjangoPagesModel):
    key = models.CharField(max_length=255)
    content = models.TextField()
    content_format = models.CharField(max_length=255)

    model_type = 'pages'

    class Meta:
        abstract = True
