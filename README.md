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

```bash
docker pull eaqash/pychay-knijniy-pomoschnik:latest
docker run -d -p 8085:8085 --name pychay-knijniy-pomoschnik \
  -e VOIDAI_API_KEY=sk-ваш-ключ \
  eaqash/pychay-knijniy-pomoschnik:latest
```

После запуска откройте в браузере: **http://localhost:8085**

## Запуск из исходников (сборка образа)

1. Склонируйте репозиторий и перейдите в папку проекта:

```bash
git clone https://github.com/itcubeulsk/pychay-knijniy-pomoschnik.git
cd pychay-knijniy-pomoschnik
```

2. Создайте файл `.env` с ключом API (можно скопировать из примера):

```bash
cp .env.example .env
# откройте .env и подставьте свой ключ: VOIDAI_API_KEY=sk-...
```

3. Соберите образ и запустите контейнер:

```bash
docker build -t pychay-knijniy-pomoschnik .
docker run -d -p 8085:8085 --name pychay-knijniy-pomoschnik \
  --env-file .env pychay-knijniy-pomoschnik
```

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
| `VOIDAI_API_KEY` | Ключ API (обязательно) | — |
| `VOIDAI_BASE_URL` | Базовый URL OpenAI-совместимого API | `https://api.voidai.app/v1` |
| `VOIDAI_MODEL_FAST` | Модель для быстрых ответов | `gpt-4o-mini` |
| `VOIDAI_MODEL_LARGE` | Модель для сложных задач | `gpt-5.6-luna` |

> ⚠️ Никогда не коммитьте `.env` с реальными ключами в репозиторий.
