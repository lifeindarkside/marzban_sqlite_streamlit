# Marzban Dashboard Project
<p align="center">
 <a href="./README.md">
 English
 </a>
 /
 <a href="./README-RU.md">
 Русский
 </a>
</p>

Этот дашборд создан для визуализации статистик в проекте [Marzban](https://github.com/Gozargah/Marzban), используя SQLITE БД, встроенную в контейнер.
Собраны метрики по нодам и пользователям. Работает только на ветке marzban:dev

![image](https://github.com/lifeindarkside/marzban_sqlite_streamlit/assets/66727826/2fd39235-9139-46a2-a734-2e200edf7861)
![image](https://github.com/lifeindarkside/marzban_sqlite_streamlit/assets/66727826/daaca12f-0e37-4542-a303-e44bb31c6b04)
![image](https://github.com/lifeindarkside/marzban_sqlite_streamlit/assets/66727826/6b54c4ce-f303-4bcb-8070-93ab9e8de191)

![image](https://github.com/lifeindarkside/marzban_mysql_streamlit/assets/66727826/8fcd7d19-1a5f-408d-8f83-7d5afc5da219)
![image](https://github.com/lifeindarkside/marzban_mysql_streamlit/assets/66727826/f55a79ec-2889-4897-8500-540a44c09b7b)


## Установка через docker

### Шаг 1: Изменение `docker-compose.yml`

Подключаем наш дашборд для запуска в докер контейнере. Для этого надо отредактировать файл `docker-compose.yml` в папке `/opt/marzban/` 

```bash
nano /opt/marzban/docker-compose.yml
```
Добавляем в него следующие строки
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
      - /opt/marzban/streamlit/config.yaml:/app/config.yaml
      - /var/lib/marzban:/var/lib/marzban
```

ВНИМАНИЕ! Замените `ВАШПАРОЛЬ` на любой ваш пароль. он необходим для формирования хеш пароля, чтобы ваш дашборд не светился на весь интернет открыто.

### Шаг 2: Создаем конфиг для streamlit

Создаем директорию конфига

```bash
mkdir /opt/marzban/streamlit
```

Создаём файл конфига

```bash
echo "credentials:
  usernames:
    root: # ваш логин, замените root на ваш ник
      name: root # отображаемое имя пользователя
      password: '123' # замените нахеш пароля без кавычек
cookie:
  expiry_days: 30 # сколько дней действует куки файл
  key: 'random_key_value' # должен быть строковым значением или замените его на 120 символов латинского алфавита нижнего регистра
  name: random_cookie_name # должен быть строковым значением" > /opt/marzban/streamlit/config.yaml
```


### Шаг 3: Получение контейнера

Инициализируйте получение обновление контейнеров.

```bash
marzban update
```

### Шаг 4: Применение пароля

Для получения хеша пароля выполните команду 

```bash
docker exec -it marzban-analytics-1 python passwordhash.py
```

в консоли вы получите следующую инфу 
![image](https://github.com/lifeindarkside/marzban_sqlite_streamlit/assets/66727826/767371a6-9de9-49a5-abce-573183036a6f)

Полученный в консоли хеш, надо скопировать (без [ и ]) и поместить в файле `config.yaml`

```bash
nano /opt/marzban/streamlit/config.yaml
```

В файле необходимо заменить логин и хеш пароля

Например:

```
credentials:
  usernames:
    root: # ваш логин
      name: root # отображаемое имя
      password: abc # замените нахеш пароля без кавычек
cookie:
  expiry_days: 30 # сколько дней действует куки файл
  key: 'random_key_value' # должен быть строковым значением
  name: random_cookie_name # должен быть строковым значением
```
В строке key и name может быть любое текстовое значение без пробелов (это будут созранены ваши cookie файлы)

`root:` вы можете заменить на любой ваш логин в дашборд. Например: `new_login:`

Сохраните файл после редактирования и обновите данные в контейнере

```bash
marzban restart
```

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





