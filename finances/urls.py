from django.urls import path
from . import views
from . import export

urlpatterns = [
    path('collection/', views.CollectionView.as_view(), name='collection'),
    path('collection/record/', views.record_payment, name='record_payment'),
    path('collection/delete/<int:pk>/', views.delete_payment, name='delete_payment'),
    path('payments/', views.PaymentHistoryView.as_view(), name='payment_list'),
    path('expenses/', views.ExpenseListView.as_view(), name='expense_list'),
    path('expenses/add/', views.ExpenseCreateView.as_view(), name='expense_add'),
    path('expenses/<int:pk>/edit/', views.ExpenseUpdateView.as_view(), name='expense_edit'),
    path('payments/export/csv/', export.export_payments_csv, name='payment_export_csv'),
    path('expenses/export/csv/', export.export_expenses_csv, name='expense_export_csv'),
]
