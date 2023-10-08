# Marzban Dashboard Project

Этот дашборд создан для визуализации статистик в проекте [Marzban](https://github.com/Gozargah/Marzban), используя MySQL для хранения данных.
![image](https://github.com/lifeindarkside/marzban_mysql_streamlit/assets/66727826/9fcc5f15-90ce-4292-894d-eaa01afd14da)
![image](https://github.com/lifeindarkside/marzban_mysql_streamlit/assets/66727826/8fcd7d19-1a5f-408d-8f83-7d5afc5da219)
![image](https://github.com/lifeindarkside/marzban_mysql_streamlit/assets/66727826/f55a79ec-2889-4897-8500-540a44c09b7b)


## Установка

### Шаг 1: Подготовка конфигурационного файла

Первым делом, вам нужно подготовить файл конфигурации. Скопируйте `config.yaml.example` в новый файл с именем `config.yaml` и заполните все необходимые поля соответствующими значениями вашей установки Marzban и базы данных MySQL.

Пример:

```yaml
credentials:
  ssh_host: 'your_ssh_host_here'
  ssh_port: your_ssh_port_here
  ssh_user: 'your_ssh_username_here'
  ssh_pass: 'your_ssh_password_here'
  sql_hostname: 'your_sql_hostname_here'
  sql_port: your_sql_port_here
  sql_username: 'your_sql_username_here'
  sql_password: 'your_sql_password_here'
  sql_main_database: 'your_sql_main_database_here'
```
### Шаг 2: Установка зависимостей

Перед запуском проекта убедитесь, что у вас установлен Python версии 3.8 или выше. Затем установите все необходимые зависимости, используя следующую команду в корневой директории проекта:

```sh
pip install -r requirements.txt
```

Либо установите и активируйте окружение Conda
```sh
conda env create --name marzban-streamlit --file=conda_env_streamlit.yml
```
### Шаг 3: Запуск проекта
Если вы создали окружение Conda, то сначала активируйте его
```sh
conda activate marzban-streamlit
```

После того как вы установили все необходимые зависимости, вы можете запустить проект с помощью следующей команды в корневой директории проекта:

```sh
streamlit run main.py
```
Автоматически откроется страница браузера с адресом http://localhost:8501/

Если необходимо сменить порт:
```sh
streamlit run main.py --server.port 8503
```




