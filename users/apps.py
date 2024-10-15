from django.apps import AppConfig
from django.db.models.signals import post_migrate


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        import users.signals
        
        from django.contrib.auth.hashers import make_password

        from .models import User

        def create_initial_users(sender, **kwargs):
            if not User.objects.exists():
                User.objects.create(
                    username='admin',
                    password=make_password('123456'),
                    email='',
                    is_superuser=True,
                    is_staff=True,
                    is_active=True,
                    user_type=User.UserType.TSG
                )
                User.objects.create(
                    username='john.doe',
                    password=make_password('123456'),
                    first_name='John',
                    last_name='Doe',
                    email='jonathan_lin@dlsu.edu.ph',
                    is_staff=False,
                    is_active=True,
                    user_type=User.UserType.TSG
                )
                User.objects.create(
                    username='josephine.cruz',
                    password=make_password('123456'),
                    first_name='Josephine',
                    last_name='Cruz',
                    email='rafael_sanchez@dlsu.edu.ph',
                    is_staff=False,
                    is_active=True,
                    user_type=User.UserType.FACULTY
                )
        post_migrate.connect(create_initial_users)
