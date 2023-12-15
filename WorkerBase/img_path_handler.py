from django.db import connection
import os

class Rename(object):
  def rename(role, filename):
    ext = filename.split('.')[-1]
    cursor = connection.cursor()
    filename = ''
    if role == 'student':
        cursor.execute("""
                       SELECT MAX(student_id)
                       FROM Students
                       """)
        student_id = cursor.fetchall()
        student_id = student_id[0][0] + 1
        filename = 'id_{}.{}'.format(student_id, ext)
        folder = 'StudentIMG/'
    elif role == 'teacher':
        cursor.execute("""
                       SELECT MAX(worker_id)
                       FROM Workers
                       """)
        teacher_id = cursor.fetchall()
        teacher_id = teacher_id[0][0] + 1
        filename = 'id_{}.{}'.format(teacher_id, ext)
        folder = 'WorkerIMG/'
    return os.path.join(folder, filename)