from django.views.generic import ListView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from django.shortcuts import redirect, get_object_or_404
from datetime import date
from .models import Payment, Expense
from members.models import Member
from core.mixins import TreasurerOrAboveMixin
from core.models import Setting


class CollectionView(LoginRequiredMixin, TemplateView):
    template_name = 'finances/collection.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        now = timezone.now()
        year = int(self.request.GET.get('year', now.year))
        month = int(self.request.GET.get('month', now.month))
        selected_date = date(year, month, 1)

        members = Member.objects.filter(is_active_member=True).order_by('first_name')
        rows = []
        total_minimum = 0
        total_paid = 0
        for m in members:
            status, paid, minimum = Payment.status_for_member_month(m, selected_date)
            total_minimum += minimum
            total_paid += paid
            rows.append({
                'member': m,
                'minimum': minimum,
                'paid': paid,
                'status': status,
                'remaining': max(minimum - paid, 0),
            })

        ctx.update({
            'rows': rows,
            'selected_year': year,
            'selected_month': month,
            'selected_date': selected_date,
            'total_minimum': total_minimum,
            'total_paid': total_paid,
            'total_pending': total_minimum - total_paid,
            'due_day': Setting.get('default_due_day', '10'),
            'years': list(range(now.year - 2, now.year + 3)),
        })
        return ctx


def record_payment(request):
    if request.method != 'POST':
        return redirect('collection')
    if request.user.role not in ('admin', 'board', 'treasurer'):
        messages.error(request, 'Permission denied.')
        return redirect('collection')

    member_id = request.POST.get('member_id')
    month_str = request.POST.get('month')
    amount = request.POST.get('amount')
    notes = request.POST.get('notes', '')

    if not all([member_id, month_str, amount]):
        messages.error(request, 'Missing required fields.')
        return redirect(request.META.get('HTTP_REFERER', 'collection'))

    try:
        from decimal import Decimal, InvalidOperation
        amount = Decimal(amount)
        if amount <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        messages.error(request, 'Invalid amount.')
        return redirect(request.META.get('HTTP_REFERER', 'collection'))

    year, month = month_str.split('-')
    month_date = date(int(year), int(month), 1)

    receipt_file = request.FILES.get('receipt')

    Payment.objects.create(
        member_id=member_id,
        month=month_date,
        amount=amount,
        paid_date=timezone.now().date(),
        received_by=request.user,
        notes=notes,
        receipt=receipt_file,
    )
    member = Member.objects.get(pk=member_id)
    messages.success(request, f'Payment of {amount} recorded for {member.get_full_name()}.')
    return redirect(request.META.get('HTTP_REFERER', 'collection'))


def delete_payment(request, pk):
    if request.user.role not in ('admin', 'board', 'treasurer'):
        messages.error(request, 'Permission denied.')
        return redirect('collection')
    payment = get_object_or_404(Payment, pk=pk)
    payment.delete()
    messages.info(request, 'Payment deleted.')
    return redirect(request.META.get('HTTP_REFERER', 'collection'))


class PaymentHistoryView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'finances/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 30

    def get_queryset(self):
        qs = Payment.objects.select_related('member', 'received_by')
        member = self.request.GET.get('member')
        month = self.request.GET.get('month')
        if member:
            qs = qs.filter(
                Q(member__first_name__icontains=member) |
                Q(member__last_name__icontains=member) |
                Q(member__username__icontains=member)
            )
        if month:
            try:
                y, m = month.split('-')
                qs = qs.filter(month=date(int(y), int(m), 1))
            except (ValueError, IndexError):
                pass
        return qs.order_by('-month', '-paid_date')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['total_collected'] = Payment.objects.aggregate(t=Sum('amount'))['t'] or 0
        return ctx


class ExpenseListView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = 'finances/expense_list.html'
    context_object_name = 'expenses'
    paginate_by = 20

    def get_queryset(self):
        qs = Expense.objects.select_related('paid_by')
        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category=category)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['category_choices'] = Expense.Category.choices
        ctx['total_expenses'] = Expense.objects.aggregate(t=Sum('amount'))['t'] or 0
        return ctx


class ExpenseCreateView(TreasurerOrAboveMixin, CreateView):
    model = Expense
    template_name = 'finances/expense_form.html'
    fields = ['description', 'category', 'amount', 'date', 'paid_by', 'receipt', 'notes']
    success_url = reverse_lazy('expense_list')

    def form_valid(self, form):
        messages.success(self.request, 'Expense recorded.')
        return super().form_valid(form)


class ExpenseUpdateView(TreasurerOrAboveMixin, UpdateView):
    model = Expense
    template_name = 'finances/expense_form.html'
    fields = ['description', 'category', 'amount', 'date', 'paid_by', 'receipt', 'notes']
    success_url = reverse_lazy('expense_list')

    def form_valid(self, form):
        messages.success(self.request, 'Expense updated.')
        return super().form_valid(form)
