from django.urls import path
from . import views

app_name = 'audits'

urlpatterns = [
    path('', views.audit_list, name='audit_list'),
    path('new/', views.audit_create, name='audit_create'),
    path('<int:pk>/checklist/', views.audit_checklist, name='audit_checklist'),
    path('<int:pk>/', views.audit_detail, name='audit_detail'),
    path('observation/<int:pk>/resolve/', views.observation_resolve, name='observation_resolve'),
]
