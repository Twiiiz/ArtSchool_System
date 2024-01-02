from django.urls import path, include
from .views import *

urlpatterns = [
    path('', include([
      path('', handleLogin, name='system-entry'),
      path('teacher_page/', showTeacherPage, name='show-teacher-page'),
      path('coord_page/', showCoordPage, name='show-coord-page')
    ]), name='system-entry-and-personal-pages'),
    path('teacher_page/fill_dates/', include([
      path('', showDatesFormLessons, name='show-dates-form-lessons'),
      path('lessons/', showTeacherLessonsPage, name='show-teacher-lesson-page'),
      path('lessons/add_lesson-done', addTeacherLessonDone, name='add-teacher-lesson-done'),
      path('lessons/edit_lesson-done_<int:lesson_id>', editTeacherLessonDone, name='edit-teacher-lesson-done'),
    ]), name='work-with-teacher-lessons'),
    path('teacher_page/class/<int:class_id>/', include([
      path('', include([
        path('', showClassPage, name='show-teacher-class-page'),
        path('<int:student_id>/', showStudentPage, name='show-teacher-student-page'),
      ]), name='work-with-class-students'),
      path('fill_dates/', include([
        path('', showDatesFormStudent, name='show-dates-form-students'),
        path('student_stat/', include([
        path('', showStudentStatsPage, name='show-teacher-student-stats-page'),
        path('add_grade/', addStudentGrade),
        path('add_attendance/', addStudentAttendance),
        path('edit_grade_<int:grade_id>/', editStudentGrade, name='edit-student-grade'),
        path('edit_attendance_<int:attend_id>/', editStudentAttendance, name='edit-student-attendance')
      ]), name='work-with-class-students-stats'),
      path('student_comp/', include([
        path('', showStudentCompPage, name='show-teacher-student-comp-page'),
        path('add_comp/', addStudentComp, name='add-comp'),
        path('edit_comp/<int:comp_id>/', editStudentComp, name='edit-comp')
      ]), name='work-with-class-students-comp'),
      ])),
    ]), name='work-with-class'),
    path('coord_page/view-teachers/', include([
      path('', showTeachersListPage, name='show-teachers-list'),
      path('<int:teacher_id>/', showCoordTeacherPage, name='show-coord-teacher-page'),
      path('/add_teacher/', addTeacher, name='add-teacher'),
      path('/add_teacher_to_class', addTeacherToClass, name='add-teacher-to-class')
    ]), name='work-with-teachers'),

    path('coord_page/add_student/', addStudent, name='add-student'),
    path('coord_page/view_classes/', include([
      path('', showClassesPage, name='show-coord-classes-page'),
      path('class/<int:class_id>/', showClassPage, name='show-coord-class-page'),
      path('<int:class_id>/<int:student_id>', showStudentPage, name='show-coord-student-page'),
      path('<int:class_id>/add_student', addStudentToClass, name='add-student-to-class'),
      path('add_class/', addClass, name='add-class')
    ]), name='work-with-classes-and-students'),
    path('coord_page/fill_dates/', include([
      path('', showDatesFormCoord, name='show-dates-form-coord'),
      path('view_lessons/', showCoordLessons, name='show-coord-lessons'),
      path('view_lessons/add_lesson/', addPlannedLesson, name='add-coord-lessons'),
      path('view_lessons/edit_<int:lesson_id>', editPlannedLesson, name='edit-coord-lessons')
    ]), name='work-with-all-lessons'),
]