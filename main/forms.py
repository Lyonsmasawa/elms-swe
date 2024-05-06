from django import forms
from froala_editor.widgets import FroalaEditor
from .models import Announcement, Assignment, ClassSchedule, LessonPlan, Material, Submission, WeeklyPlan
from datetime import date, timedelta, timezone


class AnnouncementForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AnnouncementForm, self).__init__(*args, **kwargs)
        self.fields['description'].required = True
        self.fields['description'].label = ''

    class Meta:
        model = Announcement
        fields = ['description']
        widgets = {
            'description': FroalaEditor(),
        }


class AssignmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AssignmentForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True
            field.label = ''
        self.fields['file'].required = False

    class Meta:
        model = Assignment
        fields = ('title', 'description', 'deadline', 'marks', 'file')
        widgets = {
            'description': FroalaEditor(),
            'title': forms.TextInput(attrs={'class': 'form-control mt-1', 'id': 'title', 'name': 'title', 'placeholder': 'Title'}),
            'deadline': forms.DateTimeInput(attrs={'class': 'form-control mt-1', 'id': 'deadline', 'name': 'deadline', 'type': 'datetime-local'}),
            'marks': forms.NumberInput(attrs={'class': 'form-control mt-1', 'id': 'marks', 'name': 'marks', 'placeholder': 'Marks'}),
            'file': forms.FileInput(attrs={'class': 'form-control mt-1', 'id': 'file', 'name': 'file', 'aria-describedby': 'file', 'aria-label': 'Upload'}),
        }


class WeeklyPlanForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(WeeklyPlanForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True
            field.label = ''
            if field.widget.attrs.get('placeholder') is None:
                field.widget.attrs['placeholder'] = field.label.capitalize()

        # Set initial value for week_start_date
        self.fields['week_start_date'].initial = self.get_start_of_week()

    def get_start_of_week(self):
        # Get the current date
        today = date.today()
        # Calculate the start of the current week (assuming Monday is the start of the week)
        start_of_week = today - timedelta(days=today.weekday())
        return start_of_week

    class Meta:
        model = WeeklyPlan
        fields = ('week_start_date',  'title', 'description', 'plan')
        widgets = {
            'week_start_date': forms.DateInput(attrs={'class': 'form-control mt-1', 'type': 'date', 'readonly': True}),
            'description': forms.TextInput(attrs={'class': 'form-control mt-1', 'placeholder': 'Description'}),
            'title': forms.TextInput(attrs={'class': 'form-control mt-1', 'placeholder': 'Title'}),
            'plan': FroalaEditor(),
        }


class LessonPlanForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(LessonPlanForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False
            field.label = ''
            if field.widget.attrs.get('placeholder') is None:
                field.widget.attrs['placeholder'] = field.label.capitalize()

    class Meta:
        model = LessonPlan
        fields = ('title', 'plan', 'time', 'date')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control mt-1', 'placeholder': 'Lesson Tilte'}),
            'plan': FroalaEditor(),
            'time': forms.TimeInput(attrs={'class': 'form-control mt-1', 'type': 'time', 'placeholder': 'Time'}),
            'date': forms.DateInput(attrs={'class': 'form-control mt-1', 'type': 'date', 'placeholder': 'Date'}),
        }


class MaterialForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(MaterialForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True
            field.label = ""
        self.fields['file'].required = False

    class Meta:
        model = Material
        fields = ('description', 'file')
        widgets = {
            'description': FroalaEditor(),
            'file': forms.FileInput(attrs={'class': 'form-control', 'id': 'file', 'name': 'file', 'aria-describedby': 'file', 'aria-label': 'Upload'}),
        }


class SubmissionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SubmissionForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True
            field.label = ""
        self.fields['file'].required = False

    class Meta:
        model = Submission
        fields = ('writing', 'file')
        widgets = {
            'writing': FroalaEditor(),
            'file': forms.FileInput(attrs={'class': 'form-control', 'id': 'file', 'name': 'file', 'aria-describedby': 'file', 'aria-label': 'Upload'}),
        }

class ClassScheduleForm(forms.ModelForm):
    class Meta:
        model = ClassSchedule
        exclude = ['subject']
