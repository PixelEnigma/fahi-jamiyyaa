from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Notice
from core.mixins import ManagerOrAboveMixin, BoardOrAdminMixin


class NoticeListView(LoginRequiredMixin, ListView):
    model = Notice
    template_name = 'notices/notice_list.html'
    context_object_name = 'notices'
    paginate_by = 20

    def get_queryset(self):
        qs = Notice.objects.select_related('created_by')
        priority = self.request.GET.get('priority')
        q = self.request.GET.get('q')
        if priority:
            qs = qs.filter(priority=priority)
        if q:
            qs = qs.filter(title__icontains=q) | qs.filter(body__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['priority_choices'] = Notice.Priority.choices
        return ctx


class NoticeCreateView(ManagerOrAboveMixin, CreateView):
    model = Notice
    template_name = 'notices/notice_form.html'
    fields = ['title', 'body', 'priority', 'pinned']
    success_url = reverse_lazy('notice_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Notice posted.')
        return super().form_valid(form)


class NoticeUpdateView(ManagerOrAboveMixin, UpdateView):
    model = Notice
    template_name = 'notices/notice_form.html'
    fields = ['title', 'body', 'priority', 'pinned']
    success_url = reverse_lazy('notice_list')

    def form_valid(self, form):
        messages.success(self.request, 'Notice updated.')
        return super().form_valid(form)


class NoticeDeleteView(BoardOrAdminMixin, DeleteView):
    model = Notice
    template_name = 'notices/notice_confirm_delete.html'
    success_url = reverse_lazy('notice_list')

    def form_valid(self, form):
        messages.success(self.request, 'Notice deleted.')
        return super().form_valid(form)
