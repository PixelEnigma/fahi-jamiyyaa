#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput

# Seed default admin user if it doesn't exist
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from members.models import Member
if not Member.objects.filter(username='admin').exists():
    admin = Member.objects.create_superuser('admin', 'admin@fahi-jamiyyaa.com', 'admin123')
    admin.role = 'admin'
    admin.save()
    print('Created admin user')
else:
    print('Admin user exists')
"
