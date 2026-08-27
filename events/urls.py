from django.urls import path
from . import views

urlpatterns = [
    path('', views.EventListView.as_view(), name='event_list'),
    path('<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('add/', views.EventCreateView.as_view(), name='event_add'),
    path('<int:pk>/edit/', views.EventUpdateView.as_view(), name='event_edit'),
    path('<int:pk>/cancel/', views.cancel_event, name='event_cancel'),
    path('<int:pk>/delete/', views.EventDeleteView.as_view(), name='event_delete'),
]
