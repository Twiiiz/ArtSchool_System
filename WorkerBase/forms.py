from django import forms

class LoginForm(forms.Form):
   login = forms.CharField(max_length=20, required=True, label='Логін', widget=forms.TextInput(attrs={'class': 'username'}))
   password = forms.CharField(max_length=20, required=True, label='Пароль', widget=forms.PasswordInput(attrs={'class': 'password'}))

class StudentGradeForm(forms.Form):
   student = forms.ChoiceField(label='Учень', required=True)
   grade = forms.IntegerField(min_value=1, max_value=5, required=True, label='Оцінка')
   eval_elt = forms.ChoiceField(label='Оцінюваний елемент', required=True)
   lesson = forms.ChoiceField(label='Проведене Заняття', required=True)

   def __init__(self, *args, **kwargs):
       self.is_editing = kwargs.pop('is_editing', False)
       super(StudentGradeForm, self).__init__(*args, **kwargs)
       if self.is_editing:
           self.fields['student'].widget = forms.HiddenInput()
           self.fields['lesson'].widget = forms.HiddenInput()

class StudentAttendanceForm(forms.Form):
   student = forms.ChoiceField(label='Учень', required=True)
   lesson = forms.ChoiceField(label='Проведене Заняття', required=True)
   attendance = forms.TypedChoiceField(choices=[('відвідано', 'відвідано'),
                                                ('пропущено', 'пропущено')], coerce=str, required=True, label='Статус')
   
   def __init__(self, *args, **kwargs):
       self.is_editing = kwargs.pop('is_editing', False)
       super(StudentAttendanceForm, self).__init__(*args, **kwargs)
       if self.is_editing:
           self.fields['student'].widget = forms.HiddenInput()
           self.fields['lesson'].widget = forms.HiddenInput()

class DatesForm(forms.Form):
    from_date = forms.DateField(label='Від', required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    to_date = forms.DateField(label='До', required=True, widget=forms.DateInput(attrs={'type': 'date'}))

    def clean(self):
       cleaned_data = super().clean()
       date1 = cleaned_data.get('from_date')
       date2 = cleaned_data.get('to_date')

       if date1 and date2 and date1 > date2:
           raise forms.ValidationError("Дата у полі 'від' повинна бути менша, ніж дата у полі 'до'")

       return cleaned_data
    
class TeacherLessonDone(forms.Form):
    discipline = forms.ChoiceField(label='Дисципліна', required=True)
    class_students = forms.ChoiceField(label='Клас', required=True)
    date = forms.DateField(label='Дата', required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    start_time = forms.TimeField(input_formats=['%H:%M'], label='Час початку заняття')
    end_time = forms.TimeField(input_formats=['%H:%M'], label='Час кінця заняття')

class StudentCompForm(forms.Form):
    student = forms.ChoiceField(label='Учень', required=True)
    level = forms.ChoiceField(label='Рівень засвоєння', required=True)
    skill = forms.ChoiceField(label='Вміння', required=True)
    date = forms.DateField(label='Дата', required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    time = forms.TimeField(input_formats=['%H:%M'], label='Час')

class CreateTeacherForm(forms.Form):
      first_name = forms.CharField(max_length=50, required=True, label="Ім'я")
      last_name = forms.CharField(max_length=50, required=True, label="Прізвище")
      patronymic = forms.CharField(max_length=50, label="По-батькові")
      personal_class = forms.ChoiceField(label='Клас учнів', required=True)

      login = forms.CharField(max_length=20, required=True, label='Логін', widget=forms.TextInput(attrs={'class': 'username'}))
      password = forms.CharField(max_length=20, required=True, label='Пароль', widget=forms.PasswordInput(attrs={'class': 'password'}))

      discipline = forms.ChoiceField(label='Дисципліна', required=True)

      photo = forms.ImageField(label='Фотографія')

class CreateStudentForm(forms.Form):
   first_name = forms.CharField(max_length=50, required=True, label="Ім'я")
   last_name = forms.CharField(max_length=50, required=True, label="Прізвище")
   patronymic = forms.CharField(max_length=50, label="По-батькові")
   date_of_birth = forms.DateField(label='Дата народження', widget=forms.DateInput(attrs={'type': 'date'}))
   photo = forms.ImageField(label='Фотографія')

class AddStudentToClassForm(forms.Form):
    student = forms.ChoiceField(label='Учень без класу', required=True)

class AddPlannedLessonForm(forms.Form):
    discipline = forms.ChoiceField(label='Дисципліна', required=True)
    student_class = forms.ChoiceField(label='Клас', required=True)
    teacher = forms.ChoiceField(label='Вчитель', required=True)
    date = forms.DateField(label='Дата', required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    start_time = forms.TimeField(input_formats=['%H:%M'], label='Час початку заняття')
    end_time = forms.TimeField(input_formats=['%H:%M'], label='Час кінця заняття')
