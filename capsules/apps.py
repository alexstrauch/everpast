"""Django app configuration for the capsules application.

This module contains the configuration class for the capsules app,
defining its basic settings and behavior within the Django project.
"""

from django.apps import AppConfig


class CapsulesConfig(AppConfig):
    """Configuration class for the capsules application.
    
    Attributes:
        default_auto_field: The default primary key type for models
        name: The name of the application
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'capsules'
