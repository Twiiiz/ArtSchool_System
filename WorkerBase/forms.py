from django import forms

class LoginForm(forms.Form):
   login = forms.CharField(max_length=20, required=True, label='Логін', widget=forms.TextInput(attrs={'class': 'username'}))
   password = forms.CharField(max_length=20, required=True, label='Пароль', widget=forms.PasswordInput(attrs={'class': 'password'}))

class StudentForm(forms.Form):
   first_name = forms.CharField(max_length=50, required=True, label="Ім'я")
   last_name = forms.CharField(max_length=50, required=True, label="Прізвище")
   patronymic = forms.CharField(max_length=50, label="По-батькові")
   date_of_birth = forms.DateField(label='Дата народження')
   