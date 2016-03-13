from django.db import models
from django_pages.models import MetadataModel, PageModel


class Author(MetadataModel):
    name = models.CharField(max_length=255)
    editor = models.ForeignKey('Author', null=True)
    tags = models.ManyToManyField('Tag', related_name='authors')


class Article(PageModel):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, null=True)
    tags = models.ManyToManyField('Tag', related_name='articles')


class Tag(MetadataModel):
    name = models.CharField(max_length=255)
