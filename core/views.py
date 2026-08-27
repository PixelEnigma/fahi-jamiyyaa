from django.views.generic import TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect
from datetime import timedelta
from datetime import date
from decimal import Decimal
from members.models import Member
from finances.models import Payment, Expense
from inventory.models import InventoryItem, Lease
from events.models import Event
from notices.models import Notice
from .models import Setting
from .mixins import AdminRequiredMixin


class SettingsView(AdminRequiredMixin, FormView):
    template_name = 'core/settings.html'

    def get_form(self):
        settings = Setting.objects.filter(is_editable=True)
        from django import forms
        fields = {}
        for s in settings:
            if s.key.endswith('_dues') or s.key.endswith('_amount'):
                fields[s.key] = forms.DecimalField(
                    initial=s.value, required=False, label=s.description or s.key,
                    widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'px-3 py-2 border border-gray-300 rounded-lg text-sm w-full'})
                )
            else:
                fields[s.key] = forms.CharField(
                    initial=s.value, required=False, label=s.description or s.key,
                    widget=forms.TextInput(attrs={'class': 'px-3 py-2 border border-gray-300 rounded-lg text-sm w-full'})
                )
        return type('SettingsForm', (forms.Form,), fields)(**self.get_form_kwargs())

    def form_valid(self, form):
        for key, value in form.cleaned_data.items():
            Setting.objects.filter(key=key).update(value=str(value))
        messages.success(self.request, 'Settings saved.')
        return redirect('settings')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['settings_list'] = Setting.objects.filter(is_editable=True)
        return ctx


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        first_of_month = date(now.year, now.month, 1)

        month_payments = Payment.objects.filter(month=first_of_month)
        default_dues = Setting.get_decimal('default_monthly_dues', 0)
        total_due = sum(m.monthly_dues or default_dues for m in Member.objects.filter(is_active_member=True))
        total_paid = month_payments.aggregate(t=Sum('amount'))['t'] or 0

        active_members = Member.objects.filter(is_active_member=True)
        total_members_count = active_members.count()

        total_collected_all = Payment.objects.aggregate(t=Sum('amount'))['t'] or 0
        total_expenses_all = Expense.objects.aggregate(t=Sum('amount'))['t'] or 0

        month_expenses = Expense.objects.filter(date__month=now.month, date__year=now.year)
        month_exp_total = month_expenses.aggregate(t=Sum('amount'))['t'] or 0

        ctx['selected_date'] = first_of_month
        ctx['total_members'] = total_members_count
        ctx['pending_dues'] = active_members.filter(monthly_dues=Decimal('0.00')).count() if default_dues > 0 else 0
        ctx['pending_dues_amount'] = total_due - total_paid
        ctx['available_items'] = InventoryItem.objects.filter(status='available').count()
        ctx['upcoming_events'] = Event.objects.filter(date__gte=now)[:5]
        ctx['overdue_leases'] = Lease.objects.filter(returned_date__isnull=True, expected_return_date__lt=now)
        ctx['recent_notices'] = Notice.objects.all()[:5]
        ctx['recent_expenses'] = month_expenses[:5]
        ctx['member_count_by_role'] = Member.objects.values('role').annotate(count=Count('id'))
        ctx['monthly_collection'] = total_paid
        ctx['monthly_expenses'] = month_exp_total
        ctx['monthly_balance'] = total_paid - month_exp_total
        ctx['total_collected_all'] = total_collected_all
        ctx['total_expenses_all'] = total_expenses_all
        ctx['overall_balance'] = total_collected_all - total_expenses_all
        ctx['recent_members'] = Member.objects.order_by('-date_joined')[:5]
        ctx['role_distribution'] = Member.objects.values('role').annotate(count=Count('id'))

        return ctx
