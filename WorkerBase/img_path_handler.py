from django.db import connection
import os

class Rename(object):
  def rename(role, filename):
    ext = filename.split('.')[-1]
    cursor = connection.cursor()
    filename = ''
    if role == 'student':
        cursor.execute("""
                       SELECT IDENT_CURRENT('Students')
                       """)
        student_id = cursor.fetchone()
        student_id = student_id[0] + 1
        filename = 'id_{}.{}'.format(student_id, ext)
        folder = 'StudentIMG/'
    elif role == 'teacher':
        cursor.execute("""
                       SELECT IDENT_CURRENT('Workers')
                       """)
        teacher_id = cursor.fetchone()
        teacher_id = teacher_id[0] + 1
        filename = 'id_{}.{}'.format(teacher_id, ext)
        folder = 'WorkerIMG/'
    return os.path.join(folder, filename)