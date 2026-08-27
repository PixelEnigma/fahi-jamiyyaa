from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from .models import Event
from core.mixins import ManagerOrAboveMixin, BoardOrAdminMixin


class EventListView(LoginRequiredMixin, ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 12

    def get_queryset(self):
        qs = Event.objects.all()
        q = self.request.GET.get('q')
        status = self.request.GET.get('status')
        if q:
            qs = qs.filter(title__icontains=q) | qs.filter(location__icontains=q)
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices'] = Event.Status.choices
        return ctx


class EventDetailView(LoginRequiredMixin, DetailView):
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        event = self.get_object()
        ctx['sponsors'] = event.sponsors.select_related().all()
        ctx['photos'] = event.photos.all()
        return ctx


class EventCreateView(ManagerOrAboveMixin, CreateView):
    model = Event
    template_name = 'events/event_form.html'
    fields = ['title', 'description', 'date', 'location', 'image']
    success_url = reverse_lazy('event_list')

    def form_valid(self, form):
        form.instance.organizer = self.request.user
        messages.success(self.request, 'Event created.')
        return super().form_valid(form)


class EventUpdateView(ManagerOrAboveMixin, UpdateView):
    model = Event
    template_name = 'events/event_form.html'
    fields = ['title', 'description', 'date', 'location', 'image', 'status', 'outcome_notes', 'cancellation_reason']
    success_url = reverse_lazy('event_list')

    def form_valid(self, form):
        messages.success(self.request, 'Event updated.')
        return super().form_valid(form)


def cancel_event(request, pk):
    if request.method != 'POST':
        return redirect('event_detail', pk=pk)
    if request.user.role not in ('admin', 'board', 'manager'):
        messages.error(request, 'Permission denied.')
        return redirect('event_detail', pk=pk)
    event = get_object_or_404(Event, pk=pk)
    if event.status == Event.Status.CANCELLED:
        messages.info(request, 'This event is already cancelled.')
        return redirect('event_detail', pk=pk)
    if event.status != Event.Status.PLANNED:
        messages.error(request, 'Only planned events can be cancelled.')
        return redirect('event_detail', pk=pk)
    reason = request.POST.get('reason', '').strip()
    if not reason:
        messages.error(request, 'A cancellation reason is required.')
        return redirect('event_detail', pk=pk)
    event.status = Event.Status.CANCELLED
    event.cancellation_reason = reason
    event.save()
    messages.success(request, f'Event "{event.title}" has been cancelled.')
    return redirect('event_detail', pk=pk)


class EventDeleteView(BoardOrAdminMixin, DeleteView):
    model = Event
    template_name = 'events/event_confirm_delete.html'
    success_url = reverse_lazy('event_list')

    def form_valid(self, form):
        messages.success(self.request, 'Event deleted.')
        return super().form_valid(form)
