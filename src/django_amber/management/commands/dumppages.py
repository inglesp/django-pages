import glob
import os

from django.apps import apps
from django.core.management.base import BaseCommand

from ...models import DjangoPagesModel
from ...serialization_helpers import dump_to_file


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                if issubclass(model, DjangoPagesModel):
                    for path in glob.glob(model.dump_path_glob_path()):
                        os.remove(path)

                    for obj in model.objects.all():
                        dump_to_file(obj)
