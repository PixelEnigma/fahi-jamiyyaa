import os
import sys
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    CallbackQueryHandler, filters, ContextTypes,
)
from asgiref.sync import sync_to_async

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.utils import timezone
from datetime import date
from decimal import Decimal
from django.db.models import Sum
from members.models import Member
from finances.models import Payment, Expense
from core.models import Setting

logger = logging.getLogger(__name__)

WAITING_LINK_CODE = 1


def get_member_by_tg(telegram_id):
    try:
        return Member.objects.get(telegram_id=telegram_id)
    except Member.DoesNotExist:
        return None


def is_privileged(member):
    return member and member.role in ('admin', 'board', 'treasurer')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    member = await sync_to_async(get_member_by_tg)(user.id)

    if member:
        name = member.get_full_name() or member.username
        text = (
            f"Assalamu Alaikum, {name}!\n\n"
            f"Welcome back to the *Fahi Jamiyyaa* bot.\n\n"
            f"Your role: *{member.get_role_display()}*\n\n"
            f"Use /help to see available commands."
        )
    else:
        text = (
            "Assalamu Alaikum! Welcome to the *Fahi Jamiyyaa* bot.\n\n"
            "You are not linked to a member account yet.\n"
            "Use /link to connect your Telegram account."
        )
    await update.message.reply_text(text, parse_mode='Markdown')


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    member = await sync_to_async(get_member_by_tg)(user.id)

    text = "*Fahi Jamiyyaa Bot Commands*\n\n"
    text += "/start - Welcome message\n"
    text += "/help - Show this help\n"
    text += "/link - Link your Telegram account\n"
    text += "/unlink - Unlink your Telegram account\n"

    if member:
        text += "\n*Finance*\n"
        text += "/dues - View your current dues\n"
        text += "/history - View your payment history\n"

    if member and await sync_to_async(is_privileged)(member):
        text += "\n*Admin/Board/Treasurer*\n"
        text += "/collection - View collection status\n"
        text += "/remind - Send reminders to unpaid members\n"
        text += "/stats - Quick financial stats\n"

    if not member:
        text += "\n_Link your account first with /link to access finance commands._\n"

    await update.message.reply_text(text, parse_mode='Markdown')


async def link_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    member = await sync_to_async(get_member_by_tg)(user.id)

    if member:
        await update.message.reply_text(
            "You are already linked to a member account.\n"
            "Use /unlink first if you want to relink.",
            parse_mode='Markdown',
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "To link your Telegram account, please enter the *link code* "
        "from your web app profile page.\n\n"
        "Go to: *Members > Profile > Link Telegram*\n"
        "Then enter the code here.",
        parse_mode='Markdown',
    )
    return WAITING_LINK_CODE


async def link_receive_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    user = update.effective_user

    member = await sync_to_async(
        lambda: Member.objects.filter(telegram_link_code=code).first()
    )()

    if not member:
        await update.message.reply_text(
            "Invalid or expired code. Please try again or send /cancel.",
            parse_mode='Markdown',
        )
        return WAITING_LINK_CODE

    # Check if code is expired (older than 15 minutes)
    if not member.telegram_link_code:
        await update.message.reply_text("Code expired. Generate a new one from your profile.")
        return ConversationHandler.END

    member.telegram_id = user.id
    member.telegram_link_code = None
    await sync_to_async(member.save)()

    name = member.get_full_name() or member.username
    await update.message.reply_text(
        f"Account linked successfully!\n\n"
        f"Welcome, *{name}* ({member.get_role_display()})\n"
        f"Use /help to see available commands.",
        parse_mode='Markdown',
    )
    return ConversationHandler.END


async def link_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Link cancelled.")
    return ConversationHandler.END


async def unlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    member = await sync_to_async(get_member_by_tg)(user.id)

    if not member:
        await update.message.reply_text("You are not linked to any account.")
        return

    member.telegram_id = None
    await sync_to_async(member.save)()
    await update.message.reply_text("Account unlinked. Use /link to relink.")


async def dues(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    member = await sync_to_async(get_member_by_tg)(user.id)

    if not member:
        await update.message.reply_text("Link your account first with /link.")
        return

    now = timezone.now()
    first_of_month = date(now.year, now.month, 1)
    status, paid, minimum = await sync_to_async(Payment.status_for_member_month)(member, first_of_month)
    remaining = max(minimum - paid, Decimal('0'))

    status_emoji = {'paid': 'Paid', 'partial': 'Partial', 'unpaid': 'Unpaid'}

    text = (
        f"*Dues for {first_of_month.strftime('%B %Y')}*\n\n"
        f"Status: *{status_emoji.get(status, status)}*\n"
        f"Minimum due: {minimum}\n"
        f"Paid: {paid}\n"
        f"Remaining: {remaining}\n"
    )

    if status == 'unpaid':
        text += "\nPlease pay your dues before the due date."
    elif status == 'partial':
        text += f"\nPartial payment. Please pay the remaining {remaining}."

    await update.message.reply_text(text, parse_mode='Markdown')


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    member = await sync_to_async(get_member_by_tg)(user.id)

    if not member:
        await update.message.reply_text("Link your account first with /link.")
        return

    payments = await sync_to_async(
        lambda: list(Payment.objects.filter(member=member).order_by('-month', '-paid_date')[:10])
    )()

    if not payments:
        await update.message.reply_text("No payment history found.")
        return

    text = f"*Your Payment History* (last {len(payments)} entries)\n\n"
    for p in payments:
        text += f"*{p.month.strftime('%b %Y')}* - {p.amount} (on {p.paid_date.strftime('%d %b %Y')})\n"

    total = await sync_to_async(
        lambda: Payment.objects.filter(member=member).aggregate(t=Sum('amount'))['t'] or Decimal('0')
    )

    text += f"\n*Total paid:* {total}"
    await update.message.reply_text(text, parse_mode='Markdown')


async def collection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    member = await sync_to_async(get_member_by_tg)(user.id)

    if not member or not await sync_to_async(is_privileged)(member):
        await update.message.reply_text("This command is for admin, board, or treasurer only.")
        return

    now = timezone.now()
    first_of_month = date(now.year, now.month, 1)
    active_members = await sync_to_async(lambda: list(Member.objects.filter(is_active_member=True)))()

    total_due = Decimal('0')
    total_paid = Decimal('0')
    unpaid_members = []
    partial_members = []

    for m in active_members:
        status, paid, minimum = await sync_to_async(Payment.status_for_member_month)(m, first_of_month)
        total_due += minimum
        total_paid += paid
        if status == 'unpaid':
            unpaid_members.append(f"  - {m.get_full_name() or m.username}: {minimum}")
        elif status == 'partial':
            partial_members.append(f"  - {m.get_full_name() or m.username}: {paid}/{minimum}")

    pending = total_due - total_paid
    rate = (total_paid / total_due * 100) if total_due > 0 else Decimal('0')

    text = (
        f"*Collection Status - {first_of_month.strftime('%B %Y')}*\n\n"
        f"Total due: {total_due}\n"
        f"Total collected: {total_paid}\n"
        f"Pending: {pending}\n"
        f"Rate: {rate:.1f}%\n"
    )

    if partial_members:
        text += f"\n*Partial ({len(partial_members)}):*\n" + "\n".join(partial_members) + "\n"
    if unpaid_members:
        text += f"\n*Unpaid ({len(unpaid_members)}):*\n" + "\n".join(unpaid_members) + "\n"
    if not partial_members and not unpaid_members:
        text += "\nAll members are up to date!"

    # Telegram has a 4096 char limit
    if len(text) > 4000:
        text = text[:3950] + "\n\n... (truncated)"

    await update.message.reply_text(text, parse_mode='Markdown')


async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    member = await sync_to_async(get_member_by_tg)(user.id)

    if not member or not await sync_to_async(is_privileged)(member):
        await update.message.reply_text("This command is for admin, board, or treasurer only.")
        return

    now = timezone.now()
    first_of_month = date(now.year, now.month, 1)
    active_members = await sync_to_async(lambda: list(Member.objects.filter(is_active_member=True)))()

    reminded = []
    for m in active_members:
        status, paid, minimum = await sync_to_async(Payment.status_for_member_month)(m, first_of_month)
        if status in ('unpaid', 'partial'):
            if m.telegram_id:
                try:
                    bot = context.bot
                    await bot.send_message(
                        chat_id=m.telegram_id,
                        text=(
                            f"Assalamu Alaikum {m.get_full_name() or m.username},\n\n"
                            f"This is a friendly reminder that your dues for *{first_of_month.strftime('%B %Y')}* "
                            f"are {'unpaid' if status == 'unpaid' else 'partially paid'}.\n\n"
                            f"Minimum due: {minimum}\n"
                            f"Already paid: {paid}\n"
                            f"Remaining: {max(minimum - paid, Decimal('0'))}\n\n"
                            f"Please pay before the due date. JazakAllahu Khairan."
                        ),
                        parse_mode='Markdown',
                    )
                    reminded.append(m.get_full_name() or m.username)
                except Exception:
                    pass  # User might have blocked the bot

    if reminded:
        text = f"Reminders sent to {len(reminded)} members:\n" + "\n".join(f"  - {n}" for n in reminded)
    else:
        text = "No members with Telegram accounts need reminders, or no one is unpaid."

    await update.message.reply_text(text, parse_mode='Markdown')


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    member = await sync_to_async(get_member_by_tg)(user.id)

    if not member or not await sync_to_async(is_privileged)(member):
        await update.message.reply_text("This command is for admin, board, or treasurer only.")
        return

    now = timezone.now()
    first_of_month = date(now.year, now.month, 1)

    total_collected = await sync_to_async(
        lambda: Payment.objects.aggregate(t=Sum('amount'))['t'] or Decimal('0')
    )
    total_expenses = await sync_to_async(
        lambda: Expense.objects.aggregate(t=Sum('amount'))['t'] or Decimal('0')
    )
    month_collected = await sync_to_async(
        lambda: Payment.objects.filter(month=first_of_month).aggregate(t=Sum('amount'))['t'] or Decimal('0')
    )
    month_expenses = await sync_to_async(
        lambda: Expense.objects.filter(date__month=now.month, date__year=now.year).aggregate(t=Sum('amount'))['t'] or Decimal('0')
    )
    member_count = await sync_to_async(lambda: Member.objects.filter(is_active_member=True).count())

    text = (
        f"*Fahi Jamiyyaa - Financial Stats*\n\n"
        f"*This Month ({first_of_month.strftime('%b %Y')}):*\n"
        f"  Collected: {month_collected}\n"
        f"  Expenses: {month_expenses}\n"
        f"  Balance: {month_collected - month_expenses}\n\n"
        f"*Lifetime:*\n"
        f"  Total collected: {total_collected}\n"
        f"  Total expenses: {total_expenses}\n"
        f"  Net balance: {total_collected - total_expenses}\n\n"
        f"Active members: {member_count}"
    )

    await update.message.reply_text(text, parse_mode='Markdown')


def build_app(token: str) -> Application:
    app = Application.builder().token(token).build()

    link_conv = ConversationHandler(
        entry_points=[CommandHandler('link', link_start)],
        states={
            WAITING_LINK_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, link_receive_code),
            ],
        },
        fallbacks=[CommandHandler('cancel', link_cancel)],
    )

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_cmd))
    app.add_handler(link_conv)
    app.add_handler(CommandHandler('unlink', unlink))
    app.add_handler(CommandHandler('dues', dues))
    app.add_handler(CommandHandler('history', history))
    app.add_handler(CommandHandler('collection', collection))
    app.add_handler(CommandHandler('remind', remind))
    app.add_handler(CommandHandler('stats', stats))

    return app
