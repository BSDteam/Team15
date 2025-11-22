sample

Настройка

1. Создайте файл `.env` в корне проекта:
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=rus_al_shifts
   DB_USER=postgres
   DB_PASS=ваш_пароль

Как запустить проект?

python -m venv .venv
.\.venv\Scripts\activate
pip install -r .\requirements.txt
python main.py