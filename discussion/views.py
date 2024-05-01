from django.shortcuts import redirect, render
from discussion.models import TeacherDiscussion, StudentDiscussion
from main.models import Student, Teacher, Subject
from main.views import is_teacher_authorised, is_student_authorised
from itertools import chain
from .forms import StudentDiscussionForm, TeacherDiscussionForm


# Create your views here.


''' We have two different user models.
    That's why we are filtering the discussions based on the user type and then combining them.'''


def context_list(subject):
    try:
        studentDis = StudentDiscussion.objects.filter(subject=subject)
        teacherDis = TeacherDiscussion.objects.filter(subject=subject)
        discussions = list(chain(studentDis, teacherDis))
        discussions.sort(key=lambda x: x.sent_at, reverse=True)

        for dis in discussions:
            if dis.__class__.__name__ == 'StudentDiscussion':
                dis.author = Student.objects.get(student_id=dis.sent_by_id)
            else:
                dis.author = Teacher.objects.get(teacher_id=dis.sent_by_id)
    except:

        discussions = []

    return discussions


def discussion(request, code):
    if is_student_authorised(request, code):
        subject = Subject.objects.get(code=code)
        student = Student.objects.get(student_id=request.session['student_id'])
        discussions = context_list(subject)
        form = StudentDiscussionForm()
        context = {
            'subject': subject,
            'student': student,
            'discussions': discussions,
            'form': form,
        }
        return render(request, 'discussion/discussion.html', context)

    elif is_teacher_authorised(request, code):
        subject = Subject.objects.get(code=code)
        teacher = Teacher.objects.get(teacher_id=request.session['teacher_id'])
        discussions = context_list(subject)
        form = TeacherDiscussionForm()
        context = {
            'subject': subject,
            'teacher': teacher,
            'discussions': discussions,
            'form': form,
        }
        return render(request, 'discussion/discussion.html', context)
    else:
        return redirect('std_login')


def send(request, code, std_id):
    if is_student_authorised(request, code):
        if request.method == 'POST':
            form = StudentDiscussionForm(request.POST)
            if form.is_valid():
                content = form.cleaned_data['content']
                subject = Subject.objects.get(code=code)
                try:
                    student = Student.objects.get(student_id=std_id)
                except:
                    return redirect('discussion', code=code)
                StudentDiscussion.objects.create(
                    content=content, subject=subject, sent_by=student)
                return redirect('discussion', code=code)
            else:
                return redirect('discussion', code=code)
        else:
            return redirect('discussion', code=code)
    else:
        return render(request, 'std_login.html')


def send_fac(request, code, fac_id):
    if is_teacher_authorised(request, code):
        if request.method == 'POST':
            form = TeacherDiscussionForm(request.POST)
            if form.is_valid():
                content = form.cleaned_data['content']
                subject = Subject.objects.get(code=code)
                try:
                    teacher = Teacher.objects.get(teacher_id=fac_id)
                except:
                    return redirect('discussion', code=code)
                TeacherDiscussion.objects.create(
                    content=content, subject=subject, sent_by=teacher)
                return redirect('discussion', code=code)
            else:
                return redirect('discussion', code=code)
        else:
            return redirect('discussion', code=code)
    else:
        return render(request, 'std_login.html')
