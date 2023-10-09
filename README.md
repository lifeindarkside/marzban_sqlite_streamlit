# Marzban Dashboard Project

Этот дашборд создан для визуализации статистик в проекте [Marzban](https://github.com/Gozargah/Marzban), используя SQLITE БД, встроенную в контейнер.
Собраны метрики по нодам и пользователям. 

![image](https://github.com/lifeindarkside/marzban_mysql_streamlit/assets/66727826/9fcc5f15-90ce-4292-894d-eaa01afd14da)
![image](https://github.com/lifeindarkside/marzban_mysql_streamlit/assets/66727826/8fcd7d19-1a5f-408d-8f83-7d5afc5da219)
![image](https://github.com/lifeindarkside/marzban_mysql_streamlit/assets/66727826/f55a79ec-2889-4897-8500-540a44c09b7b)


## Установка через docker

### Шаг 1: Изменение `docker-compose.yml`

Подключаем наш дашборд для запуска в докер контейнере. Для этого надо отредактировать файл `docker-compose.yml` в папке `/opt/marzban/` 

```bash
nano /opt/marzban/docker-compose.yml
```
Прописываем в него следующие строки
```
  analytics:
    image: lifeindarkside/marzban-analytics:latest
    environment: 
      - MY_SECRET_PASSWORD=ВАШПАРОЛЬ
    ports:
      - 8501:8501
    depends_on:
      - marzban
    volumes:
      - /opt/marzban/streamlit:/app
      - /var/lib/marzban:/var/lib/marzban
```

ВНИМАНИЕ! Замените `ВАШПАРОЛЬ` на любой ваш пароль. он необходим для формирования хеш пароля, чтобы ваш дашборд не светился на весь интернет открыто.

### Шаг 2: Запуск

Для запуска вам необходимо выполнить обновление и потом сделать restart

```bash
marzban update
```

```bash
marzban restart
```

Итогом панель запустится, но получить в нее доступ не получится. Так как мы не сменили хеш пароля.

### Шаг 3: Смена пароля

Для получения хеша пароля выполните команду 

```bash
docker exec -it marzban-analytics-1 python passwordhash.py
```

в консоли вы получите следующую инфу 
![image](https://github.com/lifeindarkside/marzban_sqlite_streamlit/assets/66727826/767371a6-9de9-49a5-abce-573183036a6f)

Полученный в консоли хеш, надо скопировать (без кавычек) и поместить в файле `config.yaml`

```bash
nano /opt/marzban/streamlit/config.yaml
```

В файле необходимо заменить логин и хеш пароля

Например:

```
credentials:
  usernames:
    root: #ваш логин
      name: root #отображаемое имя
      password: abc # To be replaced with hashed password
cookie:
  expiry_days: 30
  key: 'sajkhfdjklhfjkhsdlfkasdfasdfghlsdhfjksdhfjklhgadfgsdfgggsadfkljhasfghddfshdfhfgh9ogsdfgsdfgwwrhfgjrufgheruhwewerwerwergf' # Must be string
  name: random_cookie_name # Must be string
```
В строке key и name может быть любое текстовое значение без пробелов (это будут созранены ваши cookie файлы)
Сохраните файл после дредактирования и обновите данные в контейнере

```bash
marzban update
```

```bash
marzban restart
```

### Шаг 4:
Зайти на дашборд можно по адресу 
`http://ip:8501/`
где `ip` может быть ip адресом вашего сервера или доменом

Если необходимо сменить порт, отредактируйте `docker-compose.yml` файл. Смените в нем параметр `port`.

Например:
```
    ports:
      - 9901:8501
```




## Сборка из исходников файла

### Шаг 1: Загрузка файлов

Загрузите файлы напрямую в папку `/opt/marzban/`

```bash
cd /opt/marzban/
git clone https://github.com/lifeindarkside/marzban_sqlite_streamlit.git
```

### Шаг 2: Добавление контейнера

Подключаем наш дашборд для запуска в докер контейнере. Для этого надо отредактировать файл `docker-compose.yml` в папке `/opt/marzban/` 

```bash
nano /opt/marzban/docker-compose.yml
```

Прописываем в него следующие строки
```
  analytics:
    build: ./marzban_sqlite_streamlit
    environment: 
      - MY_SECRET_PASSWORD=ВАШПАРОЛЬ
    ports:
      - 8501:8501
    depends_on:
      - marzban
    volumes:
      - /opt/marzban/marzban_sqlite_streamlit:/app
      - /var/lib/marzban:/var/lib/marzban
```

ВНИМАНИЕ! Замените `ВАШПАРОЛЬ` на любой ваш пароль. он необходим для формирования хеш пароля, чтобы ваш дашборд не светился на весь интернет открыто.

Итоговый файл должен выглядеть примерно так
```
services:
  marzban:
    image: gozargah/marzban:dev
    restart: always
    env_file: .env
    network_mode: host
    volumes:
      - /var/lib/marzban:/var/lib/marzban

  analytics:
    build: ./marzban_sqlite_streamlit
    environment: 
      - MY_SECRET_PASSWORD=abc123123123
    ports:
      - 8501:8501
    depends_on:
      - marzban
    volumes:
      - /opt/marzban/marzban_sqlite_streamlit:/app
      - /var/lib/marzban:/var/lib/marzban
```

### Шаг 3: Запуск

Для запуска вам необходимо выполнить обновление и потом сделать restart

```bash
marzban update
```

```bash
marzban restart
```

Итогом панель запустится, но получить в нее доступ не получится. Так как мы не сменили хеш пароля.

### Шаг 4: Смена пароля

Для получения хеша пароля выполните команду 

```bash
docker exec -it marzban-analytics-1 python passwordhash.py
```

в консоли вы получите следующую инфу 
![image](https://github.com/lifeindarkside/marzban_sqlite_streamlit/assets/66727826/767371a6-9de9-49a5-abce-573183036a6f)

Полученный в консоли хеш, надо скопировать и поместить в файле `config.yaml`

```bash
nano /opt/marzban/marzban_sqlite_streamlit/config.yaml
```

В файле необходимо заменить логин и хеш пароля

Например:

```
credentials:
  usernames:
    root: #ваш логин
      name: root #отображаемое имя
      password: abc # To be replaced with hashed password
cookie:
  expiry_days: 30
  key: 'sajkhfdjklhfjkhsdlfkasdfasdfghlsdhfjksdhfjklhgadfgsdfgggsadfkljhasfghddfshdfhfgh9ogsdfgsdfgwwrhfgjrufgheruhwewerwerwergf' # Must be string
  name: random_cookie_name # Must be string
```
В строке key и name может быть любое текстовое значение без пробелов (это будут созранены ваши cookie файлы)
Сохраните файл после дредактирования

### Шаг 5:
Зайти на дашборд можно по адресу 
`http://ip:8501/`
где `ip` может быть ip адресом вашего сервера или доменом

Если необходимо сменить порт, отредактируйте `docker-compose.yml` файл. Смените в нем параметр `port`.

Например:
```
    ports:
      - 9901:8501
```





