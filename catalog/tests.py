from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User

from .models import DrawSchedule, DrawType, NumberLimit, Zone
from .serializers import (
    DrawScheduleSerializer,
    DrawTypeSerializer,
    NumberLimitSerializer,
    ZoneSerializer,
)


class ZoneModelTests(TestCase):
    def setUp(self):
        self.zone_data = {
            'name': 'Test Zone',
            'description': 'A test zone for testing purposes'
        }

    def test_create_zone(self):
        zone = Zone.objects.create(**self.zone_data)
        self.assertEqual(zone.name, 'Test Zone')
        self.assertEqual(zone.description, 'A test zone for testing purposes')
        self.assertIsNotNone(zone.created_at)
        self.assertIsNotNone(zone.updated_at)

    def test_zone_str_representation(self):
        zone = Zone.objects.create(**self.zone_data)
        self.assertEqual(str(zone), 'Test Zone')

    def test_zone_ordering(self):
        zone1 = Zone.objects.create(name='Zone A')
        zone2 = Zone.objects.create(name='Zone B')
        zones = list(Zone.objects.all())
        self.assertEqual(zones[0], zone1)
        self.assertEqual(zones[1], zone2)


class DrawTypeModelTests(TestCase):
    def setUp(self):
        self.draw_type_data = {
            'code': 'TEST',
            'name': 'Test Draw',
            'description': 'A test draw type'
        }

    def test_create_draw_type(self):
        draw_type = DrawType.objects.create(**self.draw_type_data)
        self.assertEqual(draw_type.code, 'TEST')
        self.assertEqual(draw_type.name, 'Test Draw')
        self.assertEqual(draw_type.description, 'A test draw type')
        self.assertIsNotNone(draw_type.created_at)
        self.assertIsNotNone(draw_type.updated_at)

    def test_draw_type_str_representation(self):
        draw_type = DrawType.objects.create(**self.draw_type_data)
        self.assertEqual(str(draw_type), 'TEST - Test Draw')

    def test_draw_type_ordering(self):
        draw1 = DrawType.objects.create(code='A', name='Draw A')
        draw2 = DrawType.objects.create(code='B', name='Draw B')
        draws = list(DrawType.objects.all())
        self.assertEqual(draws[0], draw1)
        self.assertEqual(draws[1], draw2)


class DrawScheduleModelTests(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(name='Test Zone')
        self.draw_type = DrawType.objects.create(code='TEST', name='Test Draw')
        self.schedule_data = {
            'zone': self.zone,
            'draw_type': self.draw_type,
            'cutoff_time': timezone.localtime().time().replace(hour=18, minute=0, second=0),
            'is_active': True
        }

    def test_create_draw_schedule(self):
        schedule = DrawSchedule.objects.create(**self.schedule_data)
        self.assertEqual(schedule.zone, self.zone)
        self.assertEqual(schedule.draw_type, self.draw_type)
        self.assertEqual(schedule.cutoff_time.hour, 18)
        self.assertTrue(schedule.is_active)
        self.assertIsNotNone(schedule.created_at)
        self.assertIsNotNone(schedule.updated_at)

    def test_draw_schedule_str_representation(self):
        schedule = DrawSchedule.objects.create(**self.schedule_data)
        expected_str = f'Test Zone - Test Draw ({schedule.cutoff_time.strftime("%H:%M")})'
        self.assertEqual(str(schedule), expected_str)

    def test_draw_schedule_unique_constraint(self):
        """Test that zone + draw_type combination is unique"""
        DrawSchedule.objects.create(**self.schedule_data)
        
        # Try to create another with same zone and draw_type
        with self.assertRaises(Exception):
            DrawSchedule.objects.create(**self.schedule_data)


class NumberLimitModelTests(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(name='Test Zone')
        self.draw_type = DrawType.objects.create(code='TEST', name='Test Draw')
        self.limit_data = {
            'zone': self.zone,
            'draw_type': self.draw_type,
            'number': '12',
            'max_pieces': 100
        }

    def test_create_number_limit(self):
        limit = NumberLimit.objects.create(**self.limit_data)
        self.assertEqual(limit.zone, self.zone)
        self.assertEqual(limit.draw_type, self.draw_type)
        self.assertEqual(limit.number, '12')
        self.assertEqual(limit.max_pieces, 100)
        self.assertIsNotNone(limit.created_at)
        self.assertIsNotNone(limit.updated_at)

    def test_number_limit_str_representation(self):
        limit = NumberLimit.objects.create(**self.limit_data)
        expected_str = 'Test Zone - Test Draw - 12 (100)'
        self.assertEqual(str(limit), expected_str)

    def test_number_limit_unique_constraint(self):
        """Test that zone + draw_type + number combination is unique"""
        NumberLimit.objects.create(**self.limit_data)
        
        # Try to create another with same zone, draw_type and number
        with self.assertRaises(Exception):
            NumberLimit.objects.create(**self.limit_data)


class ZoneSerializerTests(TestCase):
    def setUp(self):
        self.zone_data = {
            'name': 'Test Zone',
            'description': 'A test zone'
        }
        self.zone = Zone.objects.create(**self.zone_data)

    def test_zone_serializer_validation(self):
        serializer = ZoneSerializer(data=self.zone_data)
        self.assertTrue(serializer.is_valid())

    def test_zone_serializer_serialization(self):
        serializer = ZoneSerializer(self.zone)
        data = serializer.data
        self.assertEqual(data['name'], 'Test Zone')
        self.assertEqual(data['description'], 'A test zone')
        self.assertIn('id', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)

    def test_zone_serializer_update(self):
        update_data = {'name': 'Updated Zone', 'description': 'Updated description'}
        serializer = ZoneSerializer(self.zone, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_zone = serializer.save()
        self.assertEqual(updated_zone.name, 'Updated Zone')
        self.assertEqual(updated_zone.description, 'Updated description')


class DrawTypeSerializerTests(TestCase):
    def setUp(self):
        self.draw_type_data = {
            'code': 'TEST',
            'name': 'Test Draw',
            'description': 'A test draw'
        }
        self.draw_type = DrawType.objects.create(**self.draw_type_data)

    def test_draw_type_serializer_validation(self):
        serializer = DrawTypeSerializer(data=self.draw_type_data)
        self.assertTrue(serializer.is_valid())

    def test_draw_type_serializer_serialization(self):
        serializer = DrawTypeSerializer(self.draw_type)
        data = serializer.data
        self.assertEqual(data['code'], 'TEST')
        self.assertEqual(data['name'], 'Test Draw')
        self.assertEqual(data['description'], 'A test draw')
        self.assertIn('id', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)

    def test_draw_type_serializer_update(self):
        update_data = {'name': 'Updated Draw', 'description': 'Updated description'}
        serializer = DrawTypeSerializer(self.draw_type, data=update_data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_draw = serializer.save()
        self.assertEqual(updated_draw.name, 'Updated Draw')
        self.assertEqual(updated_draw.description, 'Updated description')


class DrawScheduleSerializerTests(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(name='Test Zone')
        self.draw_type = DrawType.objects.create(code='TEST', name='Test Draw')
        self.schedule_data = {
            'zone': self.zone.id,
            'draw_type': self.draw_type.id,
            'cutoff_time': '18:00:00',
            'is_active': True
        }
        self.schedule = DrawSchedule.objects.create(
            zone=self.zone,
            draw_type=self.draw_type,
            cutoff_time=timezone.localtime().time().replace(hour=18, minute=0, second=0),
            is_active=True
        )

    def test_draw_schedule_serializer_validation(self):
        serializer = DrawScheduleSerializer(data=self.schedule_data)
        self.assertTrue(serializer.is_valid())

    def test_draw_schedule_serializer_serialization(self):
        serializer = DrawScheduleSerializer(self.schedule)
        data = serializer.data
        self.assertEqual(data['zone'], self.zone.id)
        self.assertEqual(data['draw_type'], self.draw_type.id)
        self.assertTrue(data['is_active'])
        self.assertIn('id', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)


class NumberLimitSerializerTests(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(name='Test Zone')
        self.draw_type = DrawType.objects.create(code='TEST', name='Test Draw')
        self.limit_data = {
            'zone': self.zone.id,
            'draw_type': self.draw_type.id,
            'number': '12',
            'max_pieces': 100
        }
        self.limit = NumberLimit.objects.create(
            zone=self.zone,
            draw_type=self.draw_type,
            number='12',
            max_pieces=100
        )

    def test_number_limit_serializer_validation(self):
        serializer = NumberLimitSerializer(data=self.limit_data)
        self.assertTrue(serializer.is_valid())

    def test_number_limit_serializer_serialization(self):
        serializer = NumberLimitSerializer(self.limit)
        data = serializer.data
        self.assertEqual(data['zone'], self.zone.id)
        self.assertEqual(data['draw_type'], self.draw_type.id)
        self.assertEqual(data['number'], '12')
        self.assertEqual(data['max_pieces'], 100)
        self.assertIn('id', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)


class ZoneViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        self.zone = Zone.objects.create(name='Test Zone')
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.admin_user).access_token}'
        )

    def test_list_zones(self):
        response = self.client.get(reverse('zone-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Zone')

    def test_create_zone(self):
        new_zone_data = {'name': 'New Zone', 'description': 'New zone description'}
        response = self.client.post(reverse('zone-list'), new_zone_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Zone')

    def test_retrieve_zone(self):
        response = self.client.get(reverse('zone-detail', args=[self.zone.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Zone')

    def test_update_zone(self):
        update_data = {'name': 'Updated Zone'}
        response = self.client.patch(
            reverse('zone-detail', args=[self.zone.id]),
            update_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.zone.refresh_from_db()
        self.assertEqual(self.zone.name, 'Updated Zone')

    def test_delete_zone(self):
        response = self.client.delete(reverse('zone-detail', args=[self.zone.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Zone.objects.filter(id=self.zone.id).exists())


class DrawTypeViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        self.draw_type = DrawType.objects.create(code='TEST', name='Test Draw')
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.admin_user).access_token}'
        )

    def test_list_draw_types(self):
        response = self.client.get(reverse('drawtype-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['code'], 'TEST')

    def test_create_draw_type(self):
        new_draw_data = {'code': 'NEW', 'name': 'New Draw', 'description': 'New draw type'}
        response = self.client.post(reverse('drawtype-list'), new_draw_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['code'], 'NEW')

    def test_retrieve_draw_type(self):
        response = self.client.get(reverse('drawtype-detail', args=[self.draw_type.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 'TEST')

    def test_update_draw_type(self):
        update_data = {'name': 'Updated Draw'}
        response = self.client.patch(
            reverse('drawtype-detail', args=[self.draw_type.id]),
            update_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.draw_type.refresh_from_db()
        self.assertEqual(self.draw_type.name, 'Updated Draw')

    def test_delete_draw_type(self):
        response = self.client.delete(reverse('drawtype-detail', args=[self.draw_type.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(DrawType.objects.filter(id=self.draw_type.id).exists())


class DrawScheduleViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        self.zone = Zone.objects.create(name='Test Zone')
        self.draw_type = DrawType.objects.create(code='TEST', name='Test Draw')
        self.schedule = DrawSchedule.objects.create(
            zone=self.zone,
            draw_type=self.draw_type,
            cutoff_time=timezone.localtime().time().replace(hour=18, minute=0, second=0),
            is_active=True
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.admin_user).access_token}'
        )

    def test_list_draw_schedules(self):
        response = self.client.get(reverse('drawschedule-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_draw_schedule(self):
        new_schedule_data = {
            'zone': self.zone.id,
            'draw_type': self.draw_type.id,
            'cutoff_time': '19:00:00',
            'is_active': True
        }
        response = self.client.post(reverse('drawschedule-list'), new_schedule_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_retrieve_draw_schedule(self):
        response = self.client.get(reverse('drawschedule-detail', args=[self.schedule.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_draw_schedule(self):
        update_data = {'cutoff_time': '20:00:00'}
        response = self.client.patch(
            reverse('drawschedule-detail', args=[self.schedule.id]),
            update_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.schedule.refresh_from_db()
        self.assertEqual(self.schedule.cutoff_time.hour, 20)

    def test_delete_draw_schedule(self):
        response = self.client.delete(reverse('drawschedule-detail', args=[self.schedule.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(DrawSchedule.objects.filter(id=self.schedule.id).exists())


class NumberLimitViewSetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        self.zone = Zone.objects.create(name='Test Zone')
        self.draw_type = DrawType.objects.create(code='TEST', name='Test Draw')
        self.limit = NumberLimit.objects.create(
            zone=self.zone,
            draw_type=self.draw_type,
            number='12',
            max_pieces=100
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.admin_user).access_token}'
        )

    def test_list_number_limits(self):
        response = self.client.get(reverse('numberlimit-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_number_limit(self):
        new_limit_data = {
            'zone': self.zone.id,
            'draw_type': self.draw_type.id,
            'number': '34',
            'max_pieces': 50
        }
        response = self.client.post(reverse('numberlimit-list'), new_limit_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_retrieve_number_limit(self):
        response = self.client.get(reverse('numberlimit-detail', args=[self.limit.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_number_limit(self):
        update_data = {'max_pieces': 150}
        response = self.client.patch(
            reverse('numberlimit-detail', args=[self.limit.id]),
            update_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.limit.refresh_from_db()
        self.assertEqual(self.limit.max_pieces, 150)

    def test_delete_number_limit(self):
        response = self.client.delete(reverse('numberlimit-detail', args=[self.limit.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(NumberLimit.objects.filter(id=self.limit.id).exists())


class CatalogPermissionsTests(TestCase):
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
            role='VENDEDOR'
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

    def test_zone_access_permissions(self):
        """Test zone access permissions for different roles"""
        
        # Admin should have full access
        self.client.credentials(**self.get_auth_headers(self.admin_user))
        response = self.client.get(reverse('zone-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Seller should not have access
        self.client.credentials(**self.get_auth_headers(self.seller_user))
        response = self.client.get(reverse('zone-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Supervisor should not have access
        self.client.credentials(**self.get_auth_headers(self.supervisor_user))
        response = self.client.get(reverse('zone-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_draw_type_access_permissions(self):
        """Test draw type access permissions for different roles"""
        
        # Admin should have full access
        self.client.credentials(**self.get_auth_headers(self.admin_user))
        response = self.client.get(reverse('drawtype-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Seller should not have access
        self.client.credentials(**self.get_auth_headers(self.seller_user))
        response = self.client.get(reverse('drawtype-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_draw_schedule_access_permissions(self):
        """Test draw schedule access permissions for different roles"""
        
        # Admin should have full access
        self.client.credentials(**self.get_auth_headers(self.admin_user))
        response = self.client.get(reverse('drawschedule-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Seller should not have access
        self.client.credentials(**self.get_auth_headers(self.seller_user))
        response = self.client.get(reverse('drawschedule-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_number_limit_access_permissions(self):
        """Test number limit access permissions for different roles"""
        
        # Admin should have full access
        self.client.credentials(**self.get_auth_headers(self.admin_user))
        response = self.client.get(reverse('numberlimit-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Seller should not have access
        self.client.credentials(**self.get_auth_headers(self.seller_user))
        response = self.client.get(reverse('numberlimit-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
