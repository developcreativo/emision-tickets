from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import UserSerializer
from catalog.models import Zone, DrawType


class UserModelTests(TestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'role': 'SELLER'
        }

    def test_create_user(self):
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.role, 'SELLER')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)
        # El role por defecto es SELLER, no ADMIN
        self.assertEqual(admin_user.role, 'SELLER')

    def test_user_str_representation(self):
        user = User.objects.create_user(**self.user_data)
        # El __str__ incluye el role
        self.assertEqual(str(user), 'testuser (SELLER)')

    def test_user_role_choices(self):
        user = User.objects.create_user(**self.user_data)
        # Usar Roles.choices en lugar de ROLE_CHOICES
        self.assertIn(user.role, dict(User.Roles.choices))

    def test_user_permissions(self):
        # Test ADMIN permissions - crear superuser
        admin_user = User.objects.create_superuser(
            username='admin',
            password='admin123'
        )
        # Los superusers tienen permisos por defecto
        self.assertTrue(admin_user.has_perm('accounts.add_user'))
        self.assertTrue(admin_user.has_perm('accounts.change_user'))

        # Test VENDEDOR permissions
        seller_user = User.objects.create_user(
            username='seller',
            password='seller123',
            role='SELLER'
        )
        # Los usuarios normales no tienen permisos especiales
        self.assertFalse(seller_user.has_perm('accounts.add_user'))
        self.assertFalse(seller_user.has_perm('accounts.change_user'))


class UserSerializerTests(TestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'role': 'SELLER'
        }
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role='SELLER'
        )

    def test_user_serializer_validation(self):
        serializer = UserSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid())

    def test_user_serializer_serialization(self):
        serializer = UserSerializer(self.user)
        data = serializer.data
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['role'], 'SELLER')
        self.assertNotIn('password', data)  # Password should not be exposed

    def test_user_serializer_update(self):
        update_data = {'email': 'updated@example.com', 'role': 'SUPERVISOR'}
        serializer = UserSerializer(self.user, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()
        self.assertEqual(updated_user.email, 'updated@example.com')
        self.assertEqual(updated_user.role, 'SUPERVISOR')


class UserViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create users with different roles
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        self.seller_user = User.objects.create_user(
            username='seller',
            password='seller123',
            role='SELLER'
        )
        self.supervisor_user = User.objects.create_user(
            username='supervisor',
            password='supervisor123',
            role='SUPERVISOR'
        )

        # Create test user for CRUD operations
        self.test_user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='VENDEDOR'
        )

    def get_auth_headers(self, user):
        token = RefreshToken.for_user(user).access_token
        return {'HTTP_AUTHORIZATION': f'Bearer {str(token)}'}

    def test_list_users_admin_access(self):
        """Admin should be able to list all users"""
        self.client.credentials(**self.get_auth_headers(self.admin_user))
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)  # Including admin, seller, supervisor, testuser

    def test_list_users_seller_denied(self):
        """Seller should not be able to list users"""
        self.client.credentials(**self.get_auth_headers(self.seller_user))
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_user_admin_only(self):
        """Only admin should be able to create users"""
        new_user_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'role': 'VENDEDOR'
        }
        
        # Admin can create
        self.client.credentials(**self.get_auth_headers(self.admin_user))
        response = self.client.post(reverse('user-list'), new_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Seller cannot create
        self.client.credentials(**self.get_auth_headers(self.seller_user))
        response = self.client.post(reverse('user-list'), new_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_user(self):
        """Admin should be able to retrieve any user"""
        self.client.credentials(**self.get_auth_headers(self.admin_user))
        response = self.client.get(reverse('user-detail', args=[self.test_user.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')

    def test_update_user(self):
        """Admin should be able to update users"""
        self.client.credentials(**self.get_auth_headers(self.admin_user))
        update_data = {'email': 'updated@example.com', 'role': 'SUPERVISOR'}
        response = self.client.patch(
            reverse('user-detail', args=[self.test_user.id]),
            update_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.test_user.refresh_from_db()
        self.assertEqual(self.test_user.email, 'updated@example.com')
        self.assertEqual(self.test_user.role, 'SUPERVISOR')

    def test_delete_user(self):
        """Admin should be able to delete users"""
        self.client.credentials(**self.get_auth_headers(self.admin_user))
        response = self.client.delete(reverse('user-detail', args=[self.test_user.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.test_user.id).exists())

    def test_me_endpoint(self):
        """Users should be able to get their own information"""
        self.client.credentials(**self.get_auth_headers(self.seller_user))
        response = self.client.get(reverse('me'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'seller')
        self.assertEqual(response.data['role'], 'SELLER')

    def test_me_endpoint_unauthenticated(self):
        """Unauthenticated users should be denied access to me endpoint"""
        response = self.client.get(reverse('me'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='VENDEDOR'
        )

    def test_token_obtain(self):
        """Test JWT token obtain endpoint"""
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_token_obtain_invalid_credentials(self):
        """Test JWT token obtain with invalid credentials"""
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        """Test JWT token refresh endpoint"""
        # First obtain tokens
        token_response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        refresh_token = token_response.data['refresh']
        
        # Then refresh
        response = self.client.post(reverse('token_refresh'), {
            'refresh': refresh_token
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_protected_endpoint_with_token(self):
        """Test accessing protected endpoint with valid token"""
        token_response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        access_token = token_response.data['access']
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(reverse('me'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token"""
        response = self.client.get(reverse('me'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_protected_endpoint_with_invalid_token(self):
        """Test accessing protected endpoint with invalid token"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        response = self.client.get(reverse('me'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserPermissionsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create users with different roles
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        self.seller_user = User.objects.create_user(
            username='seller',
            password='seller123',
            role='SELLER'
        )
        self.supervisor_user = User.objects.create_user(
            username='supervisor',
            password='supervisor123',
            role='SUPERVISOR'
        )

        # Create test data
        self.zone = Zone.objects.create(name='Test Zone')
        self.draw_type = DrawType.objects.create(code='TEST', name='Test Draw')

    def get_auth_headers(self, user):
        token = RefreshToken.for_user(user).access_token
        return {'HTTP_AUTHORIZATION': f'Bearer {str(token)}'}

    def test_role_based_permissions(self):
        """Test that different roles have appropriate permissions"""
        
        # Admin should have full access
        self.client.credentials(**self.get_auth_headers(self.admin_user))
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Seller should not have access
        self.client.credentials(**self.get_auth_headers(self.seller_user))
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Supervisor should not have access
        self.client.credentials(**self.get_auth_headers(self.supervisor_user))
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_self_access(self):
        """Users should be able to access their own information"""
        self.client.credentials(**self.get_auth_headers(self.seller_user))
        response = self.client.get(reverse('me'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'seller')
