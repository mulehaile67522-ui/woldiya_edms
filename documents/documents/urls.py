from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/',  views.login_view,  name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Documents
    path('documents/',                          views.document_list,    name='document_list'),
    path('documents/new/',                      views.document_create,  name='document_create'),
    path('documents/<int:pk>/',                 views.document_detail,  name='document_detail'),
    path('documents/<int:pk>/edit/',            views.document_update,  name='document_update'),
    path('documents/<int:pk>/delete/',          views.document_delete,  name='document_delete'),
    path('documents/<int:pk>/status/',          views.update_status,    name='update_status'),
    path('documents/<int:pk>/download/',        views.document_download, name='document_download'),
    path('documents/<int:pk>/print/',           views.document_print,   name='document_print'),
    path('documents/<int:pk>/qr/',              views.document_qr,      name='document_qr'),
    path('documents/overdue/',                  views.overdue_documents, name='overdue_documents'),

    # Reports
    path('reports/', views.reports, name='reports'),

    # Notifications
    path('notifications/',                       views.notifications_view,        name='notifications'),
    path('notifications/mark-all/',              views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/<int:pk>/read/',         views.mark_notification_read,    name='mark_notification_read'),

    # Audit trail
    path('audit/', views.audit_trail, name='audit_trail'),

    # Capacity building
    path('capacity-building/', views.capacity_building, name='capacity_building'),

    # User management (staff only)
    path('users/', views.user_management, name='user_management'),

    # Categories
    path('categories/',                   views.category_list,   name='category_list'),
    path('categories/new/',               views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/',     views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/',   views.category_delete, name='category_delete'),

    # API helpers
    path('api/suggest-reference/', views.suggest_reference, name='suggest_reference'),

    # Profile & My Documents
    path('profile/',      views.profile_view,  name='profile'),
    path('my-documents/', views.my_documents,  name='my_documents'),
]
