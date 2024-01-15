from django.db import models

class Classes(models.Model):
    class_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    fk_spec = models.ForeignKey('Specialisations', models.DO_NOTHING)
    fk_teacher = models.ForeignKey('Workers', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Classes'


class CompetenceLevels(models.Model):
    level_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'Competence levels'


class DisciplineSkills(models.Model):
    skill_id = models.AutoField(primary_key=True)
    fk_discipline = models.ForeignKey('Disciplines', models.DO_NOTHING)
    name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'Discipline skills'


class Disciplines(models.Model):
    discipline_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'Disciplines'


class EvaluatedElements(models.Model):
    element_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=35)

    class Meta:
        managed = False
        db_table = 'Evaluated elements'


class LessonStatuses(models.Model):
    status_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'Lesson statuses'


class Lessons(models.Model):
    lesson_id = models.AutoField(primary_key=True)
    fk_discipline = models.ForeignKey(Disciplines, models.DO_NOTHING)
    fk_class = models.ForeignKey(Classes, models.DO_NOTHING)
    fk_teacher = models.ForeignKey('Workers', models.DO_NOTHING)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    fk_status = models.ForeignKey(LessonStatuses, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'Lessons'


class Specialisations(models.Model):
    spec_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'Specialisations'


class StudentAttendances(models.Model):
    attend_id = models.AutoField(primary_key=True)
    fk_student = models.ForeignKey('Students', models.DO_NOTHING)
    fk_lesson = models.ForeignKey(Lessons, models.DO_NOTHING)
    presence = models.CharField(max_length=15)

    class Meta:
        managed = False
        db_table = 'Student attendances'


class StudentCompetencies(models.Model):
    stud_comp_id = models.AutoField(primary_key=True)
    fk_skill = models.ForeignKey(DisciplineSkills, models.DO_NOTHING)
    date_time = models.DateTimeField()
    fk_teacher = models.ForeignKey('Workers', models.DO_NOTHING)
    fk_student = models.ForeignKey('Students', models.DO_NOTHING)
    fk_level = models.ForeignKey(CompetenceLevels, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'Student competencies'


class StudentGrades(models.Model):
    grade_id = models.AutoField(primary_key=True)
    fk_student = models.ForeignKey('Students', models.DO_NOTHING)
    grade = models.IntegerField()
    fk_eval_elt = models.ForeignKey(EvaluatedElements, models.DO_NOTHING, db_column='fk_eval_elt')
    fk_lesson = models.ForeignKey(Lessons, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'Student grades'


class Students(models.Model):
    student_id = models.AutoField(primary_key=True)
    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    patronymic = models.CharField(max_length=50, blank=True, null=True)
    date_of_birth = models.DateField()
    photo_path = models.CharField(max_length=80)

    class Meta:
        managed = False
        db_table = 'Students'


class StudentsInClass(models.Model):
    stud_class_id = models.AutoField(primary_key=True)
    fk_student = models.ForeignKey(Students, models.DO_NOTHING)
    fk_class = models.ForeignKey(Classes, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'Students in class'


class TeacherDisciplines(models.Model):
    teach_disc_id = models.AutoField(primary_key=True)
    fk_teacher = models.ForeignKey('Workers', models.DO_NOTHING)
    fk_discipline = models.ForeignKey(Disciplines, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'Teacher disciplines'


class WorkerEntryData(models.Model):
    data_id = models.AutoField(primary_key=True)
    fk_worker = models.ForeignKey('Workers', models.DO_NOTHING)
    login = models.CharField(max_length=20)
    password = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'Worker entry data'


class WorkerRoles(models.Model):
    role_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'Worker roles'


class Workers(models.Model):
    worker_id = models.AutoField(primary_key=True)
    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    patronymic = models.CharField(max_length=50, blank=True, null=True)
    fk_role = models.ForeignKey(WorkerRoles, models.DO_NOTHING)
    photo_path = models.CharField(max_length=80)

    class Meta:
        managed = False
        db_table = 'Workers'