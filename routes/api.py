from django.urls import include, path

urlpatterns = [
    path('auth/', include('accounts.urls')),
    path('catalog/', include('catalog.urls')),
    path('sales/', include('sales.urls')),
]



