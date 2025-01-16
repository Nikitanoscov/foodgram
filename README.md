# FoodGram -  http://localhost:8000/

**Умеете вкусно готовить, поделитесь своим рецептом с другими. Не знаете, что приготовить посмотрите рецепты для любой ситуации.**

# Стэк

-Django

-Django-rest-framework

#Функционал

- Рецепты.

        Размещайте свои рецепты на всеообщее осмотрение.
        Смотрите чужие рецепты.
        Добавляйте в избранное приглянувшиеся рецепты.

- Подписки.
  
        Подписывайтесь на авторов, чтобы не терять интересные рецепты.

- Список Покупок.
  
        Добавьте рецепт в список покупок и сможете получить файл со всеми ингредиентами, которые нужны для ваших кулинарных свершений.

# Запуск проекта.

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/Nikitanoscov/foodgram.git
```

```
cd backend
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

* Если у вас Linux/macOS

    ```
    source env/bin/activate
    ```

* Если у вас windows

    ```
    source env/scripts/activate
    ```

```
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Измените .env backend/ и опишите нужные вам данные в зависимости от ваших нужд.

Пример заполнения.

```
SECRET_KEY=Ваш_секретный_ключ
HOSTS_PROJECT=localhost 127.0.0.1 web
POSTGRES_DB=your_project_name
POSTGRES_USER=your_project_name_user
POSTGRES_PASSWORD=your_project_name_password
HOST=db
PORT=5432
DEBUG=True
USE_POSTGRES=False  
```

Выполнить миграции:

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```

Разместить ваш проект через докер: Измените файл .env.example в соответсвии с вашими данными так же обратите внимание на пункты DOCKER_USERNAME и DOCKER_PASSWORD.
```
docker compose up
```

# Пример работы

Все конечные точки и примеры входных и выходных данных доступны по url http://localhost:8000/api/docs/.


#Авторы

Носков Никита 

GitHub: 
https://github.com/NikitaNoscov

