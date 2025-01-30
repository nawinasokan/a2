from django.urls import path
from . import views


urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('upload/', views.upload, name='upload'), 
    path('user_creation/', views.user_creation, name='user_creation'),
    path('update_user/<str:username>/', views.update_user, name='update_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('menu_permission/', views.menu_permission, name='menu_permission'),
    path('delete-menu-permission/<int:permission_id>/', views.delete_menu_permission, name='delete_menu_permission'),
    path('update-menu-permission/<int:permission_id>/', views.update_menu_permission, name='update_menu_permission'),
    path('l3_production/', views.l3_production, name='l3_production'),
    path('l3-submit-task/', views.l3_submit_task, name='l3_submit_task'),
    path('l2_production/', views.l2_production, name='l2_production'),
    path('l2-submit-task/', views.l2_submit_task, name='l2_submit_task'),
    path('l1_production/', views.l1_production, name='l1_production'),
    path('l1-submit-task/', views.l1_submit_task, name='l1_submit_task'),
    path('production_report/', views.production_report, name='production_report'),
    path('production_result/l1/', views.production_result, {'level': 'l1'}, name='l1_production_result'),
    path('production_result/l2/', views.production_result, {'level': 'l2'}, name='l2_production_result'),
    path('production_result/l3/', views.production_result, {'level': 'l3'}, name='l3_production_result'),
]