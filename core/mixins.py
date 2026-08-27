from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseForbidden
from django.shortcuts import redirect


class RoleRequiredMixin(UserPassesTestMixin):
    allowed_roles = []

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in self.allowed_roles

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('login')
        return HttpResponseForbidden("You don't have permission to access this page.")


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['admin']


class BoardOrAdminMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'board']


class TreasurerOrAboveMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'board', 'treasurer']


class ManagerOrAboveMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'board', 'treasurer', 'manager']


class TreasurerOrBoardOrAdminMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'board', 'treasurer']
