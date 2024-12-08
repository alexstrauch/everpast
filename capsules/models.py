from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from cloudinary.models import CloudinaryField


class TimeCapsule(models.Model):
    """
    Represents a digital time capsule that can store various types of content.
    
    A time capsule has three states:
    - Active: Content can be added and modified
    - Locked: Content is hidden and cannot be modified until unlock date
    - Unlocked: Content is visible and can be modified again
    
    The state transitions are:
    Active -> Locked (when manually locked or unlock date reached)
    Locked -> Unlocked (when unlock date is reached)
    Unlocked -> Locked (when manually locked again)
    """
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('locked', 'Locked'),
        ('unlocked', 'Unlocked')
    ]

    # Basic information
    title = models.CharField(max_length=200, help_text="The name of your time capsule")
    description = models.TextField(blank=True, help_text="A description of what this time capsule contains or represents")
    
    # Relationships and timestamps
    creator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='time_capsules',
        help_text="The user who created this time capsule"
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="When this capsule was created")
    unlock_date = models.DateTimeField(help_text="When this capsule should become accessible")
    
    # State management
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='active',
        help_text="Current state of the capsule (active, locked, or unlocked)"
    )
    is_public = models.BooleanField(
        default=False, 
        help_text="If checked, this capsule will be visible to everyone when unlocked"
    )
    
    def __str__(self):
        """String representation of the capsule."""
        return self.title

    def is_unlockable(self):
        """
        Check if the capsule can be unlocked based on the unlock date.
        
        Returns:
            bool: True if the current time is past the unlock date, False otherwise
        """
        now = timezone.localtime(timezone.now())
        unlock_date_local = timezone.localtime(self.unlock_date)
        print(f"\nChecking if capsule '{self.title}' is unlockable:")
        print(f"Current time (Berlin): {now}")
        print(f"Unlock date (Berlin): {unlock_date_local}")
        print(f"Current status: {self.status}")
        is_time_passed = now >= unlock_date_local
        print(f"Time has passed: {is_time_passed}")
        return is_time_passed

    def check_and_unlock(self):
        """
        Check if capsule should be unlocked and update its status accordingly.
        
        This method handles the state transitions:
        - Active -> Locked (if unlock date has passed)
        - Locked -> Unlocked (if unlock date has passed)
        
        Returns:
            bool: True if the capsule was unlocked, False otherwise
        """
        if self.status == 'active':
            # If it's active and past unlock date, lock it
            if timezone.localtime(timezone.now()) >= timezone.localtime(self.unlock_date):
                print(f"\nLocking active capsule '{self.title}'")
                self.status = 'locked'
                self.save()
                return False
        elif self.status == 'locked' and self.is_unlockable():
            print(f"\nUnlocking capsule '{self.title}'")
            self.status = 'unlocked'
            self.save()
            return True
        return False

    @property
    def is_locked(self):
        """
        Check if the capsule is locked and not yet unlockable.
        
        Returns:
            bool: True if the capsule is locked and cannot be unlocked yet
        """
        return self.status == 'locked' and not self.is_unlockable()

    def save(self, *args, **kwargs):
        """
        Override save method to handle initial status setting.
        
        When a capsule is first created, its status is set based on the unlock date:
        - If unlock date is in the past -> Unlocked
        - If unlock date is in the future -> Active
        """
        if not self.pk:  # When first creating a capsule
            if timezone.localtime(timezone.now()) >= timezone.localtime(self.unlock_date):
                self.status = 'unlocked'
            else:
                self.status = 'active'
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']


class CapsuleContent(models.Model):
    """
    Represents a piece of content stored within a time capsule.
    
    Content can be of different types (image, video, document) and includes
    metadata such as title and description. The visibility and editability
    of content is controlled by its parent capsule's status.
    """
    
    CONTENT_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('document', 'Document')
    ]
    
    # Relationship to capsule
    capsule = models.ForeignKey(
        TimeCapsule, 
        on_delete=models.CASCADE, 
        related_name='contents',
        help_text="The time capsule this content belongs to"
    )
    
    # Content metadata
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPES,
        help_text="Type of content (image, video, or document)"
    )
    file = CloudinaryField(
        'file',
        resource_type='auto',
        folder='capsule_contents',
        help_text="The actual file to be stored in the time capsule"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this content was added to the capsule"
    )
    title = models.CharField(
        max_length=200,
        help_text="Title of this piece of content"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of what this content represents"
    )

    def save(self, *args, **kwargs):
        """
        Override save method to add logging for debugging file uploads.
        
        Logs various file attributes to help track upload issues.
        """
        print("\n=== Saving CapsuleContent ===")
        print(f"Title: {self.title}")
        print(f"Content Type: {self.content_type}")
        print(f"File: {self.file}")
        print(f"File name: {self.file.name if self.file else 'No file'}")
        if hasattr(self.file, 'file') and self.file.file:
            print(f"File size: {self.file.size} bytes")
            if hasattr(self.file, 'content_type'):
                print(f"File content type: {self.file.content_type}")
        super().save(*args, **kwargs)
        print(f"Saved successfully with ID: {self.pk}")
        if self.file:
            print(f"File URL: {self.file.url}")

    def get_file_url(self):
        """Get the protected URL for the file"""
        return reverse('capsules:serve_protected_file', args=[self.pk])

    def __str__(self):
        """String representation of the content."""
        return self.title

    class Meta:
        ordering = ['uploaded_at']
