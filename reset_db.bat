@echo off
echo [StudyStream] Running migrations and starting server...
python manage.py migrate
python manage.py runserver
pause
