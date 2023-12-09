from django.urls import path, include
from .views import *

urlpatterns = [
    path('', handleLogin),
    path('coord_page/', showCoordPage),
    path('teacher_page/', showTeacherPage),
    path('teacher_page/lessons/', showTeacherLessonsPage, name='show-teacher-lesson-page'),
    path('teacher_page/class/<int:class_id>/', include([
      path('', showClassPage, name='show-teacher-class-page'),
      path('<int:student_id>/', showStudentPage, name='show-teacher-student-page'),
    ]))
    # path('teacher_page/class/<int:class_id>', showClassPage, name='show-teacher-class-page'),
    # path('teacher_page/class/<int:class_id>/<int:student_id>', showStudentPage, name='show-teacher-student-page'),
    # path('teacher_page/class', showClassPage),
    # path('coord_page/class', showClassPage)
]