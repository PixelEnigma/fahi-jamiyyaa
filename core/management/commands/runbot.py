import os
import logging
from django.core.management.base import BaseCommand, CommandError
from core.models import Setting

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Start the Fahi Jamiyyaa Telegram bot'

    def handle(self, *args, **options):
        token = os.environ.get('TELEGRAM_BOT_TOKEN', '') or Setting.get('telegram_bot_token', '')
        if not token:
            raise CommandError(
                'No bot token configured. '
                'Set TELEGRAM_BOT_TOKEN env var or set it in Settings in the web app.'
            )

        self.stdout.write(self.style.SUCCESS('Starting Telegram bot...'))

        from bot.handlers import build_app
        import asyncio

        app = build_app(token)
        app.run_polling(drop_pending_updates=True)
