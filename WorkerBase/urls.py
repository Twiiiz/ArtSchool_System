from django.urls import path, include
from .views import *

urlpatterns = [
    path('', handleLogin),
    path('coord_page/', showCoordPage),
    path('teacher_page/', showTeacherPage),
    path('teacher_page/lessons/', showTeacherLessonsPage, name='show-teacher-lesson-page'),
    path('teacher_page/class/<int:class_id>/', include([
      path('', showClassPage, name='show-teacher-class-page'),
      path('student_stat/', showStudentStatsPage, name='show-teacher-student-stats-page'),
      path('<int:student_id>/', showStudentPage, name='show-teacher-student-page'),
      path('student_comp/', showStudentCompPage, name='show-teacher-student-comp-page')
    ]))
]