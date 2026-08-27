from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import InventoryItem, Lease
from core.mixins import ManagerOrAboveMixin


class InventoryListView(LoginRequiredMixin, ListView):
    model = InventoryItem
    template_name = 'inventory/inventory_list.html'
    context_object_name = 'items'
    paginate_by = 20

    def get_queryset(self):
        qs = InventoryItem.objects.all()
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices'] = InventoryItem.Status.choices
        return ctx


class InventoryCreateView(ManagerOrAboveMixin, CreateView):
    model = InventoryItem
    template_name = 'inventory/inventory_form.html'
    fields = ['name', 'description', 'quantity', 'available_quantity', 'status',
              'purchase_date', 'purchase_price', 'image']
    success_url = reverse_lazy('inventory_list')

    def form_valid(self, form):
        messages.success(self.request, 'Item added to inventory.')
        return super().form_valid(form)


class InventoryUpdateView(ManagerOrAboveMixin, UpdateView):
    model = InventoryItem
    template_name = 'inventory/inventory_form.html'
    fields = ['name', 'description', 'quantity', 'available_quantity', 'status',
              'purchase_date', 'purchase_price', 'image']
    success_url = reverse_lazy('inventory_list')

    def form_valid(self, form):
        messages.success(self.request, 'Inventory item updated.')
        return super().form_valid(form)


class LeaseListView(LoginRequiredMixin, ListView):
    model = Lease
    template_name = 'inventory/lease_list.html'
    context_object_name = 'leases'
    paginate_by = 20

    def get_queryset(self):
        qs = Lease.objects.select_related('item', 'member')
        overdue = self.request.GET.get('overdue')
        q = self.request.GET.get('q')
        if overdue:
            qs = qs.filter(returned_date__isnull=True, expected_return_date__lt=timezone.now())
        if q:
            qs = qs.filter(
                Q(item__name__icontains=q) | Q(member__first_name__icontains=q) |
                Q(member__last_name__icontains=q) | Q(purpose__icontains=q)
            )
        return qs


class LeaseCreateView(ManagerOrAboveMixin, CreateView):
    model = Lease
    template_name = 'inventory/lease_form.html'
    fields = ['item', 'member', 'quantity', 'expected_return_date', 'purpose', 'notes']
    success_url = reverse_lazy('lease_list')

    def form_valid(self, form):
        item = form.cleaned_data['item']
        quantity = form.cleaned_data['quantity']
        if quantity > item.available_quantity:
            form.add_error('quantity', f'Only {item.available_quantity} available.')
            return self.form_invalid(form)
        item.available_quantity -= quantity
        if item.available_quantity == 0:
            item.status = 'leased'
        item.save()
        messages.success(self.request, 'Item leased successfully.')
        return super().form_valid(form)


class LeaseReturnView(ManagerOrAboveMixin, UpdateView):
    model = Lease
    template_name = 'inventory/lease_return.html'
    fields = ['returned_date', 'notes']
    success_url = reverse_lazy('lease_list')

    def get_object(self):
        return Lease.objects.get(pk=self.kwargs['pk'])

    def form_valid(self, form):
        lease = form.save(commit=False)
        lease.returned_date = timezone.now()
        lease.save()
        item = lease.item
        item.available_quantity += lease.quantity
        if item.status == 'leased' and item.available_quantity > 0:
            item.status = 'available'
        item.save()
        messages.success(self.request, 'Item returned successfully.')
        return super().form_valid(form)
