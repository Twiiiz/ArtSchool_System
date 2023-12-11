from django import forms

class LoginForm(forms.Form):
   login = forms.CharField(max_length=20, required=True, label='Логін', widget=forms.TextInput(attrs={'class': 'username'}))
   password = forms.CharField(max_length=20, required=True, label='Пароль', widget=forms.PasswordInput(attrs={'class': 'password'}))

# class StudentForm(forms.Form):
#    first_name = forms.CharField(max_length=50, required=True, label="Ім'я")
#    last_name = forms.CharField(max_length=50, required=True, label="Прізвище")
#    patronymic = forms.CharField(max_length=50, label="По-батькові")
#    date_of_birth = forms.DateField(label='Дата народження')

# class TeacherForm(forms.Form):
#       first_name = forms.CharField(max_length=50, required=True, label="Ім'я")
#       last_name = forms.CharField(max_length=50, required=True, label="Прізвище")
#       patronymic = forms.CharField(max_length=50, label="По-батькові")

#       login = forms.CharField(max_length=20, required=True, label='Логін', widget=forms.TextInput(attrs={'class': 'username'}))
#       password = forms.CharField(max_length=20, required=True, label='Пароль', widget=forms.PasswordInput(attrs={'class': 'password'}))

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
   attendance = forms.TypedChoiceField(choices=[('', '--- Статус ---'),
                                                ('відвідано', 'відвідано'),
                                                ('пропущено', 'пропущено')], coerce=str, required=True, label='Статус')