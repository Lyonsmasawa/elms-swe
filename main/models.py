from django.db import models
from froala_editor.fields import FroalaField
# Create your models here.


class Student(models.Model):
    student_id = models.CharField(primary_key=True, max_length=12)
    name = models.CharField(max_length=100, null=False)
    email = models.EmailField(max_length=100, null=True, blank=True)
    password = models.CharField(max_length=255, null=False)
    role = models.CharField(
        default="Student", max_length=100, null=False, blank=True)
    subject = models.ManyToManyField(
        'Subject', related_name='students', blank=True)
    photo = models.ImageField(upload_to='profile_pics', blank=True,
                              null=False, default='profile_pics/default_student.png')
    level = models.ForeignKey(
        'Level', on_delete=models.CASCADE, null=False, blank=False, related_name='students')

    def delete(self, *args, **kwargs):
        if self.photo != 'profile_pics/default_student.png':
            self.photo.delete()
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name_plural = 'Students'

    def __str__(self):
        return f"Student ID: {self.student_id}, Name: {self.name}"


class Teacher(models.Model):
    teacher_id = models.CharField(primary_key=True, max_length=12)
    name = models.CharField(max_length=100, null=False)
    email = models.EmailField(max_length=100, null=True, blank=True)
    password = models.CharField(max_length=255, null=False)
    level = models.ForeignKey(
        'Level', on_delete=models.CASCADE, null=False, related_name='teacher')
    role = models.CharField(
        default="Teacher", max_length=100, null=False, blank=True)
    photo = models.ImageField(upload_to='profile_pics', blank=True,
                              null=False, default='profile_pics/default_teacher.png')

    def delete(self, *args, **kwargs):
        if self.photo != 'profile_pics/default_teacher.png':
            self.photo.delete()
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name_plural = 'Teacher'

    def __str__(self):
        return f"Teacher ID: {self.teacher_id}, Name: {self.name}"


class Level(models.Model):
    level_id = models.CharField(primary_key=True, max_length=12)
    name = models.CharField(max_length=100, null=False)
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Levels'

    def __str__(self):
        return f"Level Id: {self.level_id}, name: {self.name}"

    def student_count(self):
        return self.students.count()

    def teacher_count(self):
        return self.teacher.count()

    def subject_count(self):
        return self.subjects.count()


class Subject(models.Model):
    code = models.CharField(primary_key=True, max_length=12)
    name = models.CharField(max_length=255, null=False, unique=True)
    level = models.ForeignKey(
        Level, on_delete=models.CASCADE, null=False, related_name='subjects')
    teacher = models.ForeignKey(
        Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    studentKey = models.CharField(null=False, max_length=6, unique=True)
    teacherKey = models.CharField(null=False, max_length=6, unique=True)

    class Meta:
        unique_together = ('code', 'level', 'name')
        verbose_name_plural = "Subjects"

    def __str__(self):
        return f"Code: {self.code}, Name: {self.name}, Level: {self.level.name}"


class ClassSchedule(models.Model):
    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name='schedules')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        verbose_name_plural = "Class Schedules"

    def __str__(self):
        return f"{self.subject.name} - {self.start_time} to {self.end_time}"


class WeeklyPlan(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    week_start_date = models.DateField()
    description = models.CharField(max_length=200)
    plan = FroalaField()
    title = models.CharField(max_length=200)

    def __str__(self):
        return f"Weekly Plan for {self.subject.name} by {self.teacher.name} - Week of {self.week_start_date}"


class LessonPlan(models.Model):
    week_plan = models.ForeignKey(WeeklyPlan, on_delete=models.CASCADE)
    plan = FroalaField()
    title = models.CharField(max_length=200)
    time = models.TimeField()
    date = models.DateField()

    def __str__(self):
        return f"Lesson Plan: {self.title}, Week of {self.week_plan.week_start_date}"


class Announcement(models.Model):
    subject_code = models.ForeignKey(
        Subject, on_delete=models.CASCADE, null=False)
    datetime = models.DateTimeField(auto_now_add=True, null=False)
    description = FroalaField()

    class Meta:
        verbose_name_plural = "Announcements"
        ordering = ['-datetime']

    def __str__(self):
        return self.datetime.strftime("%d-%b-%y, %I:%M %p")

    def post_date(self):
        return self.datetime.strftime("%d-%b-%y, %I:%M %p")


class Assignment(models.Model):
    subject_code = models.ForeignKey(
        Subject, on_delete=models.CASCADE, null=False)
    title = models.CharField(max_length=255, null=False)
    description = models.TextField(null=False)
    datetime = models.DateTimeField(auto_now_add=True, null=False)
    deadline = models.DateTimeField(null=False)
    file = models.FileField(upload_to='assignments/', null=True, blank=True)
    marks = models.DecimalField(max_digits=6, decimal_places=2, null=False)

    class Meta:
        verbose_name_plural = "Assignments"
        ordering = ['-datetime']

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        self.file.delete()
        super().delete(*args, **kwargs)

    def post_date(self):
        return self.datetime.strftime("%d-%b-%y, %I:%M %p")

    def due_date(self):
        return self.deadline.strftime("%d-%b-%y, %I:%M %p")


class Submission(models.Model):
    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE, null=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=False)
    file = models.FileField(upload_to='submissions/', null=True, blank=True)
    writing = FroalaField(null=True, blank=True)
    datetime = models.DateTimeField(auto_now_add=True, null=False)
    marks = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)

    def file_name(self):
        return self.file.name.split('/')[-1]

    def time_difference(self):
        difference = self.assignment.deadline - self.datetime
        days = difference.days
        hours = difference.seconds//3600
        minutes = (difference.seconds//60) % 60
        seconds = difference.seconds % 60

        if days == 0:
            if hours == 0:
                if minutes == 0:
                    return str(seconds) + " seconds"
                else:
                    return str(minutes) + " minutes " + str(seconds) + " seconds"
            else:
                return str(hours) + " hours " + str(minutes) + " minutes " + str(seconds) + " seconds"
        else:
            return str(days) + " days " + str(hours) + " hours " + str(minutes) + " minutes " + str(seconds) + " seconds"

    def submission_date(self):
        return self.datetime.strftime("%d-%b-%y, %I:%M %p")

    def delete(self, *args, **kwargs):
        self.file.delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.student.name + " - " + self.assignment.title

    class Meta:
        unique_together = ('assignment', 'student')
        verbose_name_plural = "Submissions"
        ordering = ['datetime']


class Material(models.Model):
    subject_code = models.ForeignKey(
        Subject, on_delete=models.CASCADE, null=False)
    description = models.TextField(max_length=2000, null=False)
    datetime = models.DateTimeField(auto_now_add=True, null=False)
    file = models.FileField(upload_to='materials/', null=True, blank=True)

    class Meta:
        verbose_name_plural = "Materials"
        ordering = ['-datetime']

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        self.file.delete()
        super().delete(*args, **kwargs)

    def post_date(self):
        return self.datetime.strftime("%d-%b-%y, %I:%M %p")
