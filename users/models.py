from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

class User(AbstractUser):
    class UserType(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        FACULTY = 'FACULTY', 'Faculty'
        TSG = 'TSG', 'TSG'

    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.STUDENT,
    )

    def is_student(self): 
        return self.user_type == User.UserType.STUDENT

    def is_faculty(self): 
        return self.user_type == User.UserType.FACULTY

    def is_tsg(self): 
        return self.user_type == User.UserType.TSG

    @classmethod
    def create_student_user(cls, username, password):
        # Create the user instance
        user = cls(username=username)

        # Hash the password for the User model
        user.set_password(password)

        # Set the user type to STUDENT
        user.user_type = cls.UserType.STUDENT

        # Save the user
        user.save()

        # Store the plain-text password in the Student model
        Student.objects.create(user=user, password=password)

        return user


class StudentManager(models.Manager):
    def create_student(self, user, password):
        if user.user_type != User.UserType.STUDENT:
            raise ValidationError("The associated user must be of type STUDENT.")
        
        # Create the Student instance with the raw password
        student = self.model(user=user, password=password)
        student.save(using=self._db)
        return student

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    password = models.CharField(max_length=128)  # Store plain-text password

    objects = StudentManager()