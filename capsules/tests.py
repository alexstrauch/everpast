from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta
from .models import TimeCapsule, CapsuleContent
from .forms import TimeCapsuleForm, CapsuleContentForm

User = get_user_model()

class TimeCapsuleModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.capsule = TimeCapsule.objects.create(
            creator=self.user,
            title='Test Capsule',
            description='Test Description',
            unlock_date=timezone.now() + timedelta(days=7),
            status='active'
        )

    def test_capsule_creation(self):
        """Test that a time capsule can be created with valid data"""
        self.assertEqual(self.capsule.title, 'Test Capsule')
        self.assertEqual(self.capsule.description, 'Test Description')
        self.assertEqual(self.capsule.creator, self.user)
        self.assertEqual(self.capsule.status, 'active')

    def test_capsule_str_representation(self):
        """Test the string representation of a time capsule"""
        self.assertEqual(str(self.capsule), 'Test Capsule')

    def test_capsule_is_unlockable(self):
        """Test that a capsule is unlockable when unlock date has passed"""
        # Set unlock date to yesterday
        self.capsule.unlock_date = timezone.now() - timedelta(days=1)
        self.capsule.save()
        self.assertTrue(self.capsule.is_unlockable())

        # Set unlock date to tomorrow
        self.capsule.unlock_date = timezone.now() + timedelta(days=1)
        self.capsule.save()
        self.assertFalse(self.capsule.is_unlockable())

    def test_check_and_unlock(self):
        """Test the check_and_unlock method"""
        # Set unlock date to yesterday
        self.capsule.unlock_date = timezone.now() - timedelta(days=1)
        self.capsule.status = 'locked'
        self.capsule.save()
        
        # Should unlock
        self.capsule.check_and_unlock()
        self.assertEqual(self.capsule.status, 'unlocked')

        # Should not unlock if already unlocked
        self.capsule.check_and_unlock()
        self.assertEqual(self.capsule.status, 'unlocked')

class TimeCapsuleFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.valid_data = {
            'title': 'Test Capsule',
            'description': 'Test Description',
            'unlock_date': timezone.now() + timedelta(days=7),
        }

    def test_valid_form(self):
        """Test form with valid data"""
        form = TimeCapsuleForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_invalid_unlock_date(self):
        """Test form with past unlock date"""
        data = self.valid_data.copy()
        data['unlock_date'] = timezone.now() - timedelta(days=1)
        form = TimeCapsuleForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('unlock_date', form.errors)

class CapsuleViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.capsule = TimeCapsule.objects.create(
            creator=self.user,
            title='Test Capsule',
            description='Test Description',
            unlock_date=timezone.now() + timedelta(days=7),
            status='active'
        )
        self.client.login(username='testuser', password='testpass123')
        self.test_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'test_image_content',
            content_type='image/jpeg'
        )

    def test_capsule_list_view(self):
        """Test the capsule list view"""
        response = self.client.get(reverse('capsule_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'capsules/capsule_list.html')
        self.assertContains(response, 'Test Capsule')

    def test_capsule_detail_view(self):
        """Test the capsule detail view"""
        response = self.client.get(
            reverse('capsule_detail', kwargs={'pk': self.capsule.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'capsules/capsule_detail.html')
        self.assertContains(response, 'Test Capsule')

    def test_capsule_create_view(self):
        """Test the capsule create view"""
        response = self.client.post(
            reverse('capsule_create'),
            {
                'title': 'New Capsule',
                'description': 'New Description',
                'unlock_date': timezone.now() + timedelta(days=7),
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(
            TimeCapsule.objects.filter(title='New Capsule').exists()
        )

    def test_unauthorized_access(self):
        """Test unauthorized access to capsule detail"""
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        # Create a locked capsule for the other user
        other_capsule = TimeCapsule.objects.create(
            creator=other_user,
            title='Other Capsule',
            description='Other Description',
            unlock_date=timezone.now() + timedelta(days=7),
            status='locked'
        )
        
        # Try to access the locked capsule
        response = self.client.get(
            reverse('capsule_detail', kwargs={'pk': other_capsule.pk})
        )
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_content_add_view(self):
        """Test adding content to a capsule"""
        response = self.client.post(
            reverse('capsules:content_add', kwargs={'pk': self.capsule.pk}),
            {
                'title': 'New Content',
                'description': 'New Content Description',
                'file': self.test_image
            }
        )
        self.assertEqual(response.status_code, 302)  # Redirect after success
