from django.contrib import admin

# Register your models here.
from .models import ClassSchedule, LessonPlan, Student, Submission, Teacher, Subject, Level, Assignment, Announcement, WeeklyPlan

admin.site.register(Student)
admin.site.register(Teacher)
admin.site.register(Subject)
admin.site.register(Level)
admin.site.register(Assignment)
admin.site.register(Submission)
admin.site.register(Announcement)
admin.site.register(WeeklyPlan)
admin.site.register(LessonPlan)
admin.site.register(ClassSchedule)
