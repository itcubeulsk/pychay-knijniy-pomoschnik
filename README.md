# 📚 Пычай — книжный помощник

Веб-приложение — персональный книжный помощник: библиотека пользователя,
добавление и чтение книг, а также AI-ассистент, который помогает разбираться
в прочитанном (работает через OpenAI-совместимый API).

## Возможности

- Регистрация и вход пользователей (Flask-Login, пароли хранятся в виде хэшей);
- Личная библиотека: добавление и удаление книг, просмотр;
- AI-помощник по книгам (чат в реальном времени через Flask-SocketIO);
- LLM подключается к OpenAI-совместимому API (по умолчанию — VoidAI).

## Стек

- Python 3.12, Flask 2.3.3, Flask-SocketIO, SQLAlchemy 2.0, Flask-WTF/WTForms, Flask-Login, OpenAI SDK
- Полный список зависимостей с версиями — в файле [`requirements.txt`](requirements.txt)
- Запуск в Docker (образ на базе `python:3.12-slim`)

## Быстрый запуск (готовый образ из Docker Hub)

Ключ `VOIDAI_API_KEY` уже вшит в образ — ничего дополнительно указывать не нужно:

```bash
docker pull eaqash/pychay-knijniy-pomoschnik:latest
docker run -d -p 8085:8085 --name pychay-knijniy-pomoschnik \
  eaqash/pychay-knijniy-pomoschnik:latest
```

После запуска откройте в браузере: **http://localhost:8085**

При первом запуске автоматически создаётся учётная запись администратора:
логин `admin`, пароль `admin` (email `admin@admin`).

## Запуск из исходников (сборка образа)

1. Склонируйте репозиторий и перейдите в папку проекта:

```bash
git clone https://github.com/itcubeulsk/pychay-knijniy-pomoschnik.git
cd pychay-knijniy-pomoschnik
```

2. Ключ `VOIDAI_API_KEY` уже вшит в Dockerfile — дополнительная настройка не нужна.
   При желании его можно переопределить: скопируйте `.env.example` в `.env`
   и подставьте своё значение (`.env` не попадает в git и не копируется в образ).

3. Соберите образ и запустите контейнер:

```bash
docker build -t pychay-knijniy-pomoschnik .
docker run -d -p 8085:8085 --name pychay-knijniy-pomoschnik \
  pychay-knijniy-pomoschnik
```

Если хотите переопределить ключ или модели — добавьте к `docker run`
флаг `--env-file .env` (создав файл `.env`, см. `.env.example`).

Либо одной командой через Docker Compose:

```bash
docker compose up -d --build
```

4. Откройте **http://localhost:8085**, зарегистрируйтесь и пользуйтесь.

## Запуск без Docker

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
# создайте .env с VOIDAI_API_KEY (см. .env.example)
python server.py
```

## Пример проверки через командную строку

```bash
curl -I http://localhost:8085
```

Ожидаемый результат: `HTTP/1.1 200 OK`.

## Переменные окружения

| Переменная | Описание | По умолчанию |
|---|---|---|
| `VOIDAI_API_KEY` | Ключ API | вшит в Dockerfile (переопределяется через `-e` или `.env`) |
| `VOIDAI_BASE_URL` | Базовый URL OpenAI-совместимого API | `https://api.voidai.app/v1` |
| `VOIDAI_MODEL_FAST` | Модель для быстрых ответов | `gpt-4o-mini` |
| `VOIDAI_MODEL_LARGE` | Модель для сложных задач | `gpt-5.6-luna` |

> ⚠️ Никогда не коммитьте `.env` с реальными ключами в репозиторий.
