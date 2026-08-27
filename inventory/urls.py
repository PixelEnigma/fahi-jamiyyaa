from django.urls import path
from . import views

urlpatterns = [
    path('', views.InventoryListView.as_view(), name='inventory_list'),
    path('add/', views.InventoryCreateView.as_view(), name='inventory_add'),
    path('<int:pk>/edit/', views.InventoryUpdateView.as_view(), name='inventory_edit'),
    path('leases/', views.LeaseListView.as_view(), name='lease_list'),
    path('leases/add/', views.LeaseCreateView.as_view(), name='lease_add'),
    path('leases/<int:pk>/return/', views.LeaseReturnView.as_view(), name='lease_return'),
]
