from django.urls import path
from . import views
from . import reports
from . import reminders

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('reports/', reports.ReportView.as_view(), name='reports'),
    path('reports/export/', reports.ReportExportView.as_view(), name='reports_export'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('reminders/send/', reminders.send_reminders, name='send_reminders'),
]
