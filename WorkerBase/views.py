from django.http import Http404
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.urls import reverse
from django.core.files.storage import default_storage

from WorkerBase.img_path_handler import Rename
from .forms import *
from datetime import date, datetime
from .models import *


def handleLogin(request):
  if request.session.keys():
    for key in list(request.session.keys()):
      del request.session[key]
  if request.method=='POST':
    form = LoginForm(request.POST)
    if form.is_valid():
      login = form.cleaned_data.get('login')
      password = form.cleaned_data.get('password')
      cursor = connection.cursor()
      cursor.execute("""
                    SELECT last_name, first_name, patronymic, photo_path, worker_id, [Worker roles].[name]
                    FROM [Worker entry data] INNER JOIN Workers ON [Worker entry data].fk_worker_id = Workers.worker_id
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

def showTeacherPage(request):
  if not request.COOKIES.get('logged_in') or request.session['role'] != 'Вчитель':
     raise Http404
  cursor = connection.cursor()
  cursor.execute("""
                 EXEC selectTeacherClasses @teacher_id=%s
                 """, (request.session['worker_id'],))
  classes = cursor.fetchall()
  is_None = True
  if classes is not None:
    is_None = False
  return render(request, 'TeacherPage.html', {'w_last_name': request.session['last_name'],
                                              'w_first_name': request.session['first_name'], 
                                              'w_role': request.session['role'],
                                              'w_photo': request.session['photo'],
                                              'is_None': is_None,
                                              'classes': classes})

def showClassPage(request, class_id):
  cursor = connection.cursor()
  cursor.execute("""
                 SELECT student_id, last_name, first_name
                 FROM Students INNER JOIN [Students in class]
                  ON Students.student_id = [Students in class].fk_student_id INNER JOIN Classes 
                  ON [Students in class].fk_class_id = Classes.class_id
                 WHERE Classes.class_id = %s
                 """, [class_id,])
  class_students = cursor.fetchall()
  if request.session['role'] == 'Вчитель':
    response = render(request, 'ClassPage.html', {'w_last_name': request.session['last_name'],
                                            'w_first_name': request.session['first_name'], 
                                            'w_role': request.session['role'],
                                            'w_photo': request.session['photo'],
                                            'class_students': class_students,
                                            'class_id': class_id})
  elif request.session['role'] == 'Координатор':
    response = render(request, 'CoordClassPage.html', {'w_last_name': request.session['last_name'],
                                            'w_first_name': request.session['first_name'], 
                                            'w_role': request.session['role'],
                                            'w_photo': request.session['photo'],
                                            'class_students': class_students,
                                            'class_id': class_id})
  return response

def showStudentPage(request, class_id, student_id):
  cursor = connection.cursor()
  student_data = Students.objects.get(student_id = student_id)
  cursor.execute("""
                 SELECT last_name, first_name, patronymic
                 FROM Workers INNER JOIN Classes ON worker_id = fk_teacher_id
                 WHERE class_id = %s
                 """, (class_id,))
  main_teacher = Workers.objects.select_related('classes').filter(classes__class_id=class_id).values('last_name', 'first_name', 'patronymic').get()
  return render(request, 'StudentPage.html', {'w_last_name': request.session['last_name'],
                                              'w_first_name': request.session['first_name'], 
                                              'w_role': request.session['role'],
                                              'w_photo': request.session['photo'],
                                              'student_data': student_data,
                                              'main_teacher': main_teacher})

def showTeacherLessonsPage(request):
  cursor = connection.cursor()
  cursor.execute("""
                 SELECT Disciplines.[name], Classes.[name], Lessons.[date], Lessons.start_time, Lessons.end_time, Lessons.lesson_id
                 FROM Disciplines INNER JOIN Lessons ON discipline_id = fk_discipline_id INNER JOIN Classes
                 ON fk_class_id = class_id INNER JOIN [Lesson statuses] ON fk_status_id = status_id
                 WHERE Lessons.fk_teacher_id = %s AND fk_status_id = 2 AND Lessons.[date] >= %s AND Lessons.[date] <= %s
                 """, (request.session['worker_id'], request.session['from_date'], request.session['to_date']))
  lessons_done = cursor.fetchall()
  cursor.execute("""
                 SELECT Disciplines.[name], Classes.[name], Lessons.[date], Lessons.start_time, Lessons.end_time
                 FROM Disciplines INNER JOIN Lessons ON discipline_id = fk_discipline_id INNER JOIN Classes
                 ON fk_class_id = class_id INNER JOIN [Lesson statuses] ON fk_status_id = status_id
                 WHERE Lessons.fk_teacher_id = %s AND fk_status_id = 1 AND Lessons.[date] >= %s AND Lessons.[date] <= %s
                 """, (request.session['worker_id'], request.session['from_date'], request.session['to_date']))
  lessons_planned = cursor.fetchall()
  return render(request, 'TeacherLessons.html', {'w_last_name': request.session['last_name'],
                                              'w_first_name': request.session['first_name'], 
                                              'w_role': request.session['role'],
                                              'w_photo': request.session['photo'],
                                              'lessons_done': lessons_done,
                                              'lessons_planned': lessons_planned,})

def showStudentStatsPage(request, class_id):
  cursor = connection.cursor()
  cursor.execute("""
                 SELECT Students.last_name, Students.first_name, Classes.[name], Disciplines.[name],
                 [Evaluated elements].[name], Lessons.[date], Lessons.start_time, grade, Students.student_id, Lessons.lesson_id, [Student grades].grade_id
                 FROM Students INNER JOIN [Student grades] 
                           ON Students.student_id = [Student grades].fk_student_id INNER JOIN Lessons
                           ON [Student grades].fk_lesson_id = Lessons.lesson_id INNER JOIN Disciplines
                           ON Lessons.fk_discipline_id = Disciplines.discipline_id INNER JOIN Classes
                           ON Lessons.fk_class_id = Classes.class_id INNER JOIN [Evaluated elements]
                           ON [Evaluated elements].element_id = [Student grades].fk_eval_elt
                 WHERE Lessons.fk_teacher_id = %s AND Lessons.fk_status_id = 2 AND Classes.class_id = %s AND Lessons.[date] >= %s AND Lessons.[date] <= %s
                 """, (request.session['worker_id'], class_id, request.session['from_date'], request.session['to_date']))
  student_grades = cursor.fetchall()
  cursor.execute("""
                 SELECT Students.last_name, Students.first_name, Classes.[name],
                 Disciplines.[name], Lessons.[date], Lessons.start_time, presence, Students.student_id, Lessons.lesson_id, [Student attendances].attend_id
                 FROM Students INNER JOIN [Student attendances]
                           ON Students.student_id = [Student attendances].fk_student_id INNER JOIN Lessons
                           ON [Student attendances].fk_lesson_id = Lessons.lesson_id INNER JOIN Disciplines
                           ON Lessons.fk_discipline_id = Disciplines.discipline_id INNER JOIN Classes
                           ON Lessons.fk_class_id = Classes.class_id
                 WHERE Lessons.fk_teacher_id = %s AND Lessons.fk_status_id = 2 AND Classes.class_id = %s AND Lessons.[date] >= %s AND Lessons.[date] <= %s
                 """, (request.session['worker_id'], class_id, request.session['from_date'], request.session['to_date']))
  student_attend = cursor.fetchall()
  present_count = 0
  absent_count = 0
  for student in student_attend:
    if student[6]=='відвідано':
      present_count+=1
    else:
      absent_count+=1
  chart_data = [present_count, absent_count]
  labels = ['відвідано', 'пропущено']
  return render(request, 'StudentStats.html', {'w_last_name': request.session['last_name'],
                                              'w_first_name': request.session['first_name'], 
                                              'w_role': request.session['role'],
                                              'w_photo': request.session['photo'],
                                              'student_grades': student_grades,
                                              'student_attend': student_attend,
                                              'id_class': class_id,
                                              'chart_data': chart_data,
                                              'labels': labels})

def showStudentCompPage(request, class_id):
  cursor = connection.cursor()
  cursor.execute("""
                 SELECT last_name, first_name, [Discipline skills].[name], Disciplines.[name], [Competence levels].[name],
                 [Student competencies].[date_time], [Student competencies].stud_comp_id 
                 FROM Disciplines INNER JOIN [Discipline skills] 
                             ON Disciplines.discipline_id = [Discipline skills].fk_discipline_id INNER JOIN [Student competencies]
                             ON [Discipline skills].skill_id = [Student competencies].fk_skill_id INNER JOIN Students
                             ON [Student competencies].fk_student_id = Students.student_id INNER JOIN [Students in class]
                             ON Students.student_id = [Students in class].fk_student_id, [Competence levels]
                 WHERE [Students in class].fk_class_id = %s AND [Student competencies].fk_level_id = [Competence levels].level_id
                       AND [Student competencies].[date_time] >= %s AND [Student competencies].[date_time] <= %s
                 ORDER BY [Student competencies].[date_time] ASC
                 """, (class_id, request.session['from_date'], request.session['to_date'] ))
  student_comp = cursor.fetchall()
  cursor.execute("""
                 SELECT [name]
                 FROM Classes
                 WHERE class_id = %s
                 """, (class_id,))
  class_name = cursor.fetchone()
  return render(request, 'StudentComp.html', {'w_last_name': request.session['last_name'],
                                              'w_first_name': request.session['first_name'], 
                                              'w_role': request.session['role'],
                                              'w_photo': request.session['photo'],
                                              'student_comp': student_comp,
                                              'class_name': class_name[0],
                                              'id_class': class_id})

def addStudentGrade(request, class_id):
  cursor = connection.cursor()
  if request.method=='POST':
    form = StudentGradeForm(request.POST)
    cursor.execute("""
                   SELECT student_id, last_name, first_name, patronymic
                   FROM Students INNER JOIN [Students in class] 
                                       ON Students.student_id = [Students in class].fk_student_id INNER JOIN Classes 
                                       ON [Students in class].fk_class_id = Classes.class_id
                   WHERE Classes.class_id = %s
                   """, (class_id,))
    students = cursor.fetchall()
    form.fields['student'].choices = [(student[0], f'{student[1]} {student[2]} {student[3]}') for student in students]
    cursor.execute("""
                   SELECT element_id, [name]
                   FROM [Evaluated elements]
                   """)
    eval_elts = cursor.fetchall()
    form.fields['eval_elt'].choices = [(eval_elt[0], eval_elt[1]) for eval_elt in eval_elts]
    cursor.execute("""
                   SELECT Lessons.lesson_id, Disciplines.[name], Lessons.[date], Lessons.start_time, Lessons.end_time
                   FROM Disciplines INNER JOIN Lessons ON discipline_id = fk_discipline_id INNER JOIN Classes
                                   ON fk_class_id = class_id INNER JOIN [Lesson statuses] ON fk_status_id = status_id
                   WHERE Classes.fk_teacher_id = %s AND fk_status_id = 2 AND Classes.class_id = %s AND Lessons.[date] >= %s AND Lessons.[date] <= %s
                   """, (request.session['worker_id'], class_id, request.session['from_date'], request.session['to_date']))
    lessons = cursor.fetchall()
    form.fields['lesson'].choices = [(lesson[0], f'Дисципліна: {lesson[1]}, Дата: {lesson[2]}, Час початку: {lesson[3]}, Час кінця: {lesson[4]}') for lesson in lessons]
    if form.is_valid():
      fk_student_id = form.cleaned_data.get('student')
      grade = form.cleaned_data.get('grade')
      fk_eval_elt = form.cleaned_data.get('eval_elt')
      fk_lesson_id = form.cleaned_data.get('lesson')
      cursor.execute("""
                     INSERT INTO [Student grades](fk_student_id, grade, fk_eval_elt, fk_lesson_id) VALUES
                     (%s, %s, %s, %s)""", (fk_student_id, grade, fk_eval_elt, fk_lesson_id))
      if cursor.rowcount > 0:
        response = redirect('show-teacher-student-stats-page', class_id=class_id)
        return response
  else:
    form = StudentGradeForm()
    cursor.execute("""
                   SELECT student_id, last_name, first_name, patronymic
                   FROM Students INNER JOIN [Students in class] 
                                       ON Students.student_id = [Students in class].fk_student_id INNER JOIN Classes 
                                       ON [Students in class].fk_class_id = Classes.class_id
                   WHERE Classes.class_id = %s
                   """, (class_id,))
    students = cursor.fetchall()
    form.fields['student'].choices = [(student[0], f'{student[1]} {student[2]} {student[3]}') for student in students]
    cursor.execute("""
                   SELECT element_id, [name]
                   FROM [Evaluated elements]
                   """)
    eval_elts = cursor.fetchall()
    form.fields['eval_elt'].choices = [(eval_elt[0], eval_elt[1]) for eval_elt in eval_elts]
    cursor.execute("""
                   SELECT Lessons.lesson_id, Disciplines.[name], Lessons.[date], Lessons.start_time, Lessons.end_time
                   FROM Disciplines INNER JOIN Lessons ON discipline_id = fk_discipline_id INNER JOIN Classes
                                   ON fk_class_id = class_id INNER JOIN [Lesson statuses] ON fk_status_id = status_id
                   WHERE Classes.fk_teacher_id = %s AND fk_status_id = 2 AND Classes.class_id = %s AND Lessons.[date] >= %s AND Lessons.[date] <= %s
                   """, (request.session['worker_id'], class_id, request.session['from_date'], request.session['to_date']))
    lessons = cursor.fetchall()
    form.fields['lesson'].choices = [(lesson[0], f'Дисципліна: {lesson[1]}, Дата: {lesson[2]}, Час початку: {lesson[3]}, Час кінця: {lesson[4]}') for lesson in lessons]
    system_messages = messages.get_messages(request)
    for message in system_messages:
      pass
  return render(request, 'FormPage.html', {'w_last_name': request.session['last_name'],
                                           'w_first_name': request.session['first_name'], 
                                           'w_role': request.session['role'],
                                           'w_photo': request.session['photo'],
                                           'form': form})

def editStudentGrade(request, class_id, grade_id):
  cursor = connection.cursor()
  if request.method=='POST':
    form = StudentGradeForm(request.POST)
    cursor.execute("""
                   SELECT student_id, last_name, first_name, patronymic
                   FROM Students INNER JOIN [Students in class] 
                                       ON Students.student_id = [Students in class].fk_student_id INNER JOIN Classes 
                                       ON [Students in class].fk_class_id = Classes.class_id
                   WHERE Classes.class_id = %s
                   """, (class_id,))
    students = cursor.fetchall()
    form.fields['student'].choices = [(student[0], f'{student[1]} {student[2]} {student[3]}') for student in students]
    cursor.execute("""
                   SELECT element_id, [name]
                   FROM [Evaluated elements]
                   """)
    eval_elts = cursor.fetchall()
    form.fields['eval_elt'].choices = [(eval_elt[0], eval_elt[1]) for eval_elt in eval_elts]
    cursor.execute("""
                   SELECT Lessons.lesson_id, Disciplines.[name], Lessons.[date], Lessons.start_time, Lessons.end_time
                   FROM Disciplines INNER JOIN Lessons ON discipline_id = fk_discipline_id INNER JOIN Classes
                                   ON fk_class_id = class_id INNER JOIN [Lesson statuses] ON fk_status_id = status_id
                   WHERE Classes.fk_teacher_id = %s AND fk_status_id = 2 AND Classes.class_id = %s AND Lessons.[date] >= %s AND Lessons.[date] <= %s
                   """, (request.session['worker_id'], class_id, request.session['from_date'], request.session['to_date']))
    lessons = cursor.fetchall()
    form.fields['lesson'].choices = [(lesson[0], f'Дисципліна: {lesson[1]}, Дата: {lesson[2]}, Час початку: {lesson[3]}, Час кінця: {lesson[4]}') for lesson in lessons]
    if form.is_valid():
      fk_student_id = form.cleaned_data.get('student')
      grade = form.cleaned_data.get('grade')
      fk_eval_elt = form.cleaned_data.get('eval_elt')
      fk_lesson_id = form.cleaned_data.get('lesson')
      cursor.execute("""
                     UPDATE [Student grades]
                     SET fk_student_id = %s, grade = %s, fk_eval_elt = %s, fk_lesson_id = %s
                     WHERE grade_id = %s
                     """, (fk_student_id, grade, fk_eval_elt, fk_lesson_id, grade_id))
      if cursor.rowcount > 0:
        response = redirect('show-teacher-student-stats-page', class_id=class_id)
        return response
  else:
    form = StudentGradeForm()
    cursor.execute("""
                   SELECT student_id, last_name, first_name, patronymic
                   FROM Students INNER JOIN [Students in class] 
                                       ON Students.student_id = [Students in class].fk_student_id INNER JOIN Classes 
                                       ON [Students in class].fk_class_id = Classes.class_id
                   WHERE Classes.class_id = %s
                   """, (class_id,))
    students = cursor.fetchall()
    form.fields['student'].choices = [(student[0], f'{student[1]} {student[2]} {student[3]}') for student in students]
    cursor.execute("""
                   SELECT element_id, [name]
                   FROM [Evaluated elements]
                   """)
    eval_elts = cursor.fetchall()
    form.fields['eval_elt'].choices = [(eval_elt[0], eval_elt[1]) for eval_elt in eval_elts]
    cursor.execute("""
                   SELECT Lessons.lesson_id, Disciplines.[name], Lessons.[date], Lessons.start_time, Lessons.end_time
                   FROM Disciplines INNER JOIN Lessons ON discipline_id = fk_discipline_id INNER JOIN Classes
                                   ON fk_class_id = class_id INNER JOIN [Lesson statuses] ON fk_status_id = status_id
                   WHERE Classes.fk_teacher_id = %s AND fk_status_id = 2 AND Classes.class_id = %s AND Lessons.[date] >= %s AND Lessons.[date] <= %s
                   """, (request.session['worker_id'], class_id, request.session['from_date'], request.session['to_date']))
    lessons = cursor.fetchall()
    form.fields['lesson'].choices = [(lesson[0], f'Дисципліна: {lesson[1]}, Дата: {lesson[2]}, Час початку: {lesson[3]}, Час кінця: {lesson[4]}') for lesson in lessons]
    system_messages = messages.get_messages(request)
    for message in system_messages:
      pass
  return render(request, 'FormPage.html', {'w_last_name': request.session['last_name'],
                                              'w_first_name': request.session['first_name'], 
                                              'w_role': request.session['role'],
                                              'w_photo': request.session['photo'],
                                           'form': form})


def addStudentAttendance(request, class_id):
  cursor = connection.cursor()
  if request.method=='POST':
    form = StudentAttendanceForm(request.POST)
    cursor.execute("""
                   SELECT student_id, last_name, first_name, patronymic
                   FROM Students INNER JOIN [Students in class] 
                                       ON Students.student_id = [Students in class].fk_student_id INNER JOIN Classes 
                                       ON [Students in class].fk_class_id = Classes.class_id
                   WHERE Classes.class_id = %s
                   """, (class_id,))
    students = cursor.fetchall()
    form.fields['student'].choices = [(student[0], f'{student[1]} {student[2]} {student[3]}') for student in students]
    cursor.execute("""
                   SELECT Lessons.lesson_id, Disciplines.[name], Lessons.[date], Lessons.start_time, Lessons.end_time
                   FROM Disciplines INNER JOIN Lessons ON discipline_id = fk_discipline_id INNER JOIN Classes
                                   ON fk_class_id = class_id INNER JOIN [Lesson statuses] ON fk_status_id = status_id
                   WHERE Classes.fk_teacher_id = %s AND fk_status_id = 2 AND Classes.class_id = %s AND Lessons.[date] >= %s AND Lessons.[date] <= %s
                   """, (request.session['worker_id'], class_id, request.session['from_date'], request.session['to_date']))
    lessons = cursor.fetchall()
    form.fields['lesson'].choices = [(lesson[0], f'Дисципліна: {lesson[1]}, Дата: {lesson[2]}, Час початку: {lesson[3]}, Час кінця: {lesson[4]}') for lesson in lessons]
    if form.is_valid():
      fk_student_id = form.cleaned_data.get('student')
      fk_lesson_id = form.cleaned_data.get('lesson')
      presence = form.cleaned_data.get('attendance')
      cursor.execute("""
                     INSERT INTO [Student attendances](fk_student_id, fk_lesson_id, presence) VALUES
                     (%s, %s, %s)
                     """, (fk_student_id, fk_lesson_id, presence))
      if cursor.rowcount > 0:
        response = redirect('show-teacher-student-stats-page', class_id=class_id)
        return response
  else:
    form = StudentAttendanceForm()
    cursor.execute("""
                   SELECT student_id, last_name, first_name, patronymic
                   FROM Students INNER JOIN [Students in class] 
                                       ON Students.student_id = [Students in class].fk_student_id INNER JOIN Classes 
                                       ON [Students in class].fk_class_id = Classes.class_id
                   WHERE Classes.class_id = %s
                   """, (class_id,))
    students = cursor.fetchall()
    form.fields['student'].choices = [(student[0], f'{student[1]} {student[2]} {student[3]}') for student in students]
    cursor.execute("""
                   SELECT Lessons.lesson_id, Disciplines.[name], Lessons.[date], Lessons.start_time, Lessons.end_time
                   FROM Disciplines INNER JOIN Lessons ON discipline_id = fk_discipline_id INNER JOIN Classes
                                   ON fk_class_id = class_id INNER JOIN [Lesson statuses] ON fk_status_id = status_id
                   WHERE Classes.fk_teacher_id = %s AND fk_status_id = 2 AND Classes.class_id = %s AND Lessons.[date] >= %s AND Lessons.[date] <= %s
                   """, (request.session['worker_id'], class_id, request.session['from_date'], request.session['to_date']))
    lessons = cursor.fetchall()
    form.fields['lesson'].choices = [(lesson[0], f'Дисципліна: {lesson[1]}, Дата: {lesson[2]}, Час початку: {lesson[3]}, Час кінця: {lesson[4]}') for lesson in lessons]
    system_messages = messages.get_messages(request)
    for message in system_messages:
      pass
  return render(request, 'FormPage.html', {'w_last_name': request.session['last_name'],
                                              'w_first_name': request.session['first_name'], 
                                              'w_role': request.session['role'],
                                              'w_photo': request.session['photo'],
                                           'form': form})

def editStudentAttendance(request, class_id, attend_id):
  cursor = connection.cursor()
  if request.method=='POST':
    form = StudentAttendanceForm(request.POST)
    cursor.execute("""
                   SELECT student_id, last_name, first_name, patronymic
                   FROM Students INNER JOIN [Students in class] 
                                       ON Students.student_id = [Students in class].fk_student_id INNER JOIN Classes 
                                       ON [Students in class].fk_class_id = Classes.class_id
                   WHERE Classes.class_id = %s
                   """, (class_id,))
    students = cursor.fetchall()
    form.fields['student'].choices = [(student[0], f'{student[1]} {student[2]} {student[3]}') for student in students]
    cursor.execute("""
                   SELECT Lessons.lesson_id, Disciplines.[name], Lessons.[date], Lessons.start_time, Lessons.end_time
                   FROM Disciplines INNER JOIN Lessons ON discipline_id = fk_discipline_id INNER JOIN Classes
                                   ON fk_class_id = class_id INNER JOIN [Lesson statuses] ON fk_status_id = status_id
                   WHERE Classes.fk_teacher_id = %s AND fk_status_id = 2 AND Classes.class_id = %s AND Lessons.[date] >= %s AND Lessons.[date] <= %s
                   """, (request.session['worker_id'], class_id, request.session['from_date'], request.session['to_date']))
    lessons = cursor.fetchall()
    form.fields['lesson'].choices = [(lesson[0], f'Дисципліна: {lesson[1]}, Дата: {lesson[2]}, Час початку: {lesson[3]}, Час кінця: {lesson[4]}') for lesson in lessons]
    if form.is_valid():
      fk_student_id = form.cleaned_data.get('student')
      fk_lesson_id = form.cleaned_data.get('lesson')
      presence = form.cleaned_data.get('attendance')
      cursor.execute("""
                     UPDATE [Student attendances]
                     SET fk_student_id = %s, fk_lesson_id = %s, presence = %s
                     WHERE attend_id = %s
                     """, (fk_student_id, fk_lesson_id, presence, attend_id))
      if cursor.rowcount > 0:
        response = redirect('show-teacher-student-stats-page', class_id=class_id)
        return response
  else:
    form = StudentAttendanceForm()
    cursor.execute("""
                   SELECT student_id, last_name, first_name, patronymic
                   FROM Students INNER JOIN [Students in class] 
                                       ON Students.student_id = [Students in class].fk_student_id INNER JOIN Classes 
                                       ON [Students in class].fk_class_id = Classes.class_id
                   WHERE Classes.class_id = %s
                   """, (class_id,))
    students = cursor.fetchall()
    form.fields['student'].choices = [(student[0], f'{student[1]} {student[2]} {student[3]}') for student in students]
    cursor.execute("""
                   SELECT Lessons.lesson_id, Disciplines.[name], Lessons.[date], Lessons.start_time, Lessons.end_time
                   FROM Disciplines INNER JOIN Lessons ON discipline_id = fk_discipline_id INNER JOIN Classes
                                   ON fk_class_id = class_id INNER JOIN [Lesson statuses] ON fk_status_id = status_id
                   WHERE Classes.fk_teacher_id = %s AND fk_status_id = 2 AND Classes.class_id = %s AND Lessons.[date] >= %s AND Lessons.[date] <= %s
                   """, (request.session['worker_id'], class_id, request.session['from_date'], request.session['to_date']))
    lessons = cursor.fetchall()
    form.fields['lesson'].choices = [(lesson[0], f'Дисципліна: {lesson[1]}, Дата: {lesson[2]}, Час початку: {lesson[3]}, Час кінця: {lesson[4]}') for lesson in lessons]
    system_messages = messages.get_messages(request)
    for message in system_messages:
      pass
  return render(request, 'FormPage.html', {'w_last_name': request.session['last_name'],
                                              'w_first_name': request.session['first_name'], 
                                              'w_role': request.session['role'],
                                              'w_photo': request.session['photo'],
                                           'form': form})

def showDatesFormStudent(request, class_id):
  if 'from_date' in request.session and 'to_date' in request.session:
    del request.session['from_date']
    del request.session['to_date']
  if request.method=='POST':
    form = DatesForm(request.POST)
    if form.is_valid():
      from_date = form.cleaned_data.get('from_date')
      to_date = form.cleaned_data.get('to_date')
      request.session['from_date'] = from_date.strftime('%Y-%m-%d')
      request.session['to_date'] = to_date.strftime('%Y-%m-%d')
      if request.GET.get('redirect_to') is not None:
        if request.GET.get('redirect_to') == 'stats':
          response = redirect(reverse('show-teacher-student-stats-page', kwargs={'class_id':class_id}))
          return response
        elif request.GET.get('redirect_to') == 'comp':
          response = redirect(reverse('show-teacher-student-comp-page', kwargs={'class_id':class_id}))
          return response
  else:
    form = DatesForm()
    system_messages = messages.get_messages(request)
    for message in system_messages:
      pass
  return render(request, 'DatesForm.html', {'w_last_name': request.session['last_name'],
                                            'w_first_name': request.session['first_name'], 
                                            'w_role': request.session['role'],
                                            'w_photo': request.session['photo'],
                                            'form': form})

def showDatesFormLessons(request):
  if 'from_date' in request.session and 'to_date' in request.session:
    del request.session['from_date']
    del request.session['to_date']

  if request.method=='POST':
    form = DatesForm(request.POST)
    if form.is_valid():
      from_date = form.cleaned_data.get('from_date')
      to_date = form.cleaned_data.get('to_date')
      request.session['from_date'] = from_date.strftime('%Y-%m-%d')
      request.session['to_date'] = to_date.strftime('%Y-%m-%d')
      response = redirect('show-teacher-lesson-page')
      return response
  else:
    form = DatesForm()
    system_messages = messages.get_messages(request)
    for message in system_messages:
      pass
  return render(request, 'DatesForm.html', {'w_last_name': request.session['last_name'],
                                            'w_first_name': request.session['first_name'], 
                                            'w_role': request.session['role'],
                                            'w_photo': request.session['photo'],
                                            'form': form})

def addTeacherLessonDone(request):
  cursor = connection.cursor()
  if request.method=='POST':
    form = TeacherLessonDone(request.POST)
    cursor.execute("""
                   SELECT discipline_id, [name]
                   FROM Disciplines
                   """)
    disciplines = cursor.fetchall()
    form.fields['discipline'].choices = [(discipline[0], f'{discipline[1]}') for discipline in disciplines]
    cursor.execute("""
                   EXEC selectTeacherClasses @teacher_id=%s
                   """, (request.session['worker_id'],))
    classes_students = cursor.fetchall()
    form.fields['class_students'].choices = [(class_students[0], f'Назва: {class_students[1]}, Спеціалізація: {class_students[2]}') for class_students in classes_students]
    if form.is_valid():
      fk_discipline_id = form.cleaned_data.get('discipline')
      fk_class_id = form.cleaned_data.get('class_students')
      fk_teacher_id = request.session['worker_id']
      date = form.cleaned_data.get('date').strftime('%Y-%m-%d')
      start_time = form.cleaned_data.get('start_time').strftime('%H:%M')
      end_time = form.cleaned_data.get('end_time').strftime('%H:%M')
      fk_status_id = 2
      cursor.execute("""
                     INSERT INTO [Lessons](fk_discipline_id, fk_class_id, fk_teacher_id, date, start_time, end_time, fk_status_id) VALUES
                     (%s, %s, %s, %s, %s, %s, %s)
                     """, (fk_discipline_id, fk_class_id, fk_teacher_id, date, start_time, end_time, fk_status_id))
      if cursor.rowcount > 0:
        response = redirect('show-teacher-lesson-page')
        return response
  else:
    form = TeacherLessonDone()
    cursor.execute("""
                   SELECT discipline_id, [name]
                   FROM Disciplines
                   """)
    disciplines = cursor.fetchall()
    form.fields['discipline'].choices = [(discipline[0], f'{discipline[1]}') for discipline in disciplines]
    cursor.execute("""
                   EXEC selectTeacherClasses @teacher_id=%s
                   """, (request.session['worker_id'],))
    classes_students = cursor.fetchall()
    form.fields['class_students'].choices = [(class_students[0], f'Назва: {class_students[1]}, Спеціалізація: {class_students[2]}') for class_students in classes_students]
    system_messages = messages.get_messages(request)
    for message in system_messages:
      pass
  return render(request, 'FormPage.html', {'w_last_name': request.session['last_name'],
                                            'w_first_name': request.session['first_name'], 
                                            'w_role': request.session['role'],
                                            'w_photo': request.session['photo'],
                                            'form': form})

def editTeacherLessonDone(request, lesson_id):
  cursor = connection.cursor()
  if request.method=='POST':
    form = TeacherLessonDone(request.POST)
    cursor.execute("""
                   SELECT discipline_id, [name]
                   FROM Disciplines
                   """)
    disciplines = cursor.fetchall()
    form.fields['discipline'].choices = [(discipline[0], f'{discipline[1]}') for discipline in disciplines]
    cursor.execute("""
                   EXEC selectTeacherClasses @teacher_id=%s
                   """, (request.session['worker_id'],))
    classes_students = cursor.fetchall()
    form.fields['class_students'].choices = [(class_students[0], f'Назва: {class_students[1]}, Спеціалізація: {class_students[2]}') for class_students in classes_students]
    if form.is_valid():
      fk_discipline_id = form.cleaned_data.get('discipline')
      fk_class_id = form.cleaned_data.get('class_students')
      date = form.cleaned_data.get('date').strftime('%Y-%m-%d')
      start_time = form.cleaned_data.get('start_time').strftime('%H:%M')
      end_time = form.cleaned_data.get('end_time').strftime('%H:%M')
      cursor.execute("""
                     UPDATE [Lessons]
                     SET fk_discipline_id = %s, fk_class_id = %s, [date] = %s, start_time = %s, end_time = %s
                     WHERE lesson_id = %s
                     """, (fk_discipline_id, fk_class_id, date, start_time, end_time, lesson_id))
      if cursor.rowcount > 0:
        response = redirect('show-teacher-lesson-page')
        return response
  else:
    cursor.execute("""
                   SELECT [date], start_time, end_time
                   FROM Lessons
                   WHERE lesson_id = %s
                   """, (lesson_id,))
    time_data = cursor.fetchone()
    form = TeacherLessonDone(initial={
      'date': time_data[0],
      'start_time': time_data[1].strftime('%H:%M'),
      'end_time': time_data[2].strftime('%H:%M')
    })
    cursor.execute("""
                   SELECT discipline_id, [name]
                   FROM Disciplines
                   """)
    disciplines = cursor.fetchall()
    form.fields['discipline'].choices = [(discipline[0], f'{discipline[1]}') for discipline in disciplines]
    cursor.execute("""
                   EXEC selectTeacherClasses @teacher_id=%s
                   """, (request.session['worker_id'],))
    classes_students = cursor.fetchall()
    form.fields['class_students'].choices = [(class_students[0], f'Назва: {class_students[1]}, Спеціалізація: {class_students[2]}') for class_students in classes_students]
    system_messages = messages.get_messages(request)
    for message in system_messages:
      pass
  return render(request, 'FormPage.html', {'w_last_name': request.session['last_name'],
                                            'w_first_name': request.session['first_name'], 
                                            'w_role': request.session['role'],
                                            'w_photo': request.session['photo'],
                                            'form': form})

def addStudentComp(request, class_id):
  cursor = connection.cursor()
  if request.method=='POST':
    form = StudentCompForm(request.POST)
    cursor.execute("""
                   SELECT skill_id, [Discipline skills].[name], Disciplines.[name]
                   FROM [Discipline skills] INNER JOIN Disciplines ON fk_discipline_id = discipline_id
                   WHERE Disciplines.discipline_id IN (SELECT fk_discipline_id
                                                       FROM [Teacher disciplines]
                                                       WHERE fk_teacher_id = %s)
                   """, (request.session['worker_id'],))
    skills = cursor.fetchall()
    form.fields['skill'].choices = [(skill[0], f'Назва: {skill[1]}, Дисципліна: {skill[2]}') for skill in skills]
    cursor.execute("""
                   SELECT student_id, last_name, first_name, patronymic
                   FROM Students INNER JOIN [Students in class] ON student_id = fk_student_id
                   WHERE fk_class_id = %s
                   """, (class_id,))
    students = cursor.fetchall()
    form.fields['student'].choices = [(student[0], f'{student[1]} {student[2]} {student[3]}') for student in students]
    cursor.execute("""
                   SELECT *
                   FROM [Competence levels]
                   """)
    levels = cursor.fetchall()
    form.fields['level'].choices = [(level[0], f'{level[1]}') for level in levels]
    if form.is_valid():
      fk_skill_id = form.cleaned_data.get('skill')
      date = form.cleaned_data.get('date')
      time = form.cleaned_data.get('time')
      date_time = datetime.combine(date, time)
      fk_teacher_id = request.session['worker_id']
      fk_student_id = form.cleaned_data.get('student')
      fk_level_id = form.cleaned_data.get('level')
      cursor.execute("""
                         INSERT INTO [Student competencies](fk_skill_id, date_time, fk_teacher_id, fk_student_id, fk_level_id) VALUES
                         (%s, %s, %s, %s, %s)
                         """, (fk_skill_id, date_time, fk_teacher_id, fk_student_id, fk_level_id))
      if cursor.rowcount > 0:
        response = redirect('show-teacher-student-comp-page', class_id=class_id)
        return response
  else:
    form = StudentCompForm()
    cursor.execute("""
                   SELECT skill_id, [Discipline skills].[name], Disciplines.[name]
                   FROM [Discipline skills] INNER JOIN Disciplines ON fk_discipline_id = discipline_id
                   WHERE Disciplines.discipline_id IN (SELECT fk_discipline_id
                                                       FROM [Teacher disciplines]
                                                       WHERE fk_teacher_id = %s)
                   """, (request.session['worker_id'],))
    skills = cursor.fetchall()
    form.fields['skill'].choices = [(skill[0], f'Назва: {skill[1]}, Дисципліна: {skill[2]}') for skill in skills]
    cursor.execute("""
                   SELECT student_id, last_name, first_name, patronymic
                   FROM Students INNER JOIN [Students in class] ON student_id = fk_student_id
                   WHERE fk_class_id = %s
                   """, (class_id,))
    students = cursor.fetchall()
    form.fields['student'].choices = [(student[0], f'{student[1]} {student[2]} {student[3]}') for student in students]
    cursor.execute("""
                   SELECT *
                   FROM [Competence levels]
                   """)
    levels = cursor.fetchall()
    form.fields['level'].choices = [(level[0], f'{level[1]}') for level in levels]
    system_messages = messages.get_messages(request)
    for message in system_messages:
      pass
  return render(request, 'FormPage.html', {'w_last_name': request.session['last_name'],
                                            'w_first_name': request.session['first_name'], 
                                            'w_role': request.session['role'],
                                            'w_photo': request.session['photo'],
                                            'form': form})

def editStudentComp(request, class_id, comp_id):
  cursor = connection.cursor()
  if request.method=='POST':
    form = StudentCompForm(request.POST)
    cursor.execute("""
                   SELECT skill_id, [Discipline skills].[name], Disciplines.[name]
                   FROM [Discipline skills] INNER JOIN Disciplines ON fk_discipline_id = discipline_id
                   WHERE Disciplines.discipline_id IN (SELECT fk_discipline_id
                                                       FROM [Teacher disciplines]
                                                       WHERE fk_teacher_id = %s)
                   """, (request.session['worker_id'],))
    skills = cursor.fetchall()
    form.fields['skill'].choices = [(skill[0], f'Назва: {skill[1]}, Дисципліна: {skill[2]}') for skill in skills]
    cursor.execute("""
                   SELECT student_id, last_name, first_name, patronymic
                   FROM Students INNER JOIN [Students in class] ON student_id = fk_student_id
                   WHERE fk_class_id = %s
                   """, (class_id,))
    students = cursor.fetchall()
    form.fields['student'].choices = [(student[0], f'{student[1]} {student[2]} {student[3]}') for student in students]
    cursor.execute("""
                   SELECT *
                   FROM [Competence levels]
                   """)
    levels = cursor.fetchall()
    form.fields['level'].choices = [(level[0], f'{level[1]}') for level in levels]
    if form.is_valid():
      fk_skill_id = form.cleaned_data.get('skill')
      date = form.cleaned_data.get('date')
      time = form.cleaned_data.get('time')
      date_time = datetime.combine(date, time)
      fk_teacher_id = request.session['worker_id']
      fk_student_id = form.cleaned_data.get('student')
      fk_level_id = form.cleaned_data.get('level')
      cursor.execute("""
                     UPDATE [Student competencies]
                     SET fk_skill_id = %s, date_time = %s, fk_teacher_id = %s, fk_student_id = %s, fk_level_id = %s
                     WHERE stud_comp_id = %s
                     """, (fk_skill_id, date_time, fk_teacher_id, fk_student_id, fk_level_id, comp_id))
      if cursor.rowcount > 0:
        response = redirect('show-teacher-student-comp-page', class_id=class_id)
        return response
  else:
    cursor.execute("""
                   SELECT date_time
                   FROM [Student competencies]
                   WHERE stud_comp_id = %s
                   """, (comp_id,))
    dtime = cursor.fetchone()
    get_data = dtime[0].date()
    get_time = dtime[0].time()
    print(get_time)
    form = StudentCompForm(initial={
      'date': get_data.strftime('%Y-%m-%d'),
      'time': get_time.strftime('%H:%M'),
    })
    cursor.execute("""
                   SELECT skill_id, [Discipline skills].[name], Disciplines.[name]
                   FROM [Discipline skills] INNER JOIN Disciplines ON fk_discipline_id = discipline_id
                   WHERE Disciplines.discipline_id IN (SELECT fk_discipline_id
                                                       FROM [Teacher disciplines]
                                                       WHERE fk_teacher_id = %s)
                   """, (request.session['worker_id'],))
    skills = cursor.fetchall()
    form.fields['skill'].choices = [(skill[0], f'Назва: {skill[1]}, Дисципліна: {skill[2]}') for skill in skills]
    cursor.execute("""
                   SELECT student_id, last_name, first_name, patronymic
                   FROM Students INNER JOIN [Students in class] ON student_id = fk_student_id
                   WHERE fk_class_id = %s
                   """, (class_id,))
    students = cursor.fetchall()
    form.fields['student'].choices = [(student[0], f'{student[1]} {student[2]} {student[3]}') for student in students]
    cursor.execute("""
                   SELECT *
                   FROM [Competence levels]
                   """)
    levels = cursor.fetchall()
    form.fields['level'].choices = [(level[0], f'{level[1]}') for level in levels]
    system_messages = messages.get_messages(request)
    for message in system_messages:
      pass
  return render(request, 'FormPage.html', {'w_last_name': request.session['last_name'],
                                            'w_first_name': request.session['first_name'], 
                                            'w_role': request.session['role'],
                                            'w_photo': request.session['photo'],
                                            'form': form})

def showCoordPage(request):
  if not request.COOKIES.get('logged_in') or request.session['role'] != 'Координатор':
     raise Http404
  return render(request, 'CoordPage.html', {'w_last_name': request.session['last_name'],
                                            'w_first_name': request.session['first_name'], 
                                            'w_role': request.session['role'],
                                            'w_photo': request.session['photo']})                                            

def showTeachersListPage(request):
  cursor = connection.cursor()
  cursor.execute("""
                 SELECT last_name, first_name, patronymic, worker_id
                 FROM Workers
                 WHERE fk_role_id = 2
                 """)
  teachers = cursor.fetchall()
  teacher_disciplines_dict = {}
  for teacher in teachers:
   cursor.execute("""
                  SELECT Disciplines.[name]
                  FROM [Teacher disciplines] INNER JOIN Disciplines ON fk_discipline_id = discipline_id
                  WHERE fk_teacher_id = %s
                  """, (teacher[-1],))
   disciplines = cursor.fetchall()
   teacher_disciplines_dict[teacher] = disciplines
  return render(request, 'TeachersList.html', {'w_last_name': request.session['last_name'],
                                               'w_first_name': request.session['first_name'], 
                                               'w_role': request.session['role'],
                                               'w_photo': request.session['photo'],
                                               'teachers': teachers,
                                               'disciplines_dict': teacher_disciplines_dict})

def showClassesPage(request):
  cursor = connection.cursor()
  cursor.execute("""
                 SELECT Classes.[name], Specialisations.[name], Classes.class_id
                 FROM Specialisations INNER JOIN Classes ON Specialisations.spec_id = Classes.fk_spec_id
                 """)
  classes = cursor.fetchall()
  return render(request, 'ClassesList.html', {'w_last_name': request.session['last_name'],
                                               'w_first_name': request.session['first_name'], 
                                               'w_role': request.session['role'],
                                               'w_photo': request.session['photo'],
                                               'classes': classes})

def addTeacher(request):
  cursor = connection.cursor()
  if request.method=='POST':
    form = CreateTeacherForm(request.POST, request.FILES)
    cursor.execute("""
                   SELECT class_id, [name]
                   FROM Classes
                   WHERE fk_teacher_id IS NULL
                   """)
    classes = cursor.fetchall()
    form.fields['personal_class'].choices = [(100, 'Без класу')] + [(personal_class[0], f'{personal_class[1]}') for personal_class in classes]
    cursor.execute("""
                   SELECT *
                   FROM Disciplines
                   """)
    disciplines = cursor.fetchall()
    form.fields['discipline'].choices = [(discipline[0], f'{discipline[1]}') for discipline in disciplines]
    if form.is_valid():
      last_name = form.cleaned_data.get('last_name')
      first_name = form.cleaned_data.get('first_name')
      patronymic = form.cleaned_data.get('patronymic')
      fk_role_id = 2

      login = form.cleaned_data.get('login')
      password = form.cleaned_data.get('password')

      fk_class_id = int(form.cleaned_data.get('personal_class'))

      discipline = form.cleaned_data.get('discipline')
      if fk_class_id > 0:
        photo = request.FILES['photo']
        filepath = Rename.rename('teacher', photo.name)
        photo_path = filepath
        cursor.execute("""
                       INSERT INTO [Workers](last_name, first_name, patronymic, fk_role_id, photo_path) VALUES
                       (%s, %s, %s, %s, %s)
                       """, (last_name, first_name, patronymic, fk_role_id, photo_path))
        if cursor.rowcount > 0:
          default_storage.save(filepath, photo)
          cursor.execute("""
                         SELECT worker_id
                         FROM Workers
                         WHERE last_name = %s AND first_name = %s AND patronymic = %s AND fk_role_id = %s AND photo_path = %s
                         """, (last_name, first_name, patronymic, fk_role_id, photo_path))
          teacher_id = cursor.fetchone()
          teacher_id = teacher_id[0]
          cursor.execute("""
                         INSERT INTO [Worker entry data](fk_worker_id, login, password) VALUES
                         (%s, %s, %s)
                         """, (teacher_id, login, password))
          if cursor.rowcount > 0:
            cursor.execute("""
                            INSERT INTO [Teacher disciplines](fk_teacher_id, fk_discipline_id) VALUES
                            (%s, %s)
                            """, (teacher_id, discipline))
            if cursor.rowcount > 0:
              if fk_class_id != 100:
                cursor.execute("""
                              UPDATE [Classes]
                              SET fk_teacher_id = %s
                              WHERE class_id = %s
                              """, (teacher_id, fk_class_id))
                if cursor.rowcount > 0:
                  response = redirect('show-coord-page')
                  return response
              else:
                response = redirect('show-teachers-list')
                return response
  else:
    form = CreateTeacherForm()
    cursor.execute("""
                   SELECT class_id, [name]
                   FROM Classes
                   WHERE fk_teacher_id IS NULL
                   """)
    classes = cursor.fetchall()
    form.fields['personal_class'].choices = [(100, 'Без класу')] + [(personal_class[0], f'{personal_class[1]}') for personal_class in classes]
    cursor.execute("""
                   SELECT *
                   FROM Disciplines
                   """)
    disciplines = cursor.fetchall()
    form.fields['discipline'].choices = [(discipline[0], f'{discipline[1]}') for discipline in disciplines]
    system_messages = messages.get_messages(request)
    for message in system_messages:
      pass
  return render(request, 'PersonFormPage.html', {'w_last_name': request.session['last_name'],
                                            'w_first_name': request.session['first_name'], 
                                            'w_role': request.session['role'],
                                            'w_photo': request.session['photo'],
                                            'form': form})

def addStudent(request):
  cursor = connection.cursor()
  if request.method=='POST':
    form = CreateStudentForm(request.POST, request.FILES)
    if form.is_valid():
      last_name = form.cleaned_data.get('last_name')
      first_name = form.cleaned_data.get('first_name')
      patronymic = form.cleaned_data.get('patronymic')
      date_of_birth = form.cleaned_data.get('date_of_birth').strftime('%Y-%m-%d')
      photo = request.FILES['photo']
      filepath = Rename.rename('student', photo.name)
      photo_path = filepath
      cursor.execute("""
                     INSERT INTO [Students](last_name, first_name, patronymic, date_of_birth, photo_path) VALUES
                     (%s, %s, %s, %s, %s)
                     """, (last_name, first_name, patronymic, date_of_birth, photo_path))
      if cursor.rowcount > 0:
        default_storage.save(filepath, photo)
        response = redirect('show-coord-page')
        return response
  else:
    form = CreateStudentForm()
    system_messages = messages.get_messages(request)
    for message in system_messages:
      pass
  return render(request, 'PersonFormPage.html', {'w_last_name': request.session['last_name'],
                                            'w_first_name': request.session['first_name'], 
                                            'w_role': request.session['role'],
                                            'w_photo': request.session['photo'],
                                            'form': form})

def addStudentToClass(request, class_id):
  cursor = connection.cursor()
  cursor.execute("""
                 SELECT student_id, last_name, first_name, patronymic
                 FROM Students s
                 WHERE NOT EXISTS (SELECT 1
                                   FROM [Students in class] sc
                                   WHERE sc.fk_student_id = s.student_id
                )
                """)
  new_students = cursor.fetchall()
  if request.method=='POST':
    form = AddStudentToClassForm(request.POST)
    form.fields['student'].choices = [(student[0], f'{student[1]} {student[2]} {student[3]}') for student in new_students]
    if form.is_valid():
      fk_student_id = form.cleaned_data.get('student')
      fk_class_id = class_id
      cursor.execute("""
                     INSERT INTO [Students in class](fk_student_id, fk_class_id) VALUES
                     (%s, %s)
                     """, (fk_student_id, fk_class_id))
      if cursor.rowcount > 0:
        response = redirect(reverse('show-coord-class-page', kwargs={'class_id':class_id}))
        return response
  else:
    form = AddStudentToClassForm()
    form.fields['student'].choices = [(student[0], f'{student[1]} {student[2]} {student[3]}') for student in new_students]
    system_messages = messages.get_messages(request)
    for message in system_messages:
      pass
  return render(request, 'PersonFormPage.html', {'w_last_name': request.session['last_name'],
                                            'w_first_name': request.session['first_name'], 
                                            'w_role': request.session['role'],
                                            'w_photo': request.session['photo'],
                                            'form': form})

def showCoordTeacherPage(request, teacher_id):
  cursor = connection.cursor()
  cursor.execute("""
                 SELECT last_name, first_name, patronymic, photo_path
                 FROM Workers
                 WHERE worker_id = %s
                 """, (teacher_id,))
  teacher = cursor.fetchone()
  cursor.execute("""
                 SELECT Classes.[name], Specialisations.[name] 
                 FROM Classes INNER JOIN Specialisations
                      ON fk_spec_id = spec_id
                 WHERE fk_teacher_id = %s
                 """, (teacher_id,))
  teacher_classes = cursor.fetchall()
  return render(request, 'CoordTeacherPage.html', {'w_last_name': request.session['last_name'],
                                                  'w_first_name': request.session['first_name'], 
                                                  'w_role': request.session['role'],
                                                  'w_photo': request.session['photo'],
                                                  'teacher_data': teacher,
                                                  'teacher_classes_data': teacher_classes})

def showDatesFormCoord(request):
  if 'from_date' in request.session and 'to_date' in request.session:
    del request.session['from_date']
    del request.session['to_date']
  if request.method=='POST':
    form = DatesForm(request.POST)
    if form.is_valid():
      from_date = form.cleaned_data.get('from_date')
      to_date = form.cleaned_data.get('to_date')
      request.session['from_date'] = from_date.strftime('%Y-%m-%d')
      request.session['to_date'] = to_date.strftime('%Y-%m-%d')
      response = redirect('show-coord-lessons')
      return response
  else:
    form = DatesForm()
    system_messages = messages.get_messages(request)
    for message in system_messages:
      pass
  return render(request, 'DatesForm.html', {'w_last_name': request.session['last_name'],
                                            'w_first_name': request.session['first_name'], 
                                            'w_role': request.session['role'],
                                            'w_photo': request.session['photo'],
                                            'form': form})

def showCoordLessons(request):
  cursor = connection.cursor()
  cursor.execute("""
                 SELECT Lessons.lesson_id, Disciplines.[name], Classes.[name], Workers.last_name, Workers.first_name,
                 Lessons.[date], Lessons.start_time, Lessons.end_time
                 FROM Disciplines INNER JOIN Lessons ON discipline_id = fk_discipline_id INNER JOIN Classes
                 ON fk_class_id = class_id INNER JOIN [Lesson statuses] ON fk_status_id = status_id INNER JOIN Workers
                 ON Lessons.fk_teacher_id = Workers.worker_id
                 WHERE fk_status_id = 1 AND Lessons.[date] >= %s AND Lessons.[date] <= %s
                 """, (request.session['from_date'], request.session['to_date']))
  planned_lessons = cursor.fetchall()
  cursor.execute("""
                 SELECT Lessons.lesson_id, Disciplines.[name], Classes.[name], Workers.last_name, Workers.first_name,
                 Lessons.[date], Lessons.start_time, Lessons.end_time
                 FROM Disciplines INNER JOIN Lessons ON discipline_id = fk_discipline_id INNER JOIN Classes
                 ON fk_class_id = class_id INNER JOIN [Lesson statuses] ON fk_status_id = status_id INNER JOIN Workers
                 ON Lessons.fk_teacher_id = Workers.worker_id
                 WHERE fk_status_id = 2 AND Lessons.[date] >= %s AND Lessons.[date] <= %s
                 """, (request.session['from_date'], request.session['to_date']))
  done_lessons = cursor.fetchall()
  return render(request, 'CoordLessons.html', {'w_last_name': request.session['last_name'],
                                            'w_first_name': request.session['first_name'], 
                                            'w_role': request.session['role'],
                                            'w_photo': request.session['photo'],
                                            'planned_lessons': planned_lessons,
                                            'done_lessons': done_lessons})

def addPlannedLesson(request):
  cursor = connection.cursor()
  if request.method=='POST':
    form = PlannedLessonForm(request.POST)
    cursor.execute("""
                  SELECT discipline_id, [name]
                  FROM DISCIPLINES
                  """)
    disciplines = cursor.fetchall()
    form.fields['discipline'].choices = [(discipline[0], f'{discipline[1]}') for discipline in disciplines]
    cursor.execute("""
                  SELECT class_id, Classes.[name], Specialisations.[name]
                  FROM Classes INNER JOIN Specialisations ON fk_spec_id = spec_id
                  """)
    classes = cursor.fetchall()
    form.fields['student_class'].choices = [(student_class[0], f'Назва: {student_class[1]}, Спеціалізація: {student_class[2]}') for student_class in classes]
    cursor.execute("""
                  SELECT worker_id, last_name, first_name, patronymic
                  FROM Workers INNER JOIN [Worker roles] ON fk_role_id = role_id
                  Where [Worker roles].[name] = N'Вчитель'
                  """)
    teachers = cursor.fetchall()
    form.fields['teacher'].choices = [(teacher[0], f'{teacher[1]} {teacher[2]} {teacher[3]}') for teacher in teachers]
    if form.is_valid():
      fk_discipline_id = form.cleaned_data.get('discipline')
      fk_class_id = form.cleaned_data.get('student_class')
      fk_teacher_id = form.cleaned_data.get('teacher')
      date = form.cleaned_data.get('date')
      date = date.strftime('%Y-%m-%d')
      start_time = form.cleaned_data.get('start_time')
      start_time = start_time.strftime('%H:%M')
      end_time = form.cleaned_data.get('end_time')
      end_time = end_time.strftime('%H:%M')
      fk_status_id = 1
      cursor.execute("""
                     INSERT INTO [Lessons](fk_discipline_id, fk_class_id, fk_teacher_id, date, start_time, end_time, fk_status_id) VALUES
                     (%s, %s, %s, %s, %s, %s, %s)
                     """, (fk_discipline_id, fk_class_id, fk_teacher_id, date, start_time, end_time, fk_status_id))
      if cursor.rowcount > 0:
        response = redirect('show-coord-lessons')
        return response
  else:
    form = PlannedLessonForm()
    cursor.execute("""
                  SELECT discipline_id, [name]
                  FROM DISCIPLINES
                  """)
    disciplines = cursor.fetchall()
    form.fields['discipline'].choices = [(discipline[0], f'{discipline[1]}') for discipline in disciplines]
    cursor.execute("""
                  SELECT class_id, Classes.[name], Specialisations.[name]
                  FROM Classes INNER JOIN Specialisations ON fk_spec_id = spec_id
                  """)
    classes = cursor.fetchall()
    form.fields['student_class'].choices = [(student_class[0], f'Назва: {student_class[1]}, Спеціалізація: {student_class[2]}') for student_class in classes]
    cursor.execute("""
                  SELECT worker_id, last_name, first_name, patronymic
                  FROM Workers INNER JOIN [Worker roles] ON fk_role_id = role_id
                  Where [Worker roles].[name] = N'Вчитель'
                  """)
    teachers = cursor.fetchall()
    form.fields['teacher'].choices = [(teacher[0], f'{teacher[1]} {teacher[2]} {teacher[3]}') for teacher in teachers]
    system_messages = messages.get_messages(request)
    for message in system_messages:
      pass
  return render(request, 'FormPage.html', {'w_last_name': request.session['last_name'],
                                            'w_first_name': request.session['first_name'], 
                                            'w_role': request.session['role'],
                                            'w_photo': request.session['photo'],
                                            'form': form})

def editPlannedLesson(request, lesson_id):
  cursor = connection.cursor()
  if request.method=='POST':
    form = PlannedLessonForm(request.POST)
    cursor.execute("""
                  SELECT discipline_id, [name]
                  FROM DISCIPLINES
                  """)
    disciplines = cursor.fetchall()
    form.fields['discipline'].choices = [(discipline[0], f'{discipline[1]}') for discipline in disciplines]
    cursor.execute("""
                  SELECT class_id, Classes.[name], Specialisations.[name]
                  FROM Classes INNER JOIN Specialisations ON fk_spec_id = spec_id
                  """)
    classes = cursor.fetchall()
    form.fields['student_class'].choices = [(student_class[0], f'Назва: {student_class[1]}, Спеціалізація: {student_class[2]}') for student_class in classes]
    cursor.execute("""
                  SELECT worker_id, last_name, first_name, patronymic
                  FROM Workers INNER JOIN [Worker roles] ON fk_role_id = role_id
                  Where [Worker roles].[name] = N'Вчитель'
                  """)
    teachers = cursor.fetchall()
    form.fields['teacher'].choices = [(teacher[0], f'{teacher[1]} {teacher[2]} {teacher[3]}') for teacher in teachers]
    if form.is_valid():
      fk_discipline_id = form.cleaned_data.get('discipline')
      fk_class_id = form.cleaned_data.get('student_class')
      fk_teacher_id = form.cleaned_data.get('teacher')
      date = form.cleaned_data.get('date')
      date = date.strftime('%Y-%m-%d')
      start_time = form.cleaned_data.get('start_time')
      start_time = start_time.strftime('%H:%M')
      end_time = form.cleaned_data.get('end_time')
      end_time = end_time.strftime('%H:%M')
      cursor.execute("""
                     UPDATE Lessons
                     SET fk_discipline_id = %s, fk_class_id = %s, fk_teacher_id = %s, [date] = %s, start_time = %s, end_time = %s
                     WHERE lesson_id = %s
                     """, (fk_discipline_id, fk_class_id, fk_teacher_id, date, start_time, end_time, lesson_id))
      if cursor.rowcount > 0:
        response = redirect('show-coord-lessons')
        return response
  else:
    cursor.execute("""
                   SELECT [date], start_time, end_time
                   FROM Lessons
                   WHERE lesson_id = %s
                   """, (lesson_id,))
    time_data = cursor.fetchone()
    form = PlannedLessonForm(initial={
      'date': time_data[0],
      'start_time': time_data[1].strftime('%H:%M'),
      'end_time': time_data[2].strftime('%H:%M')
    })
    cursor.execute("""
                  SELECT discipline_id, [name]
                  FROM Disciplines
                  """)
    disciplines = cursor.fetchall()
    form.fields['discipline'].choices = [(discipline[0], f'{discipline[1]}') for discipline in disciplines]
    cursor.execute("""
                  SELECT class_id, Classes.[name], Specialisations.[name]
                  FROM Classes INNER JOIN Specialisations ON fk_spec_id = spec_id
                  """)
    classes = cursor.fetchall()
    form.fields['student_class'].choices = [(student_class[0], f'Назва: {student_class[1]}, Спеціалізація: {student_class[2]}') for student_class in classes]
    cursor.execute("""
                  SELECT worker_id, last_name, first_name, patronymic
                  FROM Workers INNER JOIN [Worker roles] ON fk_role_id = role_id
                  Where [Worker roles].[name] = N'Вчитель'
                  """)
    teachers = cursor.fetchall()
    form.fields['teacher'].choices = [(teacher[0], f'{teacher[1]} {teacher[2]} {teacher[3]}') for teacher in teachers]
    system_messages = messages.get_messages(request)
    for message in system_messages:
      pass
  return render(request, 'FormPage.html', {'w_last_name': request.session['last_name'],
                                            'w_first_name': request.session['first_name'], 
                                            'w_role': request.session['role'],
                                            'w_photo': request.session['photo'],
                                            'form': form})

def addClass(request):
  cursor = connection.cursor()
  if request.method=='POST':
    form = CreateClassForm(request.POST)
    cursor.execute("""
                   SELECT worker_id, last_name, first_name, patronymic
                   FROM Workers INNER JOIN [Worker roles] ON fk_role_id = role_id
                   WHERE [Worker roles].[name] = N'Вчитель'
                   """)
    teachers = cursor.fetchall()
    form.fields['main_teacher'].choices = [(0, 'Без вчителя')] + [(teacher[0], f'{teacher[1]} {teacher[2]} {teacher[3]}') for teacher in teachers]
    cursor.execute("""
                   SELECT spec_id, [name]
                   FROM Specialisations
                   """)
    specs = cursor.fetchall()
    form.fields['spec'].choices = [(spec[0], f'{spec[1]}') for spec in specs]
    if form.is_valid():
      name = form.cleaned_data.get('name')
      main_teacher = int(form.cleaned_data.get('main_teacher'))
      specialisation = int(form.cleaned_data.get('spec'))
      if main_teacher == 0:
        cursor.execute("""
                       INSERT INTO Classes([name], fk_spec_id) VALUES
                       (%s, %s)
                       """, (name, specialisation))
        if cursor.rowcount > 0:
          response = redirect('show-coord-classes-page')
          return response
      else:
        cursor.execute("""
                       INSERT INTO Classes([name], fk_teacher_id, fk_spec_id) VALUES
                       (%s, %s, %s)
                       """, (name, main_teacher, specialisation))
        if cursor.rowcount > 0:
          response = redirect('show-coord-classes-page')
          return response
  else:
    form = CreateClassForm()
    cursor.execute("""
                   SELECT worker_id, last_name, first_name, patronymic
                   FROM Workers INNER JOIN [Worker roles] ON fk_role_id = role_id
                   WHERE [Worker roles].[name] = N'Вчитель'
                   """)
    teachers = cursor.fetchall()
    form.fields['main_teacher'].choices = [(0, 'Без вчителя')] + [(teacher[0], f'{teacher[1]} {teacher[2]} {teacher[3]}') for teacher in teachers]
    cursor.execute("""
                   SELECT spec_id, [name]
                   FROM Specialisations
                   """)
    specs = cursor.fetchall()
    form.fields['spec'].choices = [(spec[0], f'{spec[1]}') for spec in specs]
    system_messages = messages.get_messages(request)
    for message in system_messages:
      pass
  return render(request, 'FormPage.html', {'w_last_name': request.session['last_name'],
                                            'w_first_name': request.session['first_name'], 
                                            'w_role': request.session['role'],
                                            'w_photo': request.session['photo'],
                                            'form': form})

def addTeacherToClass(request):
  cursor = connection.cursor()
  if request.method=='POST':
    form = AddClassToTeacherForm(request.POST)
    cursor.execute("""
                   SELECT worker_id, last_name, first_name, patronymic
                   FROM Workers INNER JOIN [Worker roles] ON fk_role_id = role_id
                   WHERE [Worker roles].[name] = N'Вчитель'
                   """)
    teachers = cursor.fetchall()
    form.fields['teacher'].choices = [(teacher[0], f'{teacher[1]} {teacher[2]} {teacher[3]}') for teacher in teachers]
    cursor.execute("""
                   SELECT class_id, [name]
                   FROM Classes
                   WHERE fk_teacher_id IS NULL
                   """)
    student_classes = cursor.fetchall()
    form.fields['student_class'].choices = [(student_class[0], f'{student_class[1]}') for student_class in student_classes] 
    if form.is_valid():
      teacher = int(form.cleaned_data.get('teacher'))
      student_class = int(form.cleaned_data.get('student_class'))
      if student_class != 0:
        cursor.execute("""
                     UPDATE Classes
                     SET fk_teacher_id = %s
                     WHERE class_id = %s
                     """, (teacher, student_class))
        if cursor.rowcount > 0:
          response = redirect('show-teachers-list')
          return response
  else:
    form = AddClassToTeacherForm()
    cursor.execute("""
                   SELECT worker_id, last_name, first_name, patronymic
                   FROM Workers INNER JOIN [Worker roles] ON fk_role_id = role_id
                   WHERE [Worker roles].[name] = N'Вчитель'
                   """)
    teachers = cursor.fetchall()
    form.fields['teacher'].choices = [(teacher[0], f'{teacher[1]} {teacher[2]} {teacher[3]}') for teacher in teachers]
    cursor.execute("""
                   SELECT class_id, [name]
                   FROM Classes
                   WHERE fk_teacher_id IS NULL
                   """)
    student_classes = cursor.fetchall()
    form.fields['student_class'].choices = [(student_class[0], f'{student_class[1]}') for student_class in student_classes] 
    system_messages = messages.get_messages(request)
    for message in system_messages:
      pass
  return render(request, 'FormPage.html', {'w_last_name': request.session['last_name'],
                                            'w_first_name': request.session['first_name'], 
                                            'w_role': request.session['role'],
                                            'w_photo': request.session['photo'],
                                            'form': form})