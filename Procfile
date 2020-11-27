release: cd website && python manage.py migrate && python manage.py set_group_permissions
web: cd website && gunicorn website.wsgi --log-file -
