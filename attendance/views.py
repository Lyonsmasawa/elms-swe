from django.contrib import messages
from django.shortcuts import render, redirect
from . models import Attendance
from main.models import Student, Subject, Teacher
from main.views import is_teacher_authorised


def attendance(request, code):
    if is_teacher_authorised(request, code):
        subject = Subject.objects.get(code=code)
        students = Student.objects.filter(subject__code=code)

        return render(request, 'attendance/attendance.html', {'students': students, 'subject': subject, 'teacher': Teacher.objects.get(subject=subject)})


def createRecord(request, code):
    if is_teacher_authorised(request, code):
        if request.method == 'POST':
            date = request.POST['dateCreate']
            subject = Subject.objects.get(code=code)
            students = Student.objects.filter(subject__code=code)
            # check if attendance record already exists for the date
            if Attendance.objects.filter(date=date, subject=subject).exists():
                return render(request, 'attendance/attendance.html', {'code': code, 'students': students, 'subject': subject, 'teacher': Teacher.objects.get(subject=subject), 'error': "Attendance record already exists for the date " + date})
            else:
                for student in students:
                    attendance = Attendance(
                        student=student, subject=subject, date=date, status=False)
                    attendance.save()

                messages.success(
                    request, 'Attendance record created successfully for the date ' + date)
                return redirect('/attendance/' + str(code))
        else:
            return redirect('/attendance/' + str(code))
    else:
        return redirect('std_login')


def loadAttendance(request, code):
    if is_teacher_authorised(request, code):
        if request.method == 'POST':
            date = request.POST['date']
            subject = Subject.objects.get(code=code)
            students = Student.objects.filter(subject__code=code)
            attendance = Attendance.objects.filter(subject=subject, date=date)
            # check if attendance record exists for the date
            if attendance.exists():
                return render(request, 'attendance/attendance.html', {'code': code, 'students': students, 'subject': subject, 'teacher': Teacher.objects.get(subject=subject), 'attendance': attendance, 'date': date})
            else:
                return render(request, 'attendance/attendance.html', {'code': code, 'students': students, 'subject': subject, 'teacher': Teacher.objects.get(subject=subject), 'error': 'Could not load. Attendance record does not exist for the date ' + date})

    else:
        return redirect('std_login')


def submitAttendance(request, code):
    if is_teacher_authorised(request, code):
        try:
            students = Student.objects.filter(subject__code=code)
            subject = Subject.objects.get(code=code)
            if request.method == 'POST':
                date = request.POST['datehidden']
                for student in students:
                    attendance = Attendance.objects.get(
                        student=student, subject=subject, date=date)
                    if request.POST.get(str(student.student_id)) == '1':
                        attendance.status = True
                    else:
                        attendance.status = False
                    attendance.save()
                messages.success(
                    request, 'Attendance record submitted successfully for the date ' + date)
                return redirect('/attendance/' + str(code))

            else:
                return render(request, 'attendance/attendance.html', {'code': code, 'students': students, 'subject': subject, 'teacher': Teacher.objects.get(subject=subject)})
        except:
            return render(request, 'attendance/attendance.html', {'code': code, 'error': "Error! could not save", 'students': students, 'subject': subject, 'teacher': Teacher.objects.get(subject=subject)})
