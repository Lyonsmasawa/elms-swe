import datetime
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from .models import Student, Subject, Announcement, Assignment, Submission, Material, Teacher, Level, WeeklyPlan
from django.template.defaulttags import register
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from .forms import AnnouncementForm, AssignmentForm, MaterialForm, WeeklyPlanForm
from django import forms
from django.core import validators


from django import forms


class LoginForm(forms.Form):
    id = forms.CharField(label='ID', max_length=12, validators=[
                         validators.RegexValidator(r'\S', 'Please enter a valid number.')])
    password = forms.CharField(widget=forms.PasswordInput)


def is_student_authorised(request, code):
    subject = Subject.objects.get(code=code)
    if request.session.get('student_id') and subject in Student.objects.get(student_id=request.session['student_id']).subject.all():
        return True
    else:
        return False


def is_teacher_authorised(request, code):
    if request.session.get('teacher_id') and code in Subject.objects.filter(teacher_id=request.session['teacher_id']).values_list('code', flat=True):
        return True
    else:
        return False


# Custom Login page for both student and teacher
def std_login(request):
    error_messages = []

    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            id = form.cleaned_data['id']
            password = form.cleaned_data['password']

            if Student.objects.filter(student_id=id, password=password).exists():
                request.session['student_id'] = id
                return redirect('mySubjects')
            elif Teacher.objects.filter(teacher_id=id, password=password).exists():
                request.session['teacher_id'] = id
                return redirect('teacherSubjects')
            else:
                error_messages.append('Invalid login credentials.')
        else:
            error_messages.append('Invalid form data.')
    else:
        form = LoginForm()

    if 'student_id' in request.session:
        return redirect('/my/')
    elif 'teacher_id' in request.session:
        return redirect('/teacherSubjects/')

    context = {'form': form, 'error_messages': error_messages}
    return render(request, 'login_page.html', context)

# Clears the session on logout


def std_logout(request):
    request.session.flush()
    return redirect('std_login')


# Display all subjects (student view)
def mySubjects(request):
    try:
        if request.session.get('student_id'):
            student = Student.objects.get(
                student_id=request.session['student_id'])
            subjects = student.subject.all()
            teacher = student.subject.all().values_list('teacher_id', flat=True)

            context = {
                'subjects': subjects,
                'student': student,
                'teacher': teacher
            }

            return render(request, 'main/mySubjects.html', context)
        else:
            return redirect('std_login')
    except:
        return render(request, 'error.html')


# Display all subjects (teacher view)
def teacherSubjects(request):
    try:
        if request.session['teacher_id']:
            teacher = Teacher.objects.get(
                teacher_id=request.session['teacher_id'])
            subjects = Subject.objects.filter(
                teacher_id=request.session['teacher_id'])
            # Student count of each subject to show on the teacher page
            studentCount = Subject.objects.all().annotate(student_count=Count('students'))

            studentCountDict = {}

            for subject in studentCount:
                studentCountDict[subject.code] = subject.student_count

            @register.filter
            def get_item(dictionary, subject_code):
                return dictionary.get(subject_code)

            context = {
                'subjects': subjects,
                'teacher': teacher,
                'studentCount': studentCountDict
            }

            return render(request, 'main/teacherSubjects.html', context)

        else:
            return redirect('std_login')
    except:

        return redirect('std_login')


# Particular subject page (student view)
def subject_page(request, code):
    try:
        subject = Subject.objects.get(code=code)
        if is_student_authorised(request, code):
            try:
                announcements = Announcement.objects.filter(
                    subject_code=subject)
                assignments = Assignment.objects.filter(
                    subject_code=subject.code)
                materials = Material.objects.filter(subject_code=subject.code)

            except:
                announcements = None
                assignments = None
                materials = None

            context = {
                'subject': subject,
                'announcements': announcements,
                'assignments': assignments[:3],
                'materials': materials,
                'student': Student.objects.get(student_id=request.session['student_id'])
            }

            return render(request, 'main/subject.html', context)

        else:
            return redirect('std_login')
    except:
        return render(request, 'error.html')


# Particular subject page (teacher view)
def subject_page_teacher(request, code):
    subject = Subject.objects.get(code=code)
    if request.session.get('teacher_id'):
        try:
            announcements = Announcement.objects.filter(subject_code=subject)
            assignments = Assignment.objects.filter(
                subject_code=subject.code)
            materials = Material.objects.filter(subject_code=subject.code)
            studentCount = Student.objects.filter(subject=subject).count()
            print(assignments)

        except:
            announcements = None
            assignments = None
            materials = None

        try:
            today = datetime.timezone.now().date()
            start_of_week = today - datetime.timedelta(days=today.weekday())
            end_of_week = start_of_week + datetime.timedelta(days=6)
            teacher_id = request.session['teacher_id']
            teacher = get_object_or_404(Teacher, teacher_id=teacher_id)

            # Filter weekly plans based on the current teacher, subject, and creation date within the current week
            weekly_plans = WeeklyPlan.objects.filter(
                teacher=teacher,
                subject=subject,
                created_at__date__range=[start_of_week, end_of_week]
            )

        except:
            weekly_plans = None

        context = {
            'subject': subject,
            'announcements': announcements,
            'assignments': assignments,
            'materials': materials,
            'teacher': Teacher.objects.get(teacher_id=request.session['teacher_id']),
            'studentCount': studentCount,
            'weekly_plans': weekly_plans,
        }

        return render(request, 'main/teacher_subject.html', context)
    else:
        return redirect('std_login')


def error(request):
    return render(request, 'error.html')


# Display user profile(student & teacher)
def profile(request, id):
    try:
        if request.session['student_id'] == id:
            student = Student.objects.get(student_id=id)
            return render(request, 'main/profile.html', {'student': student})
        else:
            return redirect('std_login')
    except:
        try:
            if request.session['teacher_id'] == id:
                teacher = Teacher.objects.get(teacher_id=id)
                return render(request, 'main/teacher_profile.html', {'teacher': teacher})
            else:
                return redirect('std_login')
        except:
            return render(request, 'error.html')


def addAnnouncement(request, code):
    if is_teacher_authorised(request, code):
        if request.method == 'POST':
            form = AnnouncementForm(request.POST)
            form.instance.subject_code = Subject.objects.get(code=code)
            if form.is_valid():
                form.save()
                messages.success(
                    request, 'Announcement added successfully.')
                return redirect('/teacher/' + str(code))
        else:
            form = AnnouncementForm()
        return render(request, 'main/announcement.html', {'subject': Subject.objects.get(code=code), 'teacher': Teacher.objects.get(teacher_id=request.session['teacher_id']), 'form': form})
    else:
        return redirect('std_login')


def deleteAnnouncement(request, code, id):
    if is_teacher_authorised(request, code):
        try:
            announcement = Announcement.objects.get(subject_code=code, id=id)
            announcement.delete()
            messages.warning(request, 'Announcement deleted successfully.')
            return redirect('/teacher/' + str(code))
        except:
            return redirect('/teacher/' + str(code))
    else:
        return redirect('std_login')


def editAnnouncement(request, code, id):
    if is_teacher_authorised(request, code):
        announcement = Announcement.objects.get(subject_code_id=code, id=id)
        form = AnnouncementForm(instance=announcement)
        context = {
            'announcement': announcement,
            'subject': Subject.objects.get(code=code),
            'teacher': Teacher.objects.get(teacher_id=request.session['teacher_id']),
            'form': form
        }
        return render(request, 'main/update-announcement.html', context)
    else:
        return redirect('std_login')


def updateAnnouncement(request, code, id):
    if is_teacher_authorised(request, code):
        try:
            announcement = Announcement.objects.get(
                subject_code_id=code, id=id)
            form = AnnouncementForm(request.POST, instance=announcement)
            if form.is_valid():
                form.save()
                messages.info(request, 'Announcement updated successfully.')
                return redirect('/teacher/' + str(code))
        except:
            return redirect('/teacher/' + str(code))

    else:
        return redirect('std_login')


def addWeeklyPlan(request, code):
    if is_teacher_authorised(request, code):
        if request.method == 'POST':
            form = WeeklyPlanForm(request.POST)
            form.instance.subject = Subject.objects.get(code=code)
            form.instance.teacher = Teacher.objects.get(
                teacher_id=request.session['teacher_id'])
            if form.is_valid():
                form.save()
                messages.success(request, 'Weekly plan added successfully.')
                return redirect('/teacher/' + str(code))
        else:
            form = WeeklyPlanForm()
        return render(request, 'main/weekly_plan.html', {'subject': Subject.objects.get(code=code), 'teacher': Teacher.objects.get(teacher_id=request.session['teacher_id']), 'form': form})
    else:
        return redirect('std_login')


def allPlans(request, code):
    if is_teacher_authorised(request, code):
        subject = Subject.objects.get(code=code)
        weekly_plans = WeeklyPlan.objects.filter(subject=subject)

        context = {
            'weekly_plans': weekly_plans,
            'subject': subject,
            'teacher': Teacher.objects.get(teacher_id=request.session['teacher_id']),
        }
        return render(request, 'main/all-weekly-plans.html', context)
    else:
        return redirect('std_login')


def addAssignment(request, code):
    if is_teacher_authorised(request, code):
        if request.method == 'POST':
            form = AssignmentForm(request.POST, request.FILES)
            form.instance.subject_code = Subject.objects.get(code=code)
            if form.is_valid():
                form.save()
                messages.success(request, 'Assignment added successfully.')
                return redirect('/teacher/' + str(code))
        else:
            form = AssignmentForm()
        return render(request, 'main/assignment.html', {'subject': Subject.objects.get(code=code), 'teacher': Teacher.objects.get(teacher_id=request.session['teacher_id']), 'form': form})
    else:
        return redirect('std_login')


def assignmentPage(request, code, id):
    subject = Subject.objects.get(code=code)
    if is_student_authorised(request, code):
        assignment = Assignment.objects.get(subject_code=subject.code, id=id)
        try:

            submission = Submission.objects.get(assignment=assignment, student=Student.objects.get(
                student_id=request.session['student_id']))

            context = {
                'assignment': assignment,
                'subject': subject,
                'submission': submission,
                'time': datetime.datetime.now(),
                'student': Student.objects.get(student_id=request.session['student_id']),
                'subjects': Student.objects.get(student_id=request.session['student_id']).subject.all()
            }

            return render(request, 'main/assignment-portal.html', context)

        except:
            submission = None

        context = {
            'assignment': assignment,
            'subject': subject,
            'submission': submission,
            'time': datetime.datetime.now(),
            'student': Student.objects.get(student_id=request.session['student_id']),
            'subjects': Student.objects.get(student_id=request.session['student_id']).subject.all()
        }

        return render(request, 'main/assignment-portal.html', context)
    else:

        return redirect('std_login')


def allAssignments(request, code):
    if is_teacher_authorised(request, code):
        subject = Subject.objects.get(code=code)
        assignments = Assignment.objects.filter(subject_code=subject)
        studentCount = Student.objects.filter(subject=subject).count()

        context = {
            'assignments': assignments,
            'subject': subject,
            'teacher': Teacher.objects.get(teacher_id=request.session['teacher_id']),
            'studentCount': studentCount

        }
        return render(request, 'main/all-assignments.html', context)
    else:
        return redirect('std_login')


def allAssignmentsSTD(request, code):
    if is_student_authorised(request, code):
        subject = Subject.objects.get(code=code)
        assignments = Assignment.objects.filter(subject_code=subject)
        context = {
            'assignments': assignments,
            'subject': subject,
            'student': Student.objects.get(student_id=request.session['student_id']),

        }
        return render(request, 'main/all-assignments-std.html', context)
    else:
        return redirect('std_login')


def addSubmission(request, code, id):
    try:
        subject = Subject.objects.get(code=code)
        if is_student_authorised(request, code):
            # check if assignment is open
            assignment = Assignment.objects.get(
                subject_code=subject.code, id=id)
            if assignment.deadline < datetime.datetime.now():

                return redirect('/assignment/' + str(code) + '/' + str(id))

            if request.method == 'POST' and request.FILES['file']:
                assignment = Assignment.objects.get(
                    subject_code=subject.code, id=id)
                submission = Submission(assignment=assignment, student=Student.objects.get(
                    student_id=request.session['student_id']), file=request.FILES['file'],)
                submission.status = 'Submitted'
                submission.save()
                return HttpResponseRedirect(request.path_info)
            else:
                assignment = Assignment.objects.get(
                    subject_code=subject.code, id=id)
                submission = Submission.objects.get(assignment=assignment, student=Student.objects.get(
                    student_id=request.session['student_id']))
                context = {
                    'assignment': assignment,
                    'subject': subject,
                    'submission': submission,
                    'time': datetime.datetime.now(),
                    'student': Student.objects.get(student_id=request.session['student_id']),
                    'subjects': Student.objects.get(student_id=request.session['student_id']).subject.all()
                }

                return render(request, 'main/assignment-portal.html', context)
        else:
            return redirect('std_login')
    except:
        return HttpResponseRedirect(request.path_info)


def viewSubmission(request, code, id):
    subject = Subject.objects.get(code=code)
    if is_teacher_authorised(request, code):
        try:
            assignment = Assignment.objects.get(subject_code_id=code, id=id)
            submissions = Submission.objects.filter(
                assignment_id=assignment.id)

            context = {
                'subject': subject,
                'submissions': submissions,
                'assignment': assignment,
                'totalStudents': len(Student.objects.filter(subject=subject)),
                'teacher': Teacher.objects.get(teacher_id=request.session['teacher_id']),
                'subjects': Subject.objects.filter(teacher_id=request.session['teacher_id'])
            }

            return render(request, 'main/assignment-view.html', context)

        except:
            return redirect('/teacher/' + str(code))
    else:
        return redirect('std_login')


def gradeSubmission(request, code, id, sub_id):
    try:
        subject = Subject.objects.get(code=code)
        if is_teacher_authorised(request, code):
            if request.method == 'POST':
                assignment = Assignment.objects.get(
                    subject_code_id=code, id=id)
                submissions = Submission.objects.filter(
                    assignment_id=assignment.id)
                submission = Submission.objects.get(
                    assignment_id=id, id=sub_id)
                submission.marks = request.POST['marks']
                if request.POST['marks'] == 0:
                    submission.marks = 0
                submission.save()
                return HttpResponseRedirect(request.path_info)
            else:
                assignment = Assignment.objects.get(
                    subject_code_id=code, id=id)
                submissions = Submission.objects.filter(
                    assignment_id=assignment.id)
                submission = Submission.objects.get(
                    assignment_id=id, id=sub_id)

                context = {
                    'subject': subject,
                    'submissions': submissions,
                    'assignment': assignment,
                    'totalStudents': len(Student.objects.filter(subject=subject)),
                    'teacher': Teacher.objects.get(teacher_id=request.session['teacher_id']),
                    'subjects': Subject.objects.filter(teacher_id=request.session['teacher_id'])
                }

                return render(request, 'main/assignment-view.html', context)

        else:
            return redirect('std_login')
    except:
        return redirect('/error/')


def addSubjectMaterial(request, code):
    if is_teacher_authorised(request, code):
        if request.method == 'POST':
            form = MaterialForm(request.POST, request.FILES)
            form.instance.subject_code = Subject.objects.get(code=code)
            if form.is_valid():
                form.save()
                messages.success(request, 'New subject material added')
                return redirect('/teacher/' + str(code))
            else:
                return render(request, 'main/subject-material.html', {'subject': Subject.objects.get(code=code), 'teacher': Teacher.objects.get(teacher_id=request.session['teacher_id']), 'form': form})
        else:
            form = MaterialForm()
            return render(request, 'main/subject-material.html', {'subject': Subject.objects.get(code=code), 'teacher': Teacher.objects.get(teacher_id=request.session['teacher_id']), 'form': form})
    else:
        return redirect('std_login')


def deleteSubjectMaterial(request, code, id):
    if is_teacher_authorised(request, code):
        subject = Subject.objects.get(code=code)
        subject_material = Material.objects.get(subject_code=subject, id=id)
        subject_material.delete()
        messages.warning(request, 'Subject material deleted')
        return redirect('/teacher/' + str(code))
    else:
        return redirect('std_login')


def subjects(request):
    if request.session.get('student_id') or request.session.get('teacher_id'):

        subjects = Subject.objects.all()
        if request.session.get('student_id'):
            student = Student.objects.get(
                student_id=request.session['student_id'])
        else:
            student = None
        if request.session.get('teacher_id'):
            teacher = Teacher.objects.get(
                teacher_id=request.session['teacher_id'])
        else:
            teacher = None

        enrolled = student.subject.all() if student else None
        accessed = Subject.objects.filter(
            teacher_id=teacher.teacher_id) if teacher else None

        context = {
            'teacher': teacher,
            'subjects': subjects,
            'student': student,
            'enrolled': enrolled,
            'accessed': accessed
        }

        return render(request, 'main/all-subjects.html', context)

    else:
        return redirect('std_login')


def levels(request):
    if request.session.get('student_id') or request.session.get('teacher_id'):
        levels = Level.objects.all()
        if request.session.get('student_id'):
            student = Student.objects.get(
                student_id=request.session['student_id'])
        else:
            student = None
        if request.session.get('teacher_id'):
            teacher = Teacher.objects.get(
                teacher_id=request.session['teacher_id'])
        else:
            teacher = None
        context = {
            'teacher': teacher,
            'student': student,
            'deps': levels
        }

        return render(request, 'main/levels.html', context)

    else:
        return redirect('std_login')


def access(request, code):
    if request.session.get('student_id'):
        subject = Subject.objects.get(code=code)
        student = Student.objects.get(student_id=request.session['student_id'])
        if request.method == 'POST':
            if (request.POST['key']) == str(subject.studentKey):
                student.subject.add(subject)
                student.save()
                return redirect('/my/')
            else:
                messages.error(request, 'Invalid key')
                return HttpResponseRedirect(request.path_info)
        else:
            return render(request, 'main/access.html', {'subject': subject, 'student': student})

    else:
        return redirect('std_login')


def search(request):
    if request.session.get('student_id') or request.session.get('teacher_id'):
        if request.method == 'GET' and request.GET['q']:
            q = request.GET['q']
            subjects = Subject.objects.filter(Q(code__icontains=q) | Q(
                name__icontains=q) | Q(teacher__name__icontains=q))

            if request.session.get('student_id'):
                student = Student.objects.get(
                    student_id=request.session['student_id'])
            else:
                student = None
            if request.session.get('teacher_id'):
                teacher = Teacher.objects.get(
                    teacher_id=request.session['teacher_id'])
            else:
                teacher = None
            enrolled = student.subject.all() if student else None
            accessed = Subject.objects.filter(
                teacher_id=teacher.teacher_id) if teacher else None

            context = {
                'subjects': subjects,
                'teacher': teacher,
                'student': student,
                'enrolled': enrolled,
                'accessed': accessed,
                'q': q
            }
            return render(request, 'main/search.html', context)
        else:
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        return redirect('std_login')


def changePasswordPrompt(request):
    if request.session.get('student_id'):
        student = Student.objects.get(student_id=request.session['student_id'])
        return render(request, 'main/changePassword.html', {'student': student})
    elif request.session.get('teacher_id'):
        teacher = Teacher.objects.get(teacher_id=request.session['teacher_id'])
        return render(request, 'main/changePasswordTeacher.html', {'teacher': teacher})
    else:
        return redirect('std_login')


def changePhotoPrompt(request):
    if request.session.get('student_id'):
        student = Student.objects.get(student_id=request.session['student_id'])
        return render(request, 'main/changePhoto.html', {'student': student})
    elif request.session.get('teacher_id'):
        teacher = Teacher.objects.get(teacher_id=request.session['teacher_id'])
        return render(request, 'main/changePhotoTeacher.html', {'teacher': teacher})
    else:
        return redirect('std_login')


def changePassword(request):
    if request.session.get('student_id'):
        student = Student.objects.get(
            student_id=request.session['student_id'])
        if request.method == 'POST':
            if student.password == request.POST['oldPassword']:
                # New and confirm password check is done in the client side
                student.password = request.POST['newPassword']
                student.save()
                messages.success(request, 'Password was changed successfully')
                return redirect('/profile/' + str(student.student_id))
            else:
                messages.error(
                    request, 'Password is incorrect. Please try again')
                return redirect('/changePassword/')
        else:
            return render(request, 'main/changePassword.html', {'student': student})
    else:
        return redirect('std_login')


def changePasswordTeacher(request):
    if request.session.get('teacher_id'):
        teacher = Teacher.objects.get(
            teacher_id=request.session['teacher_id'])
        if request.method == 'POST':
            if teacher.password == request.POST['oldPassword']:
                # New and confirm password check is done in the client side
                teacher.password = request.POST['newPassword']
                teacher.save()
                messages.success(request, 'Password was changed successfully')
                return redirect('/teacherProfile/' + str(teacher.teacher_id))
            else:
                print('error')
                messages.error(
                    request, 'Password is incorrect. Please try again')
                return redirect('/changePasswordTeacher/')
        else:
            print(teacher)
            return render(request, 'main/changePasswordTeacher.html', {'teacher': teacher})
    else:
        return redirect('std_login')


def changePhoto(request):
    if request.session.get('student_id'):
        student = Student.objects.get(
            student_id=request.session['student_id'])
        if request.method == 'POST':
            if request.FILES['photo']:
                student.photo = request.FILES['photo']
                student.save()
                messages.success(request, 'Photo was changed successfully')
                return redirect('/profile/' + str(student.student_id))
            else:
                messages.error(
                    request, 'Please select a photo')
                return redirect('/changePhoto/')
        else:
            return render(request, 'main/changePhoto.html', {'student': student})
    else:
        return redirect('std_login')


def changePhotoTeacher(request):
    if request.session.get('teacher_id'):
        teacher = Teacher.objects.get(
            teacher_id=request.session['teacher_id'])
        if request.method == 'POST':
            if request.FILES['photo']:
                teacher.photo = request.FILES['photo']
                teacher.save()
                messages.success(request, 'Photo was changed successfully')
                return redirect('/teacherProfile/' + str(teacher.teacher_id))
            else:
                messages.error(
                    request, 'Please select a photo')
                return redirect('/changePhotoTeacher/')
        else:
            return render(request, 'main/changePhotoTeacher.html', {'teacher': teacher})
    else:
        return redirect('std_login')


def guestStudent(request):
    request.session.flush()
    try:
        student = Student.objects.get(name='Guest Student')
        request.session['student_id'] = str(student.student_id)
        return redirect('mySubjects')
    except:
        return redirect('std_login')


def guestTeacher(request):
    request.session.flush()
    try:
        teacher = Teacher.objects.get(name='Guest Teacher')
        request.session['teacher_id'] = str(teacher.teacher_id)
        return redirect('teacherSubjects')
    except:
        return redirect('std_login')
