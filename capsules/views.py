from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseForbidden, FileResponse
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from .models import TimeCapsule, CapsuleContent
from .forms import TimeCapsuleForm, CapsuleContentForm
import cloudinary
from cloudinary.uploader import upload

def home(request):
    """
    Display the home page.
    
    Args:
        request: The HTTP request
        
    Returns:
        HttpResponse: Rendered home page template
    """
    return render(request, 'capsules/home.html')

@login_required
def capsule_list(request):
    """
    Display a list of user's time capsules and handle automatic unlocking.
    
    This view:
    1. Retrieves all capsules for the current user
    2. Checks each capsule to see if it should be unlocked
    3. Notifies the user if any capsules were unlocked
    
    Args:
        request: The HTTP request
        
    Returns:
        HttpResponse: Rendered template with list of capsules
    """
    print("\n=== Checking Capsules for Unlocking ===")
    capsules = TimeCapsule.objects.filter(creator=request.user).order_by('-created_at')
    print(f"Found {capsules.count()} capsules")
    
    # Check each locked capsule if it should be unlocked
    unlocked_any = False
    for capsule in capsules:
        print(f"\nProcessing capsule: {capsule.title}")
        print(f"Current status: {capsule.status}")
        if capsule.check_and_unlock():
            print("Capsule was unlocked!")
            unlocked_any = True
        else:
            print("Capsule remains in current status")
    
    if unlocked_any:
        messages.success(request, 'One or more of your time capsules have been unlocked!')
        # Refresh the queryset to get updated status
        capsules = TimeCapsule.objects.filter(creator=request.user).order_by('-created_at')
    
    return render(request, 'capsules/capsule_list.html', {'capsules': capsules})

@login_required
def capsule_create(request):
    """
    Handle creation of new time capsules.
    
    This view:
    1. Displays the capsule creation form
    2. Validates form input
    3. Sets the creator to the current user
    4. Creates the capsule with initial 'active' status
    
    Args:
        request: The HTTP request
        
    Returns:
        HttpResponse: Redirects to capsule detail on success, or shows form with errors
    """
    if request.method == 'POST':
        form = TimeCapsuleForm(request.POST)
        if form.is_valid():
            capsule = form.save(commit=False)
            capsule.creator = request.user
            capsule.status = 'active'
            capsule.save()
            messages.success(request, 'Time capsule created successfully!')
            return redirect('capsules:capsule_detail', pk=capsule.pk)
    else:
        form = TimeCapsuleForm()
    
    return render(request, 'capsules/capsule_form.html', {
        'form': form,
        'title': 'Create time capsule'
    })

@login_required
def capsule_detail(request, pk):
    """
    Display details of a specific time capsule.
    
    This view:
    1. Retrieves the capsule and verifies user permission
    2. Updates capsule status if unlock date has passed
    3. Shows or hides content based on capsule status
    
    Args:
        request: The HTTP request
        pk: Primary key of the capsule to display
        
    Returns:
        HttpResponse: Rendered template with capsule details
        
    Raises:
        Http404: If capsule doesn't exist
        PermissionDenied: If user doesn't have access
    """
    capsule = get_object_or_404(TimeCapsule, pk=pk)
    print(f"\n=== Viewing Capsule: {capsule.title} ===")
    print(f"Current status: {capsule.status}")
    print(f"Unlock date: {capsule.unlock_date}")
    
    # Check if user has permission to view this capsule
    if capsule.creator != request.user and not capsule.is_public:
        return HttpResponseForbidden("You don't have permission to view this capsule.")
    
    # Check if capsule should be unlocked
    if capsule.check_and_unlock():
        messages.success(request, 'Your time capsule has been unlocked!')
    
    return render(request, 'capsules/capsule_detail.html', {'capsule': capsule})

@login_required
def capsule_edit(request, pk):
    """
    Handle editing of an existing time capsule.
    
    This view:
    1. Verifies user permission and capsule status
    2. Allows editing only if capsule is active or unlocked
    3. Updates capsule information
    
    Args:
        request: The HTTP request
        pk: Primary key of the capsule to edit
        
    Returns:
        HttpResponse: Redirects to capsule detail on success, or shows form with errors
        
    Raises:
        Http404: If capsule doesn't exist
        PermissionDenied: If user doesn't have permission
    """
    capsule = get_object_or_404(TimeCapsule, pk=pk)
    
    if capsule.creator != request.user:
        return HttpResponseForbidden("You don't have permission to edit this capsule.")
    
    if capsule.status == 'locked':
        messages.error(request, "You can't edit a locked capsule.")
        return redirect('capsules:capsule_detail', pk=capsule.pk)
    
    if request.method == 'POST':
        form = TimeCapsuleForm(request.POST, instance=capsule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Time capsule updated successfully!')
            return redirect('capsules:capsule_detail', pk=capsule.pk)
    else:
        form = TimeCapsuleForm(instance=capsule)
    
    return render(request, 'capsules/capsule_form.html', {
        'form': form,
        'title': 'Edit Time Capsule'
    })

@login_required
def capsule_delete(request, pk):
    """
    Handle deletion of a time capsule.
    
    This view:
    1. Verifies user permission
    2. Deletes the capsule and all its contents
    3. Redirects to capsule list
    
    Args:
        request: The HTTP request
        pk: Primary key of the capsule to delete
        
    Returns:
        HttpResponse: Redirects to capsule list on success
        
    Raises:
        Http404: If capsule doesn't exist
        PermissionDenied: If user doesn't have permission
    """
    capsule = get_object_or_404(TimeCapsule, pk=pk)
    
    if capsule.creator != request.user:
        return HttpResponseForbidden("You don't have permission to delete this capsule.")
    
    if request.method == 'POST':
        capsule.delete()
        messages.success(request, 'Time capsule deleted successfully!')
        return redirect('capsules:capsule_list')
    
    # If not POST, redirect back to list view
    return redirect('capsules:capsule_list')

@login_required
def capsule_lock(request, pk):
    """
    Handle locking of a time capsule.
    
    This view:
    1. Verifies user permission
    2. Changes capsule status to 'locked'
    3. Prevents further modifications until unlock date
    
    Args:
        request: The HTTP request
        pk: Primary key of the capsule to lock
        
    Returns:
        HttpResponse: Redirects to capsule detail
        
    Raises:
        Http404: If capsule doesn't exist
        PermissionDenied: If user doesn't have permission
    """
    capsule = get_object_or_404(TimeCapsule, pk=pk)
    
    if capsule.creator != request.user:
        return HttpResponseForbidden("You don't have permission to lock this capsule.")
    
    if capsule.status == 'locked':
        messages.error(request, "This capsule is already locked.")
        return redirect('capsules:capsule_detail', pk=capsule.pk)
    
    capsule.status = 'locked'
    capsule.save()
    messages.success(request, 'Time capsule locked successfully!')
    return redirect('capsules:capsule_detail', pk=capsule.pk)

@login_required
def content_add(request, pk):
    """
    Handle adding new content to a time capsule.
    
    This view:
    1. Verifies user permission and capsule status
    2. Handles file upload and metadata
    3. Associates content with capsule
    
    Args:
        request: The HTTP request
        pk: Primary key of the capsule to add content to
        
    Returns:
        HttpResponse: Redirects to capsule detail on success, or shows form with errors
        
    Raises:
        Http404: If capsule doesn't exist
        PermissionDenied: If user doesn't have permission
    """
    capsule = get_object_or_404(TimeCapsule, pk=pk)
    
    if capsule.creator != request.user:
        return HttpResponseForbidden("You don't have permission to add content to this capsule.")
    
    if capsule.status == 'locked':
        messages.error(request, "You can't add content to a locked capsule.")
        return redirect('capsules:capsule_detail', pk=pk)
    
    if request.method == 'POST':
        form = CapsuleContentForm(request.POST, request.FILES)
        if form.is_valid():
            content = form.save(commit=False)
            content.capsule = capsule
            
            # Automatically detect content type from file
            if 'file' in request.FILES:
                file = request.FILES['file']
                
                # Check file mime type
                if file.content_type.startswith('image/'):
                    content_type = 'image'
                elif file.content_type.startswith('video/'):
                    content_type = 'video'
                elif file.content_type.startswith('application/') or file.content_type.startswith('text/'):
                    content_type = 'document'
                    # Set raw resource type for documents
                    content.file.options = {
                        'resource_type': 'raw'
                    }
                
                content.content_type = content_type
                content.save()
                messages.success(request, 'Content added successfully!')
                return redirect('capsules:capsule_detail', pk=pk)
            else:
                messages.error(request, 'No file was uploaded.')
        else:
            print("Form errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Error in {field}: {error}')
    else:
        form = CapsuleContentForm()
    
    return render(request, 'capsules/content_form.html', {
        'form': form,
        'capsule': capsule,
        'title': 'Add Content'
    })

@login_required
def content_edit(request, pk):
    """
    Handle editing of existing capsule content.
    
    This view:
    1. Verifies user permission and capsule status
    2. Allows updating content metadata and file
    3. Preserves existing file if no new file uploaded
    
    Args:
        request: The HTTP request
        pk: Primary key of the content to edit
        
    Returns:
        HttpResponse: Redirects to capsule detail on success, or shows form with errors
        
    Raises:
        Http404: If content doesn't exist
        PermissionDenied: If user doesn't have permission
    """
    content = get_object_or_404(CapsuleContent, pk=pk)
    
    if content.capsule.creator != request.user:
        return HttpResponseForbidden("You don't have permission to edit this content.")
    
    if content.capsule.status == 'locked':
        messages.error(request, "You can't edit content in a locked capsule.")
        return redirect('capsules:capsule_detail', pk=content.capsule.pk)
    
    if request.method == 'POST':
        form = CapsuleContentForm(request.POST, request.FILES, instance=content)
        if form.is_valid():
            try:
                # Detect content type from file if a new file is uploaded
                if 'file' in request.FILES:
                    file = request.FILES['file']
                    if file.content_type.startswith('image/'):
                        form.instance.content_type = 'image'
                    elif file.content_type.startswith('video/'):
                        form.instance.content_type = 'video'
                    elif file.content_type.startswith('application/') or file.content_type.startswith('text/'):
                        form.instance.content_type = 'document'
                        # Set raw resource type for documents
                        form.instance.file.options = {
                            'resource_type': 'raw'
                        }
                
                form.save()
                messages.success(request, 'Content updated successfully!')
                return redirect('capsules:capsule_detail', pk=content.capsule.pk)
            except Exception as e:
                messages.error(request, f'Error updating content: {str(e)}')
    else:
        form = CapsuleContentForm(instance=content)
    
    return render(request, 'capsules/content_form.html', {
        'form': form,
        'capsule': content.capsule,
        'content': content,
        'title': 'Edit Content'
    })

@login_required
def content_delete(request, pk):
    """
    Handle deletion of capsule content.
    
    This view:
    1. Verifies user permission and capsule status
    2. Deletes content and associated file
    3. Redirects back to capsule detail
    
    Args:
        request: The HTTP request
        pk: Primary key of the content to delete
        
    Returns:
        HttpResponse: Redirects to capsule detail
        
    Raises:
        Http404: If content doesn't exist
        PermissionDenied: If user doesn't have permission
    """
    content = get_object_or_404(CapsuleContent, pk=pk)
    
    if content.capsule.creator != request.user:
        return HttpResponseForbidden("You don't have permission to delete this content.")
    
    if content.capsule.status == 'locked':
        messages.error(request, "You can't delete content from a locked capsule.")
        return redirect('capsules:capsule_detail', pk=content.capsule.pk)
    
    content.delete()
    messages.success(request, 'Content deleted successfully!')
    return redirect('capsules:capsule_detail', pk=content.capsule.pk)

@login_required
def serve_protected_file(request, content_id):
    """
    Serve uploaded files with proper access control.
    
    This view:
    1. Verifies user permission and capsule status
    2. Checks if content should be visible
    3. Serves file securely
    
    Args:
        request: The HTTP request
        content_id: ID of the content whose file should be served
        
    Returns:
        FileResponse: The requested file
        
    Raises:
        Http404: If content doesn't exist
        PermissionDenied: If user doesn't have permission
    """
    content = get_object_or_404(CapsuleContent, pk=content_id)
    capsule = content.capsule
    
    # Check if user has permission to access this content
    if capsule.creator != request.user and not capsule.is_public:
        raise PermissionDenied("You don't have permission to view this content.")
    
    # Check if capsule is locked
    if capsule.status == 'locked' and not capsule.is_unlockable():
        raise PermissionDenied("This content is locked until the capsule's unlock date.")
    
    try:
        # For Cloudinary files, redirect to the URL
        return redirect(content.file.url)
    except Exception as e:
        messages.error(request, f"Error serving file: {str(e)}")
        return redirect('capsules:capsule_detail', pk=capsule.pk)
