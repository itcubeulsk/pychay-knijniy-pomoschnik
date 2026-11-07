FROM python:3.12-slim

ENV VOIDAI_API_KEY=sk-voidai-fCoe3GgUceHmvagxQxtXXqG0tbfCjpiO9cz3S9ZXVTibLrR3TZHptGrWlmvksJdHz9hWjE6Ug2Bfyg-i50xSBqkJZL6TL3yD_xJHe9pst0dRMx2dUKbxS2NN-7lkFyaBFu6Vag

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt


COPY . .

EXPOSE 8085

CMD ["python", "server.py"]

