from django.urls import path
from . import views
from .import views_transaction_report
from .import checkStatusviews

urlpatterns = [
   
    path('login/', views.login_view, name='login'),
    path('home/', views.main, name='home'),
    path('', views.main, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('send/', views.send_transaction, name='send_transaction'),
    path('search-locations/', views.search_locations, name='search_locations'),
    path('transaction-report/', views_transaction_report.transaction_report, name='transaction_report'),
    path('StatusUpdate/', checkStatusviews.query_txn_status, name='CheckStatus'),

]