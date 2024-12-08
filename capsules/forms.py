from django import forms
from django.utils import timezone
from .models import TimeCapsule, CapsuleContent
from allauth.account.forms import LoginForm

class TimeCapsuleForm(forms.ModelForm):
    """
    Form for creating and editing time capsules.
    
    This form handles:
    - Basic capsule information (title, description)
    - Unlock date validation (must be in the future)
    - Bootstrap styling for form fields
    """
    
    class Meta:
        model = TimeCapsule
        fields = ['title', 'description', 'unlock_date']
        widgets = {
            'unlock_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'},
                format='%Y-%m-%dT%H:%M'
            ),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        """
        Initialize the form with custom field requirements.
        
        Makes description field required, unlike the model where it's optional.
        """
        super().__init__(*args, **kwargs)
        self.fields['description'].required = True

    def clean_unlock_date(self):
        """
        Validate that the unlock date is in the future.
        
        Returns:
            datetime: The validated unlock date
            
        Raises:
            ValidationError: If the unlock date is not in the future
        """
        unlock_date = self.cleaned_data.get('unlock_date')
        if unlock_date <= timezone.now():
            raise forms.ValidationError("Unlock date must be in the future.")
        return unlock_date

class CapsuleContentForm(forms.ModelForm):
    """
    Form for adding and editing content within a time capsule.
    
    This form handles:
    - Content metadata (title, description)
    - File uploads with size validation
    - File type validation
    - Optional file field when editing existing content
    - Bootstrap styling for form fields
    """
    
    content_type = forms.ChoiceField(
        choices=CapsuleContent.CONTENT_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = CapsuleContent
        fields = ['title', 'description', 'content_type', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        """Initialize the form with custom field requirements."""
        super().__init__(*args, **kwargs)
        self.fields['description'].required = True
        if self.instance and self.instance.pk:
            self.fields['file'].required = False

    def clean(self):
        """Validate the form data."""
        cleaned_data = super().clean()
        file = cleaned_data.get('file')
        content_type = cleaned_data.get('content_type')

        if file and not isinstance(file, str):
            # Check file size
            if file.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("File size must be under 5MB.")

            # Check file type matches content_type
            if content_type == 'image' and not file.content_type.startswith('image/'):
                raise forms.ValidationError("File must be an image for image content type.")
            elif content_type == 'video' and not file.content_type.startswith('video/'):
                raise forms.ValidationError("File must be a video for video content type.")
            elif content_type == 'document' and not any(
                file.content_type.startswith(t) for t in ['application/', 'text/']
            ):
                raise forms.ValidationError("File must be a document for document content type.")

        return cleaned_data

class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to existing fields
        self.fields['login'].widget.attrs['class'] = 'form-control'
        self.fields['password'].widget.attrs['class'] = 'form-control'
        # Add remember me field
        self.fields['remember'] = forms.BooleanField(
            required=False,
            label="Remember me",
            widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
        )
