FROM python:3.8-slim
WORKDIR /app
COPY requirements.txt requirements.txt
RUN python -m pip install --upgrade pip && \
    pip3 install -r requirements.txt --no-cache-dir
COPY . .
RUN python manage.py collectstatic --noinput
RUN mv /app/static /static
CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000"]