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

This dashboard is created to visualize statistics in the [Marzban](https://github.com/Gozargah/Marzban) project using the SQLite database built into the container.
Metrics are collected for nodes and users. Works only on the marzban:dev branch


![image](https://github.com/lifeindarkside/marzban_sqlite_streamlit/assets/66727826/2fd39235-9139-46a2-a734-2e200edf7861)
![image](https://github.com/lifeindarkside/marzban_sqlite_streamlit/assets/66727826/daaca12f-0e37-4542-a303-e44bb31c6b04)
![image](https://github.com/lifeindarkside/marzban_sqlite_streamlit/assets/66727826/6b54c4ce-f303-4bcb-8070-93ab9e8de191)

![image](https://github.com/lifeindarkside/marzban_mysql_streamlit/assets/66727826/8fcd7d19-1a5f-408d-8f83-7d5afc5da219)
![image](https://github.com/lifeindarkside/marzban_mysql_streamlit/assets/66727826/f55a79ec-2889-4897-8500-540a44c09b7b)


## Installation via docker

### Step 1: Edit `docker-compose.yml`

Connect our dashboard to run in a docker container. To do this, you need to edit the `docker-compose.yml` file in the `/opt/marzban/` folder 

```bash
nano /opt/marzban/docker-compose.yml
```
Add the following lines:
```
  analytics:
    image: lifeindarkside/marzban-analytics:latest
    environment: 
      - MY_SECRET_PASSWORD=YOURPASSWORD  
    ports:
      - 8501:8501
    depends_on:
      - marzban
    volumes:
      - /opt/marzban/streamlit/config.yaml:/app/config.yaml
      - /opt/marzban/streamlit/main_sqlite_en.py:/app/main_sqlite.py
      - /var/lib/marzban:/var/lib/marzban
```

ATTENTION! Replace `YOURPASSWORD` with any password of your choice. This is necessary to generate a password hash so that your dashboard does not shine on the entire Internet openly.

### Step 2: Get the container

Initialize getting container updates.

```bash
marzban update
```

### Step 3: Apply password

To get the password hash, run the command

```bash
docker exec -it marzban-analytics-1 python passwordhash.py
```

In the console you will receive the following information:
![image](https://github.com/lifeindarkside/marzban_sqlite_streamlit/assets/66727826/767371a6-9de9-49a5-abce-573183036a6f)

Copy the hash obtained in the console (without quotes) and place it in the `config.yaml` file

```bash
nano /opt/marzban/streamlit/config.yaml
```

In the file you need to replace the login and password hash

For example:

```
credentials:
  usernames:
    root: # your login  
      name: root # display name
      password: abc # replace with password hash without quotes
cookie:
  expiry_days: 30 # how many days the cookie is valid
  key: 'random_key_value' # must be string value  
  name: random_cookie_name # must be string value
```
In the key and name strings you can put any text value without spaces (this will save your cookie files)

`root:` you can replace with any login you want for the dashboard. For example: `new_login:`

Save the file after editing and copy file `main_sqlite_en.py` into `/opt/marzban/streamlit/` folder. 

Update the data in the container:
```bash
marzban restart
```

### Step 4:
You can access the dashboard at:
`http://ip:8501/`
where `ip` can be the IP address of your server or domain

If you need to change the port, edit the `docker-compose.yml` file. Change the `port` parameter in it.

For example:
```
    ports:
      - 9901:8501
```




## Building from source files

### Step 1: Download files

Download the files directly to the `/opt/marzban/` folder

```bash
cd /opt/marzban/
git clone https://github.com/lifeindarkside/marzban_sqlite_streamlit.git
```

### Step 2: Add container

Connect our dashboard to run in a docker container. To do this, you need to edit the `docker-compose.yml` file in the `/opt/marzban/` folder

```bash
nano /opt/marzban/docker-compose.yml
```

Add the following lines:
```
  analytics:
    image: lifeindarkside/marzban-analytics:latest
    environment: 
      - MY_SECRET_PASSWORD=YOURPASSWORD  
    ports:
      - 8501:8501
    depends_on:
      - marzban
    volumes:
      - /opt/marzban/streamlit/config.yaml:/app/config.yaml
      - /opt/marzban/streamlit/main_sqlite_en.py:/app/main_sqlite.py
      - /var/lib/marzban:/var/lib/marzban
```

ATTENTION! Replace `YOURPASSWORD` with any password of your choice. This is necessary to generate a password hash so that your dashboard does not shine on the entire Internet openly.

The final file should look something like this:
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
      - /opt/marzban/streamlit/main_sqlite_en.py:/app/main_sqlite.py
      - /var/lib/marzban:/var/lib/marzban
```

### Step 3: Run

To run you need to update and then restart:

```bash
marzban update
```

```bash
marzban restart
```

As a result, the panel will start, but access to it will not be possible. Since we did not change the password hash.

### Step 4: Change password

To get the password hash, run the command:

```bash
docker exec -it marzban-analytics-1 python passwordhash.py
```

In the console you will receive the following information:
![image](https://github.com/lifeindarkside/marzban_sqlite_streamlit/assets/66727826/767371a6-9de9-49a5-abce-573183036a6f)

Copy the hash received in the console and place it in the `config.yaml` file:

```bash
nano /opt/marzban/marzban_sqlite_streamlit/config.yaml
```

In the file you need to replace the login and password hash:

For example:

```
credentials:
  usernames:
    root: #your login
      name: root #display name 
      password: abc # To be replaced with hashed password
cookie:
  expiry_days: 30
  key: 'abc' # Must be string
  name: random_cookie_name # Must be string
```
In the key and name strings you can put any text value without spaces (this will save your cookie files)

Save the file after editing


### Step 5:
You can access the dashboard at:
`http://ip:8501/`
where `ip` can be the IP address of your server or domain

If you need to change the port, edit the `docker-compose.yml` file. Change the `port` parameter in it.

For example:
```
    ports:
      - 9901:8501
```




## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=lifeindarkside/marzban_sqlite_streamlit&type=Date)](https://star-history.com/#lifeindarkside/marzban_sqlite_streamlit&Date)


