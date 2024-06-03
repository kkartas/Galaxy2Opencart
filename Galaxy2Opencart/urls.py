from django.urls import path, include
from . import views


urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('products/', views.products_view, name='products_view'),
    path('orders/', views.orders_view, name='orders_view'),
    path('categories/', views.categories_view, name='categories_view'),
    path('image/', views.image_view, name='image_view'),
    path('balance/', views.balance_view, name='balance_view'),
    path('answers/', views.answer_form_view, name='answer_form_view'),
    path('messages/', views.get_latest_messages, name='get_latest_messages'),
    path('clear_logs/', views.clear_logs, name='clear_logs'),
    # Add any other paths you might need for your application.
]

