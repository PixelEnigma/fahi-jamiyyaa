from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django.db.models import Sum
from .models import Sponsor, Contribution
from core.mixins import TreasurerOrAboveMixin


class SponsorListView(LoginRequiredMixin, ListView):
    model = Sponsor
    template_name = 'sponsors/sponsor_list.html'
    context_object_name = 'sponsors'
    paginate_by = 20

    def get_queryset(self):
        qs = Sponsor.objects.all()
        tier = self.request.GET.get('tier')
        q = self.request.GET.get('q')
        if tier:
            qs = qs.filter(tier=tier)
        if q:
            qs = qs.filter(name__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tier_choices'] = Sponsor.Tier.choices
        ctx['total_contributions'] = Sponsor.objects.aggregate(t=Sum('total_contribution'))['t'] or 0
        return ctx


class SponsorDetailView(LoginRequiredMixin, DetailView):
    model = Sponsor
    template_name = 'sponsors/sponsor_detail.html'
    context_object_name = 'sponsor'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        sponsor = self.get_object()
        from events.models import Event
        ctx['contributions'] = sponsor.contributions.select_related('event').all()
        ctx['events'] = Event.objects.order_by('-date')[:50]
        return ctx


class SponsorCreateView(TreasurerOrAboveMixin, CreateView):
    model = Sponsor
    template_name = 'sponsors/sponsor_form.html'
    fields = ['name', 'contact_person', 'phone', 'email', 'tier', 'logo', 'event', 'notes']
    success_url = reverse_lazy('sponsor_list')

    def form_valid(self, form):
        messages.success(self.request, 'Sponsor added.')
        return super().form_valid(form)


class SponsorUpdateView(TreasurerOrAboveMixin, UpdateView):
    model = Sponsor
    template_name = 'sponsors/sponsor_form.html'
    fields = ['name', 'contact_person', 'phone', 'email', 'tier', 'logo', 'event', 'is_active', 'notes']
    success_url = reverse_lazy('sponsor_list')

    def form_valid(self, form):
        messages.success(self.request, 'Sponsor updated.')
        return super().form_valid(form)


class SponsorDeleteView(TreasurerOrAboveMixin, DeleteView):
    model = Sponsor
    template_name = 'sponsors/sponsor_confirm_delete.html'
    success_url = reverse_lazy('sponsor_list')
    context_object_name = 'sponsor'


def add_contribution(request, sponsor_pk):
    if request.method != 'POST':
        return redirect('sponsor_detail', pk=sponsor_pk)
    if request.user.role not in ('admin', 'board', 'treasurer'):
        messages.error(request, 'Permission denied.')
        return redirect('sponsor_detail', pk=sponsor_pk)

    sponsor = Sponsor.objects.get(pk=sponsor_pk)
    amount = request.POST.get('amount')
    event_id = request.POST.get('event')
    notes = request.POST.get('notes', '')

    try:
        from decimal import Decimal, InvalidOperation
        amount = Decimal(amount)
        if amount <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        messages.error(request, 'Invalid amount.')
        return redirect('sponsor_detail', pk=sponsor_pk)

    Contribution.objects.create(
        sponsor=sponsor,
        event_id=event_id or None,
        amount=amount,
        notes=notes,
    )
    messages.success(request, f'Contribution of {amount} recorded for {sponsor.name}.')
    return redirect('sponsor_detail', pk=sponsor_pk)
