from django import forms
from .models import StudentDiscussion, TeacherDiscussion


class StudentDiscussionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(StudentDiscussionForm, self).__init__(*args, **kwargs)
        self.fields['content'].required = True
        self.fields['content'].label = ''

    class Meta:
        model = StudentDiscussion
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={'class': 'form-control', 'id': 'content', 'name': 'content', 'placeholder': 'Write message...', 'type': 'text'}),
        }


class TeacherDiscussionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TeacherDiscussionForm, self).__init__(*args, **kwargs)
        self.fields['content'].required = True
        self.fields['content'].label = ''

    class Meta:
        model = TeacherDiscussion
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={'class': 'form-control', 'id': 'content', 'name': 'content', 'placeholder': 'Write message...', 'type': 'text'}),
        }
