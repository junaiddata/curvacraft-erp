# users/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Custom User model to include user roles.
    """
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('sco', 'SCO'),
        ('staff', 'Staff'), # <-- ADD THIS LINE
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='sco')

    def __str__(self):
        return self.username