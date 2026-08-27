from django.db import migrations


def seed_due_day(apps, schema_editor):
    Setting = apps.get_model('core', 'Setting')
    Setting.objects.get_or_create(
        key='default_due_day',
        defaults={'value': '10', 'description': 'Day of month dues are due by (e.g. 10 = 10th)', 'is_editable': True},
    )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_seed_default_settings'),
    ]

    operations = [
        migrations.RunPython(seed_due_day),
    ]
