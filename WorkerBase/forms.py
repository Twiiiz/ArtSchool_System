from django import forms

class LoginForm(forms.Form):
   login = forms.CharField(max_length=20, required=True, label='Логін', widget=forms.TextInput(attrs={'class': 'username'}))
   password = forms.CharField(max_length=20, required=True, label='Пароль', widget=forms.PasswordInput(attrs={'class': 'password'}))