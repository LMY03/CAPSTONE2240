from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

# Create your models here.

class User(AbstractUser):

    class UserType(models.TextChoices):
        STUDENT = 'STUDENT'
        FACULTY = 'FACULTY'
        TSG = 'TSG'

    user_type = models.CharField(
        max_length=20, 
        choices=UserType.choices, 
        default=UserType.STUDENT,
    )

    def is_student(self): return self.user_type == User.UserType.STUDENT
    def is_faculty(self): return self.user_type == User.UserType.FACULTY
    def is_tsg(self): return self.user_type == User.UserType.TSG

    def set_password(self, raw_password):
        # First validate the raw password using Django's validators
        try:
            validate_password(raw_password, self)  # Pass the raw password for validation
        except ValidationError as e:
            raise e  # Raise the validation errors if password does not meet criteria

        # Save the password as plain text
        self.password = raw_password

    # Override check_password to compare plain-text passwords
    def check_password(self, raw_password):
        return self.password == raw_password  # Compare plain-text
    
    def create_student_user(username, password):
        user = User(username=username)
        user.set_password(password)
        user.save()

        return user

# class UserProfile (models.Model):
#     USER_TYPE_CHOICES = [
#         ('student', 'Student'),
#         ('faculty', 'Faculty'),
#         ('admin', 'Admin'),
#     ]

#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     user_type = models.CharField(max_length= 20, choices=USER_TYPE_CHOICES, default='student')
#     system_password = models.CharField(max_length=45)
#     #request_use_case = models.ForeignKey(RequestUseCase, on_delete= models.CASCADE, null = True)

#     def is_faculty(self): return self.user_type == 'faculty'

#     def __str__(self) -> str:
#         return f"{self.user.username} - Role: {self.user_type}"