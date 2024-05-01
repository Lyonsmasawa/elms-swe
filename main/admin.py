from django.contrib import admin

# Register your models here.
from .models import Student, Teacher, Subject, Level, Assignment, Announcement

admin.site.register(Student)
admin.site.register(Teacher)
admin.site.register(Subject)
admin.site.register(Level)
admin.site.register(Assignment)
admin.site.register(Announcement)
