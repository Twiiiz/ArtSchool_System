# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

class ClassSpecialisation(models.Model):
    class_specialisation_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'class_specialisation'


class CompeteneceLevel(models.Model):
    competence_level_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'competenece_level'


class Discipline(models.Model):
    discipline_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'discipline'


class DisciplineSkill(models.Model):
    discipline_skill_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    discipline = models.ForeignKey(Discipline, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'discipline_skill'

class EvaluatedElement(models.Model):
    evaluated_element_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=35)
    discipline = models.ForeignKey(Discipline, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'evaluated_element'


class Lesson(models.Model):
    lesson_id = models.AutoField(primary_key=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    student_class = models.ForeignKey('StudentClass', models.DO_NOTHING)
    discipline = models.ForeignKey(Discipline, models.DO_NOTHING)
    lesson_status = models.ForeignKey('LessonStatus', models.DO_NOTHING)
    teacher = models.ForeignKey('Worker', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'lesson'


class LessonAttendance(models.Model):
    lesson_attendance_id = models.AutoField(primary_key=True)
    presence = models.CharField(max_length=15)
    lesson = models.ForeignKey(Lesson, models.DO_NOTHING)
    student = models.ForeignKey('Student', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'lesson_attendance'


class LessonStatus(models.Model):
    lesson_status_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'lesson_status'


class Student(models.Model):
    student_id = models.AutoField(primary_key=True)
    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    patronymic = models.CharField(max_length=50, blank=True, null=True)
    date_of_birth = models.DateField()
    photo_path = models.CharField(max_length=80)

    class Meta:
        managed = False
        db_table = 'student'


class StudentClass(models.Model):
    student_class_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    specialty = models.ForeignKey(ClassSpecialisation, models.DO_NOTHING)
    teacher = models.ForeignKey('Worker', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'student_class'


class StudentCompetence(models.Model):
    student_competence_id = models.AutoField(primary_key=True)
    date_time = models.DateTimeField()
    competence_level = models.ForeignKey(CompeteneceLevel, models.DO_NOTHING)
    discipline_skill = models.ForeignKey(DisciplineSkill, models.DO_NOTHING)
    student = models.ForeignKey(Student, models.DO_NOTHING)
    teacher = models.ForeignKey('Worker', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'student_competence'


class StudentGrade(models.Model):
    student_grade_id = models.AutoField(primary_key=True)
    value = models.IntegerField()
    evaluated_element = models.ForeignKey(EvaluatedElement, models.DO_NOTHING)
    lesson = models.ForeignKey(Lesson, models.DO_NOTHING)
    student = models.ForeignKey(Student, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'student_grade'


class StudentInClass(models.Model):
    student_in_class_id = models.AutoField(primary_key=True)
    student_class = models.ForeignKey(StudentClass, models.DO_NOTHING)
    student = models.ForeignKey(Student, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'student_in_class'

class TeacherDiscipline(models.Model):
    teacher_discipline_id = models.AutoField(primary_key=True)
    discipline = models.ForeignKey(Discipline, models.DO_NOTHING)
    teacher = models.ForeignKey('Worker', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'teacher_discipline'


class Worker(models.Model):
    worker_id = models.AutoField(primary_key=True)
    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    patronymic = models.CharField(max_length=50, blank=True, null=True)
    photo_path = models.CharField(max_length=80)
    worker_role = models.ForeignKey('WorkerRole', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'worker'


class WorkerLoginData(models.Model):
    login_data_id = models.AutoField(primary_key=True)
    worker = models.ForeignKey(Worker, models.DO_NOTHING)
    auth_user_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'worker_login_data'


class WorkerRole(models.Model):
    worker_role_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'worker_role'