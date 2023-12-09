from django.http import Http404
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from .forms import *


def handleLogin(request):
  if request.method=='POST':
    form = LoginForm(request.POST)
    if form.is_valid():
      login = form.cleaned_data.get('login')
      password = form.cleaned_data.get('password')
      cursor = connection.cursor()
      cursor.execute("""
                    SELECT last_name, first_name, patronymic, photo_path, worker_id, [Worker roles].[name]
                    FROM [Employee login data] INNER JOIN Workers ON [Employee login data].fk_worker_id = Workers.worker_id
                     INNER JOIN [Worker roles] ON Workers.fk_role_id = [Worker roles].role_id
                    WHERE login = %s AND password = %s 
                    """, [login, password])
      worker = cursor.fetchone()
      if worker is not None:
        request.session['role'] = worker[-1]
        request.session['last_name'] = worker[0]
        request.session['first_name'] = worker[1]
        request.session['patronymic'] = worker[2]
        request.session['photo'] = worker[3]
        request.session['worker_id'] = worker[4]
        if request.session['role'] == 'Координатор':
          response = redirect('coord_page/')
        elif request.session['role'] == 'Вчитель':
          response = redirect('teacher_page/')
        response.set_cookie('logged_in', 'True', secure=True)
        return response
      else:
        messages.error(request, "Неправильно введено ім'я користувача чи пароль")
  else:
    form = LoginForm()
    system_messages = messages.get_messages(request)
    for message in system_messages:
      pass
  return render(request, 'UserEntry.html', {'form': form})

def showCoordPage(request):
  if not request.COOKIES.get('logged_in') or request.session['role'] != 'Координатор':
     raise Http404
  return render(request, 'CoordPage.html', {'w_last_name': request.session['last_name'],
                                            'w_first_name': request.session['first_name'], 
                                            'w_patronymic': request.session['patronymic'],
                                            'w_role': request.session['role'],
                                            'w_photo': request.session['photo']})

def showTeacherPage(request):
  if not request.COOKIES.get('logged_in') or request.session['role'] != 'Вчитель':
     raise Http404
  # response.set_cookie('logged_in', 'True', secure=True)
  # request.session['role'] = 'Вчитель'
  cursor = connection.cursor()
  cursor.execute("""
                 SELECT Classes.class_id, Classes.[name], Specialisations.[name]
                 FROM Specialisations INNER JOIN Classes ON Specialisations.spec_id = Classes.fk_spec_id
                 WHERE EXISTS (
                     SELECT 1
                     FROM [Students in class] INNER JOIN Students ON [Students in class].fk_student_id = Students.student_id
                     WHERE Students.fk_teacher_id = %s AND [Students in class].fk_class_id = Classes.class_id
                     GROUP BY [Students in class].fk_class_id
                     HAVING COUNT([Students in class].fk_student_id) >= 2)
                 """, (request.session['worker_id'],))
  classes = cursor.fetchall()
  is_None = True
  if classes is not None:
    is_None = False
  return render(request, 'TeacherPage.html', {'w_last_name': request.session['last_name'],
                                              'w_first_name': request.session['first_name'], 
                                              'w_patronymic': request.session['patronymic'],
                                              'w_role': request.session['role'],
                                              'w_photo': request.session['photo'],
                                              'is_None': is_None,
                                              'classes': classes})

def showClassPage(request, class_id):
  # if not request.COOKIES.get('logged_in') or request.session['role'] != 'Вчитель' or request.session['role'] != 'Координатор':
  #    raise Http404
  cursor = connection.cursor()
  cursor.execute("""
                 SELECT student_id, last_name, first_name
                 FROM Students INNER JOIN [Students in class]
                  ON Students.student_id = [Students in class].fk_student_id INNER JOIN Classes 
                  ON [Students in class].fk_class_id = Classes.class_id
                 WHERE Students.fk_teacher_id = %s AND Classes.class_id = %s
                 """, [request.session['worker_id'], class_id])
  class_students = cursor.fetchall()
  return render(request, 'ClassPage.html', {'w_last_name': request.session['last_name'],
                                            'w_first_name': request.session['first_name'], 
                                            'w_patronymic': request.session['patronymic'],
                                            'w_role': request.session['role'],
                                            'w_photo': request.session['photo'],
                                            'class_students': class_students,
                                            'class_id': class_id})

def showStudentPage(request, class_id, student_id):
  cursor = connection.cursor()
  cursor.execute("""
                 SELECT *
                 FROM Students
                 WHERE student_id = %s
                 """, (student_id,))
  student_data = cursor.fetchone()
  cursor.execute("""
                 SELECT last_name, first_name, patronymic
                 FROM Workers
                 WHERE worker_id = %s
                 """, (student_data[5],))
  main_teacher = cursor.fetchone()
  print(student_data[-1])
  return render(request, 'StudentPage.html', {'w_last_name': request.session['last_name'],
                                              'w_first_name': request.session['first_name'], 
                                              'w_patronymic': request.session['patronymic'],
                                              'w_role': request.session['role'],
                                              'w_photo': request.session['photo'],
                                              'student_data': student_data,
                                              'main_teacher': main_teacher})

def showTeacherLessonsPage(request):
  cursor = connection.cursor()
  cursor.execute("""
                 SELECT Disciplines.[name], Classes.[name], Lessons.[date], Lessons.start_time, Lessons.end_time
                 FROM Disciplines INNER JOIN Lessons ON discipline_id = FK_discipline_id INNER JOIN Classes
                 ON fk_class_id = class_id INNER JOIN [Lesson statuses] ON fk_status_id = status_id
                 WHERE fk_teacher_id = %s AND fk_status_id = 2
                 """, (request.session['worker_id'],))
  lessons_done = cursor.fetchall()
  biggest_date = max(lessons_done, key=lambda t: t[2])[2]
  biggest_start_time = max(lessons_done, key=lambda t: t[3])[3]
  cursor.execute("""
                 SELECT Disciplines.[name], Classes.[name], Lessons.[date], Lessons.start_time, Lessons.end_time
                 FROM Disciplines INNER JOIN Lessons ON discipline_id = FK_discipline_id INNER JOIN Classes
                 ON fk_class_id = class_id INNER JOIN [Lesson statuses] ON fk_status_id = status_id
                 WHERE fk_teacher_id = %s AND fk_status_id = 1 AND (Lessons.[date] > %s OR (Lessons.[date] = %s AND Lessons.start_time > %s))
                 """, (request.session['worker_id'], biggest_date, biggest_date, biggest_start_time))
  lessons_planned = cursor.fetchall()
  is_None = True
  if len(lessons_planned) > 0:
    is_None = False
  return render(request, 'TeacherLessons.html', {'w_last_name': request.session['last_name'],
                                              'w_first_name': request.session['first_name'], 
                                              'w_patronymic': request.session['patronymic'],
                                              'w_role': request.session['role'],
                                              'w_photo': request.session['photo'],
                                              'lessons_done': lessons_done,
                                              'lessons_planned': lessons_planned,
                                              'is_None': is_None})