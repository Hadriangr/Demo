"""
Copy the content of this file into your PythonAnywhere WSGI configuration file.
Update YOUR_USERNAME and project path before using.
"""

import os
import sys

# 1) Update this path to your project directory in PythonAnywhere.
project_home = '/home/YOUR_USERNAME/Demo'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# 2) Set Django settings module.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'warehouse_audit_demo.settings')

# 3) Optional but recommended env vars for production.
os.environ.setdefault('DJANGO_DEBUG', 'False')
os.environ.setdefault('DJANGO_ALLOWED_HOSTS', 'YOUR_USERNAME.pythonanywhere.com')
os.environ.setdefault('DJANGO_CSRF_TRUSTED_ORIGINS', 'https://YOUR_USERNAME.pythonanywhere.com')
os.environ.setdefault('DJANGO_SECRET_KEY', 'CHANGE-THIS-TO-A-REAL-SECRET')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
