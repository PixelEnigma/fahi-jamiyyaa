from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import date
from members.models import Member
from finances.models import Payment
from notices.models import Notice


@login_required
def send_reminders(request):
    if request.user.role not in ('admin', 'board', 'treasurer'):
        messages.error(request, 'Permission denied.')
        return redirect('dashboard')
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
    messages.success(request, f'{created} reminder notice(s) created.')
    return redirect('collection')
