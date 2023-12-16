from django.http import Http404
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.urls import reverse
from django.core.files.storage import default_storage

from WorkerBase.img_path_handler import Rename
from .forms import *
from datetime import date


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

def showTeacherPage(request):
  if not request.COOKIES.get('logged_in') or request.session['role'] != 'Вчитель':
     raise Http404
  # response.set_cookie('logged_in', 'True', secure=True)
  # request.session['role'] = 'Вчитель'
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
  # if not request.COOKIES.get('logged_in') or request.session['role'] != 'Вчитель' or request.session['role'] != 'Координатор':
  #    raise Http404
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
  cursor.execute("""
                 SELECT *
                 FROM Students
                 WHERE student_id = %s
                 """, (student_id,))
  student_data = cursor.fetchone()
  cursor.execute("""
                 SELECT last_name, first_name, patronymic
                 FROM Workers INNER JOIN Classes ON worker_id = fk_teacher_id
                 WHERE class_id = %s
                 """, (class_id,))
  main_teacher = cursor.fetchone()
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
  # biggest_date = max(lessons_done, key=lambda t: t[2])[2]
  # biggest_start_time = max(lessons_done, key=lambda t: t[3])[3]
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
    form = StudentGradeForm(request.POST, is_editing=False)
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
    print('GOT THE FORM')
    if form.is_valid():
      grade_info = [form.cleaned_data.get('student'),
                    form.cleaned_data.get('grade'),
                    form.cleaned_data.get('eval_elt'),
                    form.cleaned_data.get('lesson')]
      for bla in grade_info:
        print(bla)
      print('OKAY')
      response = redirect('show-teacher-student-stats-page', class_id=class_id)
      response.set_cookie('logged_in', 'True', secure=True)
      return response
    else:
      print('NOT VALID')
      print(request.POST)
  else:
    form = StudentGradeForm(is_editing=False)
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

def editStudentGrade(request, class_id, grade_id, student_id, lesson_id):
  cursor = connection.cursor()
  if request.method=='POST':
    form = StudentGradeForm(request.POST, is_editing=True)
    form.fields['student'].choices = [(student_id, 'Цей учень')]
    cursor.execute("""
                   SELECT element_id, [name]
                   FROM [Evaluated elements]
                   """)
    eval_elts = cursor.fetchall()
    form.fields['eval_elt'].choices = [(eval_elt[0], eval_elt[1]) for eval_elt in eval_elts]
    form.fields['lesson'].choices = [(lesson_id, 'Це заняття')]
    print('GOT THE FORM')
    if form.is_valid():
      grade_info = [form.cleaned_data.get('student'),
                    form.cleaned_data.get('grade'),
                    form.cleaned_data.get('eval_elt'),
                    form.cleaned_data.get('lesson')]
      for bla in grade_info:
        print(bla)
      print(grade_id)
      print('OKAY')
      response = redirect('show-teacher-page')
      response.set_cookie('logged_in', 'True', secure=True)
      return response
    else:
      print('NOT VALID')
      print(request.POST)
  else:
    form = StudentGradeForm(is_editing=True)
    form.fields['student'].choices = [(student_id, 'Цей учень')]
    form.fields['student'].initial = student_id
    cursor.execute("""
                   SELECT element_id, [name]
                   FROM [Evaluated elements]
                   """)
    eval_elts = cursor.fetchall()
    form.fields['eval_elt'].choices = [(eval_elt[0], eval_elt[1]) for eval_elt in eval_elts]
    form.fields['lesson'].choices = [(lesson_id, 'Це заняття')]
    form.fields['lesson'].initial = lesson_id
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
    form = StudentAttendanceForm(request.POST, is_editing=False)
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
    print('GOT THE FORM')
    if form.is_valid():
      grade_info = [form.cleaned_data.get('student'),
                    form.cleaned_data.get('lesson'),
                    form.cleaned_data.get('attendance'),]
      for bla in grade_info:
        print(bla)
      print('OKAY')
      response = redirect('show-teacher-student-stats-page', class_id=class_id)
      response.set_cookie('logged_in', 'True', secure=True)
      return response
    else:
      print('NOT VALID')
      print(request.POST)
  else:
    form = StudentAttendanceForm(is_editing=False)
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

def editStudentAttendance(request, class_id, attend_id, student_id, lesson_id):
  cursor = connection.cursor()
  if request.method=='POST':
    form = StudentAttendanceForm(request.POST, is_editing=True)
    form.fields['student'].choices = [(student_id, 'Цей учень')]
    form.fields['lesson'].choices = [(lesson_id, 'Це заняття')]
    print('GOT THE FORM')
    if form.is_valid():
      grade_info = [form.cleaned_data.get('student'),
                    form.cleaned_data.get('lesson'),
                    form.cleaned_data.get('attendance'),]
      for bla in grade_info:
        print(bla)
      print('OKAY')
      response = redirect('show-teacher-page')
      response.set_cookie('logged_in', 'True', secure=True)
      return response
    else:
      print('NOT VALID')
      print(request.POST)
  else:
    form = StudentAttendanceForm(is_editing=True)
    form.fields['student'].choices = [(student_id, 'Цей учень')]
    form.fields['student'].initial = student_id
    form.fields['lesson'].choices = [(lesson_id, 'Це заняття')]
    form.fields['lesson'].initial = lesson_id
    system_messages = messages.get_messages(request)
    for message in system_messages:
      pass
  return render(request, 'FormPage.html', {'form': form})

def showDatesFormStudent(request, class_id):
  if 'from_date' in request.session and 'to_date' in request.session:
    del request.session['from_date']
    del request.session['to_date']
  if request.method=='POST':
    form = DatesForm(request.POST)
    print('GOT THE FORM')
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
        print('ERROR! NULL PARAMETER')
    else:
      print('NOT VALID')
      print(request.POST)
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
    print('GOT THE FORM')
    if form.is_valid():
      from_date = form.cleaned_data.get('from_date')
      to_date = form.cleaned_data.get('to_date')
      request.session['from_date'] = from_date.strftime('%Y-%m-%d')
      request.session['to_date'] = to_date.strftime('%Y-%m-%d')
      response = redirect('show-teacher-lesson-page')
      return response
    else:
      print('NOT VALID')
      print(request.POST)
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
    print('GOT THE FORM')
    if form.is_valid():
      print(request.POST)
      response = redirect('show-teacher-lesson-page')
      return response
    else:
      print('NOT VALID')
      print(request.POST)
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
    print('GOT THE FORM')
    if form.is_valid():
      print(request.POST)
      response = redirect('show-teacher-lesson-page')
      return response
    else:
      print('NOT VALID')
      print(request.POST)
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

def handleStudentComp(request, class_id):
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
    form.fields['skill'].choices = [(skill[0], f'Компетенція: {skill[1]}, Дисципліна: {skill[2]}') for skill in skills]
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
      print(request.POST)
      if request.GET.get('action_type') is not None:
        if request.GET.get('action_type') == 'insert':
          print('INSERT')
        elif request.GET.get('action_type') == 'alter':
          print('ALTER')
        response = redirect('show-teacher-student-comp-page', class_id=class_id)
        return response
    else:
      print('NOT VALID')
      print(request.POST)
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
    form.fields['skill'].choices = [(skill[0], f'Компетенція: {skill[1]}, Дисципліна: {skill[2]}') for skill in skills]
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
                   """)
    classes = cursor.fetchall()
    form.fields['personal_class'].choices = [(personal_class[0], f'{personal_class[1]}') for personal_class in classes]
    cursor.execute("""
                   SELECT *
                   FROM Disciplines
                   """)
    disciplines = cursor.fetchall()
    form.fields['discipline'].choices = [(discipline[0], f'{discipline[1]}') for discipline in disciplines]
    if form.is_valid():
      print(request.POST)
      photo = request.FILES['photo']
      filepath = Rename.rename('teacher', photo.name)
      default_storage.save(filepath, photo)
      response = redirect('show-coord-page')
      return response
    else:
      print('NOT VALID')
      print(request.POST)
  else:
    form = CreateTeacherForm()
    cursor.execute("""
                   SELECT class_id, [name]
                   FROM Classes
                   """)
    classes = cursor.fetchall()
    form.fields['personal_class'].choices = [(personal_class[0], f'{personal_class[1]}') for personal_class in classes]
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
      print(request.POST)
      photo = request.FILES['photo']
      filepath = Rename.rename('student', photo.name)
      default_storage.save(filepath, photo)
      response = redirect('show-coord-page')
      return response
    else:
      print('NOT VALID')
      print(request.POST)
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
                 FROM Students INNER JOIN [Students in class]
                      ON Students.student_id = [Students in class].fk_student_id
                 WHERE student_id NOT IN (SELECT fk_student_id
                                          FROM [Students in class]
                                          WHERE fk_class_id = %s)
                 """, (class_id,))
  new_students = cursor.fetchall()
  if request.method=='POST':
    form = AddStudentToClassForm(request.POST)
    form.fields['student'].choices = [(student[0], f'{student[1]} {student[2]} {student[3]}') for student in new_students]
    if form.is_valid():
      print(request.POST)
    else:
      print('NOT VALID')
      print(request.POST)
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
                 """)
  teacher_classes = cursor.fetchall()
  return render(request, 'CoordTeacherPage.html', {'w_last_name': request.session['last_name'],
                                            'w_first_name': request.session['first_name'], 
                                            'w_role': request.session['role'],
                                            'w_photo': request.session['photo'],
                                            'teacher_data': teacher,
                                            'teacher_classes_data': teacher_classes})