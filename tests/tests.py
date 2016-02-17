import os.path

from django.core import management, serializers
from django.test import TestCase, override_settings

from .models import RelatedThingA, RelatedThingB, Thing


class TestModel(TestCase):
    def test_natural_key(self):
        t = Thing.objects.create(
            key='thing',
            content='This is a *blue* thing',
            content_format='md',
            colour='blue',
        )
        self.assertEqual(t.natural_key(), ('thing',))

    def test_get_by_natural_key(self):
        t1 = Thing.objects.create(
            key='thing1',
            content='This is a *blue* thing',
            content_format='md',
            colour='blue',
        )

        t2 = Thing.objects.create(
            key='thing2',
            content='This is a *green* thing',
            content_format='md',
            colour='green',
        )

        self.assertEqual(Thing.objects.get_by_natural_key('thing1'), t1)


class TestDeserialization(TestCase):
    def deserialize(self, filename):
        path = os.path.join('tests', 'pages', 'thing', filename)
        with open(path, 'rb') as f:
            return next(serializers.deserialize('md', f))

    def test_deserialization(self):
        deserialized_obj = self.deserialize('valid.md')
        obj = deserialized_obj.object

        self.assertEqual(obj.key, 'valid')
        self.assertEqual(obj.content_format, '.md')
        self.assertEqual(obj.content, 'This is a *green* thing\n')
        self.assertEqual(obj.colour, 'green')

    def test_deserialization_with_foreign_key(self):
        related_obj = RelatedThingA.objects.create(pk=1, name='A1')

        deserialized_obj = self.deserialize('with_foreign_key.md')
        obj = deserialized_obj.object

        self.assertEqual(obj.related_thing_a, related_obj)

    def test_deserialization_with_natural_foreign_key(self):
        related_obj = RelatedThingB.objects.create(name='B1')

        deserialized_obj = self.deserialize('with_natural_foreign_key.md')
        obj = deserialized_obj.object

        self.assertEqual(obj.related_thing_b, related_obj)

    def test_deserialization_with_invalid_yaml(self):
        with self.assertRaises(serializers.base.DeserializationError):
            self.deserialize('invalid_yaml.md')

    def test_deserialization_with_missing_content(self):
        with self.assertRaises(serializers.base.DeserializationError):
            self.deserialize('missing_content.md')

    def test_deserialization_with_invalid_object(self):
        with self.assertRaises(serializers.base.DeserializationError):
            self.deserialize('invalid_object.md')


class TestSerialization(TestCase):
    def _test_roundtrip(self, filename, **kwargs):
        path = os.path.join('tests', 'pages', 'thing', filename)
        with open(path, 'rb') as f:
            obj = next(serializers.deserialize('md', f)).object

        obj.save()

        with open(path) as f:
            expected_serialization = f.read()

        actual = serializers.serialize('md', [obj], **kwargs)
        self.assertEqual(actual, expected_serialization)

    def test_serialization(self):
        self._test_roundtrip('valid.md')

    def test_serialization_with_foreign_key(self):
        related_obj = RelatedThingA.objects.create(pk=1, name='A1')
        self._test_roundtrip('with_foreign_key.md')

    def test_serialization_with_natural_foreign_key(self):
        related_obj = RelatedThingB.objects.create(name='B1')
        self._test_roundtrip('with_natural_foreign_key.md', use_natural_foreign_keys=True)


class TestLoadData(TestCase):
    def test_loaddata(self):
        path = os.path.join('tests', 'pages', 'thing', 'valid.md')
        management.call_command('loaddata', path, verbosity=0)

        t = Thing.objects.get(key='valid')
        self.assertEqual(t.key, 'valid')
        self.assertEqual(t.content_format, '.md')
        self.assertEqual(t.content, 'This is a *green* thing\n')
        self.assertEqual(t.colour, 'green')
