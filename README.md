# Проект Foodgram


### Описание
Проект "Foodgram" – это "продуктовый помощник". Сдесь вы можете публиковать свои рецепты, а так же ознакомится с рецепптами других пользователей.
Присутствует возможность подписки на авторов, а так же добавление рецептов в избранное.
С помощью многофункционального окна создания рецепта вы сможете легко добавить свой собственный рецепт.

### Запуск проекта на сервере

Установите на сервере docker. Скопируйте на сервер файл docker-compose.production.yml, создайте файл .env 
Заполните в файле .env поля.
Переменные для .env находятся в файле .env.example

```
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
DB_HOST=
DB_PORT=

DEBUG=True

SECRET_KEY= 
IP= 
DOMAIN=
LOCAL_IP=


```

Выполнить команды:

```

*   sudo docker compose -f docker-compose.production.yml up -d
*   sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
*   sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
*   sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /static/


```

Создать суперпользователя:


```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser

```

Данные суперпользователя для проверки проекта
Сервер доступен по адресу https://foodgramio.zapto.org/

```

login: testadmin
password: testadmin

```




### Автор проекта

[**github.com/PepegaBoss**](https://github.com/PepegaBoss)
