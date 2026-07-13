# Sirius.Arena — уникальная версия (FastAPI + Postgres + JWT)

Проект: backend для бронирования пространств. Версия с JWT, ролями, поиском доступных пространств, тестами и Docker Compose.

Запуск (локально с Docker):
1) docker-compose up --build
2) Открыть http://localhost:8000/docs

Default admin: username=admin, password=adminpass (создаётся при старте)
Регистрация: POST /users/signup?username=...&password=...
Получение токена: POST /token (form) username/password

Важно: SECRET_KEY сгенерирован автоматически в .env — поменяйте при необходимости.
