import calendar
import csv
from decimal import Decimal
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.utils import timezone
from datetime import date
from finances.models import Payment, Expense
from events.models import Event
from members.models import Member
from sponsors.models import Sponsor
from core.models import Setting


class ReportView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/report.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        try:
            year = int(self.request.GET.get('year', now.year))
        except (TypeError, ValueError):
            year = now.year
        year = min(max(year, now.year - 5), now.year + 1)

        default_dues = Setting.get_decimal('default_monthly_dues', 0)
        members = Member.objects.filter(is_active_member=True)

        def effective_dues(mb):
            return mb.monthly_dues or default_dues

        # --- Monthly breakdown ---
        monthly = []
        for m in range(1, 13):
            month_date = date(year, m, 1)
            payments = Payment.objects.filter(month=month_date)
            expenses = Expense.objects.filter(date__year=year, date__month=m)
            total_due = sum(effective_dues(mb) for mb in members.filter(join_date__lte=month_date))
            col = payments.aggregate(t=Sum('amount'))['t'] or 0
            exp = expenses.aggregate(t=Sum('amount'))['t'] or 0
            monthly.append({
                'month': calendar.month_name[m],
                'month_short': calendar.month_abbr[m],
                'total_due': total_due,
                'collected': col,
                'expenses': exp,
                'net': col - exp,
                'rate': round(col / total_due * 100, 1) if total_due else 0,
            })

        total_due_year = sum(effective_dues(mb) for mb in members) * 12
        total_collected = Payment.objects.filter(month__year=year).aggregate(t=Sum('amount'))['t'] or 0
        total_expenses = Expense.objects.filter(date__year=year).aggregate(t=Sum('amount'))['t'] or 0

        # --- Members with outstanding dues (latest month of the year) ---
        if year < now.year:
            target_month = date(year, 12, 1)
        else:
            target_month = date(year, now.month, 1)
        outstanding = []
        for mb in members.filter(join_date__lte=target_month):
            total = Payment.total_for_member_month(mb, target_month)
            minimum = mb.effective_monthly_dues
            remaining = max(minimum - total, Decimal('0.00'))
            if remaining > 0:
                outstanding.append({
                    'member': mb,
                    'minimum': minimum,
                    'paid': total,
                    'remaining': remaining,
                })
        outstanding.sort(key=lambda r: r['remaining'], reverse=True)
        outstanding_count = len(outstanding)

        # --- Top contributors (all time) ---
        top_qs = Payment.objects.values('member').annotate(
            total=Sum('amount'), count=Count('id')
        ).order_by('-total')[:10]
        member_map = {m.id: m for m in Member.objects.filter(id__in=[t['member'] for t in top_qs])}
        top_contributors = [{
            'member': member_map[t['member']],
            'total': t['total'],
            'count': t['count'],
        } for t in top_qs if t['member'] in member_map]

        # --- Expense by category ---
        expense_categories = Expense.objects.filter(date__year=year).values('category').annotate(
            total=Sum('amount'), count=Count('id')
        ).order_by('-total')
        expense_categories = list(expense_categories)
        expense_cat_total = sum(e['total'] for e in expense_categories) or 0

        # --- Member growth by year ---
        growth = {}
        for mb in Member.objects.all():
            growth[mb.join_date.year] = growth.get(mb.join_date.year, 0) + 1
        member_growth = [{'year': y, 'count': growth[y]} for y in sorted(growth)]

        # --- Events summary ---
        events_qs = Event.objects.filter(date__year=year)
        event_status = list(events_qs.values('status').annotate(count=Count('id')))

        # --- Sponsors ---
        sponsors = list(Sponsor.objects.filter(is_active=True).order_by('-total_contribution')[:10])
        sponsor_tiers = list(Sponsor.objects.values('tier').annotate(
            total=Sum('total_contribution'), count=Count('id')
        ).order_by('-total'))
        sponsor_total = Sponsor.objects.filter(is_active=True).aggregate(t=Sum('total_contribution'))['t'] or 0

        ctx.update({
            'year': year,
            'years': list(range(now.year - 3, now.year + 1)),
            'monthly_data': monthly,
            'expense_by_category': expense_categories,
            'expense_cat_total': expense_cat_total,
            'top_contributors': top_contributors,
            'outstanding': outstanding[:10],
            'outstanding_count': outstanding_count,
            'outstanding_month': target_month.strftime('%B %Y'),
            'member_growth': member_growth,
            'member_growth_max': max((g['count'] for g in member_growth), default=1),
            'event_status': event_status,
            'event_total': events_qs.count(),
            'sponsors': sponsors,
            'sponsor_tiers': sponsor_tiers,
            'sponsor_total': sponsor_total,
            'total_dues': total_due_year,
            'total_collected': total_collected,
            'total_expenses': total_expenses,
            'balance': total_collected - total_expenses,
            'collection_rate': round(total_collected / total_due_year * 100, 1) if total_due_year else 0,
        })
        return ctx


class ReportExportView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        now = timezone.now()
        try:
            year = int(request.GET.get('year', now.year))
        except (TypeError, ValueError):
            year = now.year

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="report_{year}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Month', 'Total Dues', 'Collected', 'Collection Rate %', 'Expenses', 'Net'])

        from core.reports import _build_monthly
        for row in _build_monthly(year):
            writer.writerow([
                row['month'],
                row['total_due'],
                row['collected'],
                row['rate'],
                row['expenses'],
                row['net'],
            ])
        return response


def _build_monthly(year):
    default_dues = Setting.get_decimal('default_monthly_dues', 0)
    members = Member.objects.filter(is_active_member=True)
    monthly = []
    for m in range(1, 13):
        month_date = date(year, m, 1)
        payments = Payment.objects.filter(month=month_date)
        expenses = Expense.objects.filter(date__year=year, date__month=m)
        total_due = sum(mb.monthly_dues or default_dues for mb in members.filter(join_date__lte=month_date))
        col = payments.aggregate(t=Sum('amount'))['t'] or 0
        exp = expenses.aggregate(t=Sum('amount'))['t'] or 0
        monthly.append({
            'month': calendar.month_name[m],
            'total_due': total_due,
            'collected': col,
            'rate': round(col / total_due * 100, 1) if total_due else 0,
            'expenses': exp,
            'net': col - exp,
        })
    return monthly
