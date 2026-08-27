from django.db import migrations


def seed_settings(apps, schema_editor):
    Setting = apps.get_model('core', 'Setting')
    Setting.objects.get_or_create(
        key='default_monthly_dues',
        defaults={'value': '20.00', 'description': 'Default minimum monthly dues for members without a custom amount', 'is_editable': True},
    )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_settings),
    ]
