from django.db import migrations


def seed_bot_token(apps, schema_editor):
    Setting = apps.get_model('core', 'Setting')
    Setting.objects.get_or_create(
        key='telegram_bot_token',
        defaults={'value': '', 'description': 'Telegram Bot API Token (from @BotFather)', 'is_editable': True},
    )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_seed_due_day_setting'),
    ]

    operations = [
        migrations.RunPython(seed_bot_token),
    ]
