from functools import wraps

from django import db
from django.db import models
from django.db.models import QuerySet


def close_db(func):
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        db.close_old_connections()
        try:
            result = func(*args, **kwargs)
        finally:
            db.close_old_connections()

        return result

    return func_wrapper


class BasicModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class _SoftDeleteQuerySet(QuerySet):
    def delete(self):
        return super().update(deleted=1)

    def hard_delete(self):
        return super().delete()


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset().filter(deleted=0)
        if not issubclass(qs.__class__, _SoftDeleteQuerySet):
            qs.__class__ = _SoftDeleteQuerySet
        return qs


class SoftDeleteModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted = models.IntegerField(default=0)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def delete(self, using=None, keep_parents=False):
        self.deleted = 1
        self.save(update_fields=["deleted"])

    class Meta:
        abstract = True
