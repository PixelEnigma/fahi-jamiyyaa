from django.db import models


class Setting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField(blank=True)
    description = models.TextField(blank=True)
    is_editable = models.BooleanField(default=True)

    class Meta:
        ordering = ['key']

    def __str__(self):
        return self.key

    @staticmethod
    def get(key, default=''):
        try:
            return Setting.objects.get(key=key).value
        except Setting.DoesNotExist:
            return default

    @staticmethod
    def get_decimal(key, default=0):
        from decimal import Decimal
        try:
            return Decimal(Setting.objects.get(key=key).value or '0')
        except (Setting.DoesNotExist, ValueError):
            return Decimal(str(default))
