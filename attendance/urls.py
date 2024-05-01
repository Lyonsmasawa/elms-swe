from django.urls import path
from . import views

urlpatterns = [
    path('attendance/<str:code>', views.attendance, name='attendance'),
    path('createRecord/<str:code>', views.createRecord, name='createRecord'),
    path('submitAttendance/<str:code>',
         views.submitAttendance, name='submitAttendance'),
    path('loadAttendance/<str:code>', views.loadAttendance, name='loadAttendance'),
]
