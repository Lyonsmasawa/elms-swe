from django.urls import path
from . import views

urlpatterns = [
    path('discussion/<str:code>', views.discussion, name='discussion'),
    path('send/<str:code>/<str:std_id>', views.send, name='send'),
    path('message/<str:code>/<str:fac_id>', views.send_fac, name='send_fac'),
]