from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django.http import JsonResponse
from django import forms
import secrets
from .models import Member
from core.mixins import BoardOrAdminMixin, AdminRequiredMixin


class MemberListView(LoginRequiredMixin, ListView):
    model = Member
    template_name = 'members/member_list.html'
    context_object_name = 'members'
    paginate_by = 20

    def get_queryset(self):
        qs = Member.objects.all()
        q = self.request.GET.get('q')
        role = self.request.GET.get('role')
        if q:
            qs = qs.filter(first_name__icontains=q) | qs.filter(last_name__icontains=q) | qs.filter(phone__icontains=q)
        if role:
            qs = qs.filter(role=role)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['role_choices'] = Member.Role.choices
        return ctx


class MemberDetailView(LoginRequiredMixin, DetailView):
    model = Member
    template_name = 'members/member_detail.html'
    context_object_name = 'member'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        member = self.get_object()
        ctx['payments'] = member.payments.all()[:12]
        ctx['leases'] = member.leases.all()[:5]
        return ctx


class MemberCreateView(BoardOrAdminMixin, CreateView):
    model = Member
    template_name = 'members/member_form.html'
    fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'role',
              'join_date', 'monthly_dues', 'is_active_member', 'avatar']
    success_url = reverse_lazy('member_list')

    def form_valid(self, form):
        password = self.request.POST.get('password', 'default123')
        form.instance.set_password(password)
        messages.success(self.request, 'Member created successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Add Member'
        return ctx


class MemberUpdateView(BoardOrAdminMixin, UpdateView):
    model = Member
    template_name = 'members/member_form.html'
    fields = ['first_name', 'last_name', 'email', 'phone', 'role',
              'join_date', 'monthly_dues', 'is_active_member', 'avatar']
    success_url = reverse_lazy('member_list')

    def form_valid(self, form):
        messages.success(self.request, 'Member updated successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Edit Member'
        return ctx


class MemberDeleteView(AdminRequiredMixin, DeleteView):
    model = Member
    template_name = 'members/member_confirm_delete.html'
    success_url = reverse_lazy('member_list')
    context_object_name = 'member'

    def form_valid(self, form):
        messages.success(self.request, 'Member deleted successfully.')
        return super().form_valid(form)


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['first_name', 'last_name', 'email', 'phone', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 dark:bg-gray-800 dark:text-gray-100 dark:border-gray-600 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 dark:bg-gray-800 dark:text-gray-100 dark:border-gray-600 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 dark:bg-gray-800 dark:text-gray-100 dark:border-gray-600 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border border-gray-300 dark:bg-gray-800 dark:text-gray-100 dark:border-gray-600 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none'}),
            'avatar': forms.FileInput(attrs={'class': 'w-full text-sm text-gray-500 dark:text-gray-400 file:mr-3 file:py-1.5 file:px-3 file:border-0 file:bg-primary-50 dark:file:bg-primary-900/50 file:text-primary-700 dark:file:text-primary-300 file:font-medium file:text-xs hover:file:bg-primary-100 dark:hover:file:bg-primary-800'}),
        }


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'members/profile.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['profile_form'] = ProfileUpdateForm(instance=self.request.user)
        ctx['password_form'] = PasswordChangeForm(self.request.user)
        return ctx

    def post(self, request, *args, **kwargs):
        if 'profile_submit' in request.POST:
            form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile updated successfully.')
            else:
                messages.error(request, 'Please correct the errors below.')
        elif 'password_submit' in request.POST:
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password changed successfully.')
            else:
                messages.error(request, 'Please correct the errors below.')
        return redirect('profile')


def generate_telegram_code(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    code = secrets.token_hex(4).upper()
    request.user.telegram_link_code = code
    request.user.telegram_id = None
    request.user.save()
    return JsonResponse({'code': code})


def unlink_telegram(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    request.user.telegram_id = None
    request.user.telegram_link_code = None
    request.user.save()
    return JsonResponse({'ok': True})
