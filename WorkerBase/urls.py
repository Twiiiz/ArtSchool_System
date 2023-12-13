from django.urls import path, include
from .views import *

urlpatterns = [
    path('', handleLogin),
    path('coord_page/', showCoordPage),
    path('teacher_page/', showTeacherPage, name='show-teacher-page'),
    path('teacher_page/fill_dates/', showDatesFormLessons, name='show-dates-form-lessons'),
    path('teacher_page/fill_dates/lessons/', showTeacherLessonsPage, name='show-teacher-lesson-page'),
    path('teacher_page/fill_dates/lessons/add_lesson-done', addTeacherLessonDone, name='add-teacher-lesson-done'),
    path('teacher_page/fill_dates/lessons/edit_lesson-done_<int:lesson_id>', editTeacherLessonDone, name='edit-teacher-lesson-done'),
    path('teacher_page/class/<int:class_id>/', include([
      path('', showClassPage, name='show-teacher-class-page'),
      path('<int:student_id>/', showStudentPage, name='show-teacher-student-page'),
      path('fill_dates/', include([
        path('', showDatesFormStudent, name='show-dates-form-students'),
        path('student_stat/', include([
        path('', showStudentStatsPage, name='show-teacher-student-stats-page'),
        path('add_grade/', addStudentGrade),
        path('add_attendance/', addStudentAttendance),
        path('edit_grade_<int:grade_id>_<int:student_id>_<int:lesson_id>/', editStudentGrade, name='edit-student-grade'),
        path('edit_attendance_<int:attend_id>_<int:student_id>_<int:lesson_id>/', editStudentAttendance, name='edit-student-attendance')
      ])),
      path('student_comp/', showStudentCompPage, name='show-teacher-student-comp-page')
      ])),
    ])),
    path('coord_page/view_teachers/', showTeachersPage),
    path('coord_page/view_classes/', showClassesPage),
]