import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Payment, Expense


@login_required
def export_payments_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="payments.csv"'
    writer = csv.writer(response)
    writer.writerow(['Member', 'Month', 'Amount', 'Paid Date', 'Received By', 'Notes'])
    for p in Payment.objects.select_related('member', 'received_by').all():
        writer.writerow([
            p.member.get_full_name() or p.member.username,
            p.month.strftime('%B %Y'),
            p.amount,
            p.paid_date,
            p.received_by.get_full_name() if p.received_by else '',
            p.notes,
        ])
    return response


@login_required
def export_expenses_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expenses.csv"'
    writer = csv.writer(response)
    writer.writerow(['Description', 'Category', 'Amount', 'Date', 'Paid By', 'Notes'])
    for e in Expense.objects.select_related('paid_by').all():
        writer.writerow([
            e.description,
            e.get_category_display(),
            e.amount,
            e.date,
            e.paid_by.get_full_name() if e.paid_by else '',
            e.notes,
        ])
    return response
