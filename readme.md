# Модуль 2_13, завдання 1

Для роботи потрібен файл `task1/.env` зі змінними оточення.

```dotenv
POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_PORT=

SQLALCHEMY_DATABASE_URL=

SECRET_KEY=
ALGORITHM=

MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=
MAIL_PORT=
MAIL_SERVER=

REDIS_HOST=localhost
REDIS_PORT=6379

CLOUDINARY_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```
Команди
```dotenv
docker-compose up -d
docker-compose down

pytest --cov=. --cov-report html tests/
```
