from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from members.models import Member
from finances.models import Payment
from notices.models import Notice
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create notices for members with unpaid dues'

    def handle(self, *args, **options):
        now = timezone.now()
        first_of_month = date(now.year, now.month, 1)
        created = 0
        for m in Member.objects.filter(is_active_member=True):
            status, paid, minimum = Payment.status_for_member_month(m, first_of_month)
            if status in ('unpaid', 'partial'):
                Notice.objects.create(
                    title='Dues Reminder',
                    body=f'{m.get_full_name() or m.username} has {"unpaid" if status == "unpaid" else "partially paid"} dues for {first_of_month.strftime("%B %Y")}. Minimum due: {minimum}. Paid: {paid}.',
                    priority='normal',
                )
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Created {created} reminder notice(s)'))
