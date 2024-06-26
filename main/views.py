from django.forms import inlineformset_factory
from django.forms import formset_factory, inlineformset_factory
import datetime
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from .models import ClassSchedule, LessonPlan, Student, Subject, Announcement, Assignment, Submission, Material, Teacher, Level, WeeklyPlan
from django.template.defaulttags import register
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from .forms import AnnouncementForm, AssignmentForm, ClassScheduleForm, LessonPlanForm, MaterialForm, SubmissionForm, WeeklyPlanForm
from django import forms
from django.core import validators
from django.contrib.auth.hashers import make_password,  check_password

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


def std_login(request):
    error_messages = []

    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            id = form.cleaned_data['id']
            password = form.cleaned_data['password']

            # Check if the user is a student
            if Student.objects.filter(student_id=id).exists():
                student = Student.objects.get(student_id=id)
                # Check if the password matches the hashed password in the database
                if check_password(password, student.password):
                    request.session['student_id'] = id
                    return redirect('mySubjects')
                # Check if the password matches the plain text password in the database
                elif password == student.password:
                    request.session['student_id'] = id
                    return redirect('mySubjects')
                else:
                    error_messages.append('Invalid login credentials.')
            # Check if the user is a teacher
            elif Teacher.objects.filter(teacher_id=id).exists():
                teacher = Teacher.objects.get(teacher_id=id)
                # Check if the password matches the hashed password in the database
                if check_password(password, teacher.password):
                    request.session['teacher_id'] = id
                    return redirect('teacherSubjects')
                # Check if the password matches the plain text password in the database
                elif password == teacher.password:
                    request.session['teacher_id'] = id
                    return redirect('teacherSubjects')
                else:
                    error_messages.append('Invalid login credentials.')
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
                class_schedules = ClassSchedule.objects.filter(subject=subject)

            except:
                announcements = None
                assignments = None
                materials = None
                class_schedules = None
            context = {
                'subject': subject,
                'announcements': announcements,
                'assignments': assignments[:3],
                'materials': materials,
                'student': Student.objects.get(student_id=request.session['student_id']),
                'class_schedules': class_schedules,
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

        except:
            announcements = None
            assignments = None
            materials = None

        try:
            teacher_id = request.session['teacher_id']
            teacher = get_object_or_404(Teacher, teacher_id=teacher_id)

            # Filter weekly plans based on the current teacher, subject, and creation date within the current week
            weekly_plans = WeeklyPlan.objects.filter(
                teacher=teacher,
                subject=subject
            ).first()
        except:
            weekly_plans = None

        try:
            class_schedules = ClassSchedule.objects.filter(subject=subject)
        except ClassSchedule.DoesNotExist:
            class_schedules = None

        context = {
            'subject': subject,
            'announcements': announcements,
            'assignments': assignments,
            'materials': materials,
            'teacher': Teacher.objects.get(teacher_id=request.session['teacher_id']),
            'studentCount': studentCount,
            'weekly_plans': weekly_plans,
            'class_schedules': class_schedules,
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


def addWeeklyPlandep(request, code):
    if is_teacher_authorised(request, code):
        LessonPlanFormSet = inlineformset_factory(
            WeeklyPlan, LessonPlan, form=LessonPlanForm, extra=1, exclude=['week_plan'])

        subject = get_object_or_404(Subject, code=code)
        teacher = Teacher.objects.get(teacher_id=request.session['teacher_id'])

        # Get the start date of the current week
        today = datetime.date.today()
        current_week_start = today - datetime.timedelta(days=today.weekday())

        # Check if there's an existing weekly plan for the same week, subject, and teacher
        existing_weekly_plan = WeeklyPlan.objects.filter(
            subject=subject, teacher=teacher, week_start_date=current_week_start).first()

        # Initialize forms
        lesson_formset = LessonPlanFormSet()
        weekly_form = WeeklyPlanForm()
        print(request.method)

        if request.method == 'POST':
            # Check if the lesson plan formset is submitted
            if 'lessonplan_set-TOTAL_FORMS' in request.POST:
                print("1")

                lesson_formset = LessonPlanFormSet(request.POST)
                if existing_weekly_plan:
                    # Associate existing_weekly_plan with formset instances
                    print("2")
                    print(type(existing_weekly_plan))
                    for form in lesson_formset:
                        print("3")
                        form.instance.week_plan = existing_weekly_plan
                        print(type(form.instance.week_plan))

                if lesson_formset.is_valid():
                    print("4")
                    for lesson_form in lesson_formset:
                        print("5")
                        # lesson_form
                        lesson_instance = lesson_form.save()
                    messages.success(
                        request, 'Weekly and Lesson plans added successfully.')
                    return redirect('/teacher/' + str(code))
                else:
                    messages.warning(
                        request, 'Please correct the errors in the lesson plans.')

            else:
                # Save or update the weekly plan
                print("Wwwwswsw")
                weekly_form = WeeklyPlanForm(
                    request.POST, instance=existing_weekly_plan)
                if weekly_form.is_valid():
                    weekly_instance = weekly_form.save(commit=False)
                    weekly_instance.teacher = teacher
                    weekly_instance.subject = subject
                    weekly_instance.week_start_date = current_week_start
                    weekly_instance.save()
                    messages.success(
                        request, 'Weekly plan updated successfully.')
                    return redirect('/teacher/' + str(code))
                else:
                    messages.warning(
                        request, 'Please correct the errors in the weekly plan form.')
        else:
            print("aaaaa")
            if existing_weekly_plan:
                weekly_form = WeeklyPlanForm(instance=existing_weekly_plan)
                lesson_formset = LessonPlanFormSet(
                    instance=existing_weekly_plan)
                print("eeeeee")
            else:
                print("ggggg")
                lesson_formset = LessonPlanFormSet()

        return render(request, 'main/weekly_plan.html', {
            'subject': subject,
            'teacher': teacher,
            'weekly_form': weekly_form,
            'lesson_formset': lesson_formset,
        })
    else:
        return redirect('std_login')


def addWeeklyPlan(request, code):
    if is_teacher_authorised(request, code):
        subject = get_object_or_404(Subject, code=code)
        teacher = Teacher.objects.get(teacher_id=request.session['teacher_id'])

        # Get the start date of the current week
        today = datetime.date.today()
        current_week_start = today - datetime.timedelta(days=today.weekday())

        # Check if there's an existing weekly plan for the same week, subject, and teacher
        existing_weekly_plan = WeeklyPlan.objects.filter(
            subject=subject, teacher=teacher, week_start_date=current_week_start).first()

        if request.method == 'POST':
            # Handle form submission
            weekly_form = WeeklyPlanForm(
                request.POST, instance=existing_weekly_plan)
            if weekly_form.is_valid():
                weekly_instance = weekly_form.save(commit=False)
                weekly_instance.teacher = teacher
                weekly_instance.subject = subject
                weekly_instance.week_start_date = current_week_start
                weekly_instance.save()
                messages.success(
                    request, 'Weekly plan updated successfully.')
                return redirect('/teacher/' + str(code))
            else:
                messages.warning(
                    request, 'Please correct the errors in the weekly plan form.')
        else:
            weekly_form = WeeklyPlanForm(instance=existing_weekly_plan)

        lesson_plans = LessonPlan.objects.filter(
            week_plan=existing_weekly_plan) if existing_weekly_plan else []

        return render(request, 'main/weekly_plan.html', {
            'subject': subject,
            'teacher': teacher,
            'weekly_form': weekly_form,
            'lesson_plans': lesson_plans,
            'existing_weekly_plan': existing_weekly_plan,
        })
    else:
        return redirect('std_login')


def allPlans(request, code):
    if is_teacher_authorised(request, code):
        subject = Subject.objects.get(code=code)
        print("Subject Code:", subject.code)  # Debugging
        print("Teacher ID:", request.session['teacher_id'])  # Debugging
        weekly_plans = WeeklyPlan.objects.filter(subject=subject)
        print("Weekly Plans:", weekly_plans)  # Debugging

        context = {
            'weekly_plans': weekly_plans,
            'subject': subject,
            'teacher': Teacher.objects.get(teacher_id=request.session['teacher_id']),
        }
        return render(request, 'main/all-weekly-plans.html', context)
    else:
        return redirect('std_login')


def viewWeeklyPlan(request, plan_id):
    weekly_plan = get_object_or_404(WeeklyPlan, id=plan_id)
    lesson_plans = weekly_plan.lessonplan_set.all()

    context = {
        'weekly_plan': weekly_plan,
        'lesson_plans': lesson_plans,
        'teacher': Teacher.objects.get(teacher_id=request.session['teacher_id']),
    }

    return render(request, 'main/viewWeeklyPlan.html', context)


def addLessonPlan(request, plan_id):
    weekly_plan = get_object_or_404(WeeklyPlan, id=plan_id)
    if is_teacher_authorised(request, weekly_plan.subject.code):
        teacher = Teacher.objects.get(teacher_id=request.session['teacher_id'])

        subject = Subject.objects.get(code=weekly_plan.subject.code)
        if request.method == 'POST':
            lesson_form = LessonPlanForm(request.POST)
            if lesson_form.is_valid():
                lesson_instance = lesson_form.save(commit=False)
                lesson_instance.week_plan = weekly_plan
                lesson_instance.save()
                messages.success(request, 'Lesson plan added successfully.')
                return redirect('addWeeklyPlan', code=weekly_plan.subject.code)
            else:
                messages.warning(
                    request, 'Please correct the errors in the lesson plan form.')
        else:
            lesson_form = LessonPlanForm()

        return render(request, 'main/add_lesson_plan.html', {
            'weekly_plan': weekly_plan,
            'lesson_form': lesson_form,
            'subject': subject,
            'teacher': teacher,
        })
    else:
        return redirect('std_login')


def editLessonPlan(request, lesson_id):
    lesson_plan = get_object_or_404(LessonPlan, id=lesson_id)
    weekly_plan = lesson_plan.week_plan

    if is_teacher_authorised(request, weekly_plan.subject.code):
        subject = Subject.objects.get(code=weekly_plan.subject.code)
        teacher = Teacher.objects.get(teacher_id=request.session['teacher_id'])
        if request.method == 'POST':
            lesson_form = LessonPlanForm(request.POST, instance=lesson_plan)
            if lesson_form.is_valid():
                lesson_form.save()
                messages.success(request, 'Lesson plan updated successfully.')
                return redirect('addWeeklyPlan', code=weekly_plan.subject.code)
            else:
                messages.warning(
                    request, 'Please correct the errors in the lesson plan form.')
        else:
            lesson_form = LessonPlanForm(instance=lesson_plan)

        return render(request, 'main/edit_lesson_plan.html', {
            'lesson_form': lesson_form,
            'lesson_plan': lesson_plan,
            'weekly_plan': weekly_plan,
            'subject': subject,
            'teacher': teacher,
        })
    else:
        return redirect('std_login')


def allClassSchedules(request, code):
    if is_teacher_authorised(request, code):
        subject = Subject.objects.get(code=code)
        class_schedules = ClassSchedule.objects.filter(subject=subject)

        context = {
            'class_schedules': class_schedules,
            'subject': subject,
            'teacher': Teacher.objects.get(teacher_id=request.session['teacher_id']),
        }
        return render(request, 'main/all-class-schedules.html', context)
    else:
        return redirect('std_login')


def editSchedule(request, code):
    schedule = get_object_or_404(ClassSchedule, id=code)
    print(schedule)
    if is_teacher_authorised(request, code):
        print
        if request.method == 'POST':
            form = ClassScheduleForm(request.POST, instance=schedule)
            if form.is_valid():
                form.save()
                return redirect('allClassSchedules', subject_code=schedule.subject.code)
        else:
            form = ClassScheduleForm(instance=schedule)

        context = {
            'form': form,
            'schedule': schedule,
            'teacher': Teacher.objects.get(teacher_id=request.session['teacher_id']),
        }

        return render(request, 'main/edit_class_schedule.html', context)

    else:
        return redirect('std_login')


def editSchedule(request, code):
    schedule = get_object_or_404(ClassSchedule, id=code)

    # Check if the teacher is authorized to edit this schedule
    if not is_teacher_authorised(request, schedule.subject.code):
        return redirect('std_login')

    if request.method == 'POST':
        form = ClassScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            # Redirect to the schedule list page
            return redirect('allClassSchedules', code=schedule.subject.code)
    else:
        form = ClassScheduleForm(instance=schedule)

    context = {
        'form': form,
        'schedule': schedule,
        # Use get() to avoid KeyError if teacher_id doesn't exist
        'teacher': request.session.get('teacher_id'),
    }

    return render(request, 'main/edit_class_schedule.html', context)


def addSchedule(request, code):
    if is_teacher_authorised(request, code):
        subject = Subject.objects.get(code=code)

        if request.method == 'POST':
            form = ClassScheduleForm(request.POST)
            if form.is_valid():
                schedule = form.save(commit=False)
                schedule.subject = subject
                schedule.save()
                return redirect('/teacher/' + str(code))

        else:
            form = ClassScheduleForm()

        context = {
            'form': form,
            'subject': subject,
            # Assuming you have a Teacher model
            'teacher': Teacher.objects.get(teacher_id=request.session['teacher_id']),
        }
        return render(request, 'main/add_schedule.html', context)
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
    subject = get_object_or_404(Subject, code=code)
    if is_student_authorised(request, code):
        assignment = get_object_or_404(
            Assignment, subject_code=subject.code, id=id)
        student = get_object_or_404(
            Student, student_id=request.session['student_id'])
        try:
            submission = Submission.objects.get(
                assignment=assignment, student=student)
        except Submission.DoesNotExist:
            submission = None

        context = {
            'assignment': assignment,
            'subject': subject,
            'submission': submission,
            'time': datetime.datetime.now(),
            'student': student,
            'subjects': student.subject.all(),
            'form':  SubmissionForm()
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

            if request.method == 'POST':
                form = SubmissionForm(request.POST, request.FILES)
                if form.is_valid():
                    submission = form.save(commit=False)
                    submission.assignment = assignment
                    submission.student = Student.objects.get(
                        student_id=request.session['student_id'])
                    submission.status = 'Submitted'
                    submission.save()
                    return HttpResponseRedirect(request.path_info)
            else:
                form = SubmissionForm()

            submission = Submission.objects.get(assignment=assignment, student=Student.objects.get(
                student_id=request.session['student_id']))
            context = {
                'assignment': assignment,
                'subject': subject,
                'submission': submission,
                'time': datetime.datetime.now(),
                'student': Student.objects.get(student_id=request.session['student_id']),
                'subjects': Student.objects.get(student_id=request.session['student_id']).subject.all(),
                'form': form
            }
            print(context)
            print(1)

            return render(request, 'main/assignment-portal.html', context)
        else:
            return redirect('std_login')
    except:
        return HttpResponseRedirect(request.path_info)


def viewSubmission(request, code, id):
    print(1)
    try:
        subject = Subject.objects.get(code=code)
        if is_teacher_authorised(request, code):
            assignment = get_object_or_404(
                Assignment, subject_code_id=code, id=id)
            submissions = Submission.objects.filter(
                assignment_id=assignment.id)
            total_students = Student.objects.filter(subject=subject).count()
            teacher = Teacher.objects.get(
                teacher_id=request.session['teacher_id'])
            subjects = Subject.objects.filter(
                teacher_id=request.session['teacher_id'])

            context = {
                'subject': subject,
                'submissions': submissions,
                'assignment': assignment,
                'totalStudents': total_students,
                'teacher': teacher,
                'subjects': subjects
            }

            return render(request, 'main/assignment-view.html', context)
        else:
            return redirect('std_login')
    except Subject.DoesNotExist:
        return redirect('/teacher/' + str(code))
    except Assignment.DoesNotExist:
        return redirect('/teacher/' + str(code))


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
            subjects = Subject.objects.filter(level=student.level)
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
        student = Student.objects.get(student_id=request.session['student_id'])
        if request.method == 'POST':
            old_password = request.POST['oldPassword']
            new_password = request.POST['newPassword']
            
            # Check if the provided old password matches either the hashed password or plain text password stored in the database
            if check_password(old_password, student.password) or old_password == student.password:
                # Hash the new password before saving
                student.password = make_password(new_password)
                student.save()
                messages.success(request, 'Password was changed successfully')
                return redirect('/profile/' + str(student.student_id))
            else:
                messages.error(request, 'Old password is incorrect. Please try again')
                return redirect('/changePassword/')
        else:
            return render(request, 'main/changePassword.html', {'student': student})
    else:
        return redirect('std_login')


def changePasswordTeacher(request):
    if request.session.get('teacher_id'):
        teacher = Teacher.objects.get(teacher_id=request.session['teacher_id'])
        if request.method == 'POST':
            old_password = request.POST['oldPassword']
            new_password = request.POST['newPassword']
            
            # Check if the provided old password matches either the hashed password or plain text password stored in the database
            if check_password(old_password, teacher.password) or old_password == teacher.password:
                # Hash the new password before saving
                teacher.password = make_password(new_password)
                teacher.save()
                messages.success(request, 'Password was changed successfully')
                return redirect('/teacherProfile/' + str(teacher.teacher_id))
            else:
                messages.error(request, 'Old password is incorrect. Please try again')
                return redirect('/changePasswordTeacher/')
        else:
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
