import os
import streamlit_authenticator as stauth

# Использование пароля из переменной окружения
password = os.environ.get('MY_SECRET_PASSWORD', 'default_password')

# Вывод в консоль хеша пароля 
print(stauth.Hasher([password]).generate())