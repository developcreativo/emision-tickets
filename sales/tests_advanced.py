import os
import tempfile
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from catalog.models import DrawSchedule, DrawType, NumberLimit, Zone

from .models import Ticket, TicketItem
from .serializers import TicketItemSerializer, TicketSerializer


class AdvancedTicketRulesTests(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(name='TestZone')
        self.draw = DrawType.objects.create(code='test', name='TestDraw')
        self.schedule = DrawSchedule.objects.create(
            zone=self.zone,
            draw_type=self.draw,
            cutoff_time=timezone.localtime().time().replace(hour=23, minute=59, second=0)
        )
        self.limit = NumberLimit.objects.create(
            zone=self.zone,
            draw_type=self.draw,
            number='12',
            max_pieces=5
        )
        User = get_user_model()
        self.user = User.objects.create_user(
            username='seller',
            password='pass',
            role='VENDEDOR'
        )
        self.client = APIClient()
        token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token)}')

    def test_ticket_with_multiple_numbers(self):
        """Test ticket creation with multiple numbers"""
        ticket_data = {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [
                {'number': '12', 'pieces': 2},
                {'number': '34', 'pieces': 3},
                {'number': '56', 'pieces': 1}
            ]
        }
        response = self.client.post('/api/sales/tickets/', ticket_data, format='json')
        self.assertEqual(response.status_code, 201)
        ticket = Ticket.objects.get(id=response.data['id'])
        self.assertEqual(ticket.total_pieces, 6)
        self.assertEqual(ticket.items.count(), 3)

    def test_ticket_with_zero_pieces(self):
        """Test ticket creation with zero pieces (should fail)"""
        ticket_data = {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [{'number': '12', 'pieces': 0}]
        }
        response = self.client.post('/api/sales/tickets/', ticket_data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_ticket_with_negative_pieces(self):
        """Test ticket creation with negative pieces (should fail)"""
        ticket_data = {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [{'number': '12', 'pieces': -1}]
        }
        response = self.client.post('/api/sales/tickets/', ticket_data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_ticket_with_invalid_number_format(self):
        """Test ticket creation with invalid number format"""
        invalid_numbers = ['1', '123', 'a1', '1a', '']
        for invalid_num in invalid_numbers:
            ticket_data = {
                'zone': self.zone.id,
                'draw_type': self.draw.id,
                'items': [{'number': invalid_num, 'pieces': 1}]
            }
            response = self.client.post('/api/sales/tickets/', ticket_data, format='json')
            self.assertEqual(response.status_code, 400, f"Failed for number: {invalid_num}")

    def test_ticket_with_decimal_pieces(self):
        """Test ticket creation with decimal pieces (should fail)"""
        ticket_data = {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [{'number': '12', 'pieces': 1.5}]
        }
        response = self.client.post('/api/sales/tickets/', ticket_data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_ticket_without_items(self):
        """Test ticket creation without items (should fail)"""
        ticket_data = {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': []
        }
        response = self.client.post('/api/sales/tickets/', ticket_data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_ticket_with_duplicate_numbers(self):
        """Test ticket creation with duplicate numbers (should fail)"""
        ticket_data = {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [
                {'number': '12', 'pieces': 1},
                {'number': '12', 'pieces': 2}
            ]
        }
        response = self.client.post('/api/sales/tickets/', ticket_data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_ticket_with_large_number_of_pieces(self):
        """Test ticket creation with very large number of pieces"""
        ticket_data = {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [{'number': '12', 'pieces': 999999}]
        }
        response = self.client.post('/api/sales/tickets/', ticket_data, format='json')
        self.assertEqual(response.status_code, 201)

    def test_ticket_with_boundary_number_values(self):
        """Test ticket creation with boundary number values (00 and 99)"""
        boundary_numbers = ['00', '99']
        for num in boundary_numbers:
            ticket_data = {
                'zone': self.zone.id,
                'draw_type': self.draw.id,
                'items': [{'number': num, 'pieces': 1}]
            }
            response = self.client.post('/api/sales/tickets/', ticket_data, format='json')
            self.assertEqual(response.status_code, 201, f"Failed for number: {num}")

    @override_settings(USE_TZ=False)
    def test_ticket_creation_timezone_handling(self):
        """Test ticket creation with different timezone settings"""
        ticket_data = {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [{'number': '12', 'pieces': 1}]
        }
        response = self.client.post('/api/sales/tickets/', ticket_data, format='json')
        self.assertEqual(response.status_code, 201)


class AdvancedAccumulatedLimitTests(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(name='TestZone')
        self.draw = DrawType.objects.create(code='test', name='TestDraw')
        self.schedule = DrawSchedule.objects.create(
            zone=self.zone,
            draw_type=self.draw,
            cutoff_time=timezone.localtime().time().replace(hour=23, minute=59, second=0)
        )
        self.limit = NumberLimit.objects.create(
            zone=self.zone,
            draw_type=self.draw,
            number='12',
            max_pieces=10
        )
        User = get_user_model()
        self.user = User.objects.create_user(
            username='seller',
            password='pass',
            role='VENDEDOR'
        )
        self.client = APIClient()
        token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token)}')

    def test_accumulated_limit_across_multiple_tickets(self):
        """Test accumulated limit across multiple tickets"""
        # First ticket: 4 pieces
        response1 = self.client.post('/api/sales/tickets/', {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [{'number': '12', 'pieces': 4}]
        }, format='json')
        self.assertEqual(response1.status_code, 201)

        # Second ticket: 4 pieces (total: 8)
        response2 = self.client.post('/api/sales/tickets/', {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [{'number': '12', 'pieces': 4}]
        }, format='json')
        self.assertEqual(response2.status_code, 201)

        # Third ticket: 3 pieces (total: 11, should fail)
        response3 = self.client.post('/api/sales/tickets/', {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [{'number': '12', 'pieces': 3}]
        }, format='json')
        self.assertEqual(response3.status_code, 400)

    def test_accumulated_limit_different_days(self):
        """Test that accumulated limits reset daily"""
        # Create ticket for today
        response1 = self.client.post('/api/sales/tickets/', {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [{'number': '12', 'pieces': 8}]
        }, format='json')
        self.assertEqual(response1.status_code, 201)

        # Create ticket for yesterday (should not affect today's limit)
        yesterday_ticket = Ticket.objects.create(
            zone=self.zone,
            draw_type=self.draw,
            user=self.user,
            total_pieces=5
        )
        yesterday_ticket.created_at = timezone.now() - timezone.timedelta(days=1)
        yesterday_ticket.save()

        # Should be able to create ticket with 3 pieces today (8 + 3 = 11 <= 10, should fail)
        response2 = self.client.post('/api/sales/tickets/', {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [{'number': '12', 'pieces': 3}]
        }, format='json')
        self.assertEqual(response2.status_code, 400)

    def test_accumulated_limit_different_zones(self):
        """Test that accumulated limits are zone-specific"""
        zone2 = Zone.objects.create(name='TestZone2')
        limit2 = NumberLimit.objects.create(
            zone=zone2,
            draw_type=self.draw,
            number='12',
            max_pieces=5
        )

        # Create ticket in first zone
        response1 = self.client.post('/api/sales/tickets/', {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [{'number': '12', 'pieces': 8}]
        }, format='json')
        self.assertEqual(response1.status_code, 201)

        # Should be able to create ticket in second zone (different accumulated limit)
        response2 = self.client.post('/api/sales/tickets/', {
            'zone': zone2.id,
            'draw_type': self.draw.id,
            'items': [{'number': '12', 'pieces': 3}]
        }, format='json')
        self.assertEqual(response2.status_code, 201)

    def test_accumulated_limit_different_draw_types(self):
        """Test that accumulated limits are draw-type-specific"""
        draw2 = DrawType.objects.create(code='test2', name='TestDraw2')
        limit2 = NumberLimit.objects.create(
            zone=self.zone,
            draw_type=draw2,
            number='12',
            max_pieces=5
        )

        # Create ticket for first draw type
        response1 = self.client.post('/api/sales/tickets/', {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [{'number': '12', 'pieces': 8}]
        }, format='json')
        self.assertEqual(response1.status_code, 201)

        # Should be able to create ticket for second draw type (different accumulated limit)
        response2 = self.client.post('/api/sales/tickets/', {
            'zone': self.zone.id,
            'draw_type': draw2.id,
            'items': [{'number': '12', 'pieces': 3}]
        }, format='json')
        self.assertEqual(response2.status_code, 201)


class AdvancedCutoffTimeTests(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(name='TestZone')
        self.draw = DrawType.objects.create(code='test', name='TestDraw')
        User = get_user_model()
        self.user = User.objects.create_user(
            username='seller',
            password='pass',
            role='VENDEDOR'
        )
        self.client = APIClient()
        token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token)}')

    def test_cutoff_time_exact_match(self):
        """Test cutoff time at exact boundary"""
        current_time = timezone.localtime()
        cutoff_time = current_time.time().replace(hour=current_time.hour, minute=0, second=0)
        
        schedule = DrawSchedule.objects.create(
            zone=self.zone,
            draw_type=self.draw,
            cutoff_time=cutoff_time
        )

        response = self.client.post('/api/sales/tickets/', {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [{'number': '12', 'pieces': 1}]
        }, format='json')
        
        # Should fail if current time is at or after cutoff
        if current_time.time() >= cutoff_time:
            self.assertEqual(response.status_code, 400)
        else:
            self.assertEqual(response.status_code, 201)

    def test_cutoff_time_midnight_boundary(self):
        """Test cutoff time at midnight boundary"""
        schedule = DrawSchedule.objects.create(
            zone=self.zone,
            draw_type=self.draw,
            cutoff_time=timezone.localtime().time().replace(hour=0, minute=0, second=0)
        )

        response = self.client.post('/api/sales/tickets/', {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [{'number': '12', 'pieces': 1}]
        }, format='json')
        self.assertEqual(response.status_code, 400)

    def test_cutoff_time_23_59_boundary(self):
        """Test cutoff time at 23:59 boundary"""
        schedule = DrawSchedule.objects.create(
            zone=self.zone,
            draw_type=self.draw,
            cutoff_time=timezone.localtime().time().replace(hour=23, minute=59, second=0)
        )

        response = self.client.post('/api/sales/tickets/', {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [{'number': '12', 'pieces': 1}]
        }, format='json')
        self.assertEqual(response.status_code, 201)

    def test_cutoff_time_inactive_schedule(self):
        """Test that inactive schedules don't enforce cutoff times"""
        schedule = DrawSchedule.objects.create(
            zone=self.zone,
            draw_type=self.draw,
            cutoff_time=timezone.localtime().time().replace(hour=0, minute=0, second=0),
            is_active=False
        )

        response = self.client.post('/api/sales/tickets/', {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [{'number': '12', 'pieces': 1}]
        }, format='json')
        self.assertEqual(response.status_code, 201)

    def test_cutoff_time_no_schedule(self):
        """Test behavior when no schedule exists"""
        response = self.client.post('/api/sales/tickets/', {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [{'number': '12', 'pieces': 1}]
        }, format='json')
        self.assertEqual(response.status_code, 400)


class AdvancedReportTests(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(name='Zone A')
        self.zone2 = Zone.objects.create(name='Zone B')
        self.draw = DrawType.objects.create(code='test', name='Test Draw')
        self.draw2 = DrawType.objects.create(code='test2', name='Test Draw 2')
        
        User = get_user_model()
        self.user = User.objects.create_user(username='seller', password='pass', role='VENDEDOR')
        self.user2 = User.objects.create_user(username='seller2', password='pass', role='VENDEDOR')
        
        self.client = APIClient()
        token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token)}')

        # Create test tickets
        self._create_test_tickets()

    def _create_test_tickets(self):
        """Create test tickets for reporting"""
        # Zone A, Draw 1, User 1
        for i in range(3):
            response = self.client.post('/api/sales/tickets/', {
                'zone': self.zone.id,
                'draw_type': self.draw.id,
                'items': [{'number': '01', 'pieces': 1}]
            }, format='json')
            assert response.status_code == 201

        # Zone B, Draw 1, User 2
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.user2).access_token}'
        )
        for i in range(2):
            response = self.client.post('/api/sales/tickets/', {
                'zone': self.zone2.id,
                'draw_type': self.draw.id,
                'items': [{'number': '02', 'pieces': 1}]
            }, format='json')
            assert response.status_code == 201

        # Zone A, Draw 2, User 1
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(self.user).access_token}'
        )
        for i in range(2):
            response = self.client.post('/api/sales/tickets/', {
                'zone': self.zone.id,
                'draw_type': self.draw2.id,
                'items': [{'number': '03', 'pieces': 1}]
            }, format='json')
            assert response.status_code == 201

    def test_reports_summary_by_zone(self):
        """Test reports summary grouped by zone"""
        response = self.client.get('/api/sales/tickets/reports/summary/?group_by=zone')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should have 2 zones
        self.assertEqual(len(data['summary']), 2)
        
        # Check totals
        self.assertEqual(data['totals']['total_tickets'], 7)
        self.assertEqual(data['totals']['total_pieces'], 7)

    def test_reports_summary_by_draw_type(self):
        """Test reports summary grouped by draw type"""
        response = self.client.get('/api/sales/tickets/reports/summary/?group_by=draw_type')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should have 2 draw types
        self.assertEqual(len(data['summary']), 2)
        
        # Check totals
        self.assertEqual(data['totals']['total_tickets'], 7)
        self.assertEqual(data['totals']['total_pieces'], 7)

    def test_reports_summary_by_user(self):
        """Test reports summary grouped by user"""
        response = self.client.get('/api/sales/tickets/reports/summary/?group_by=user')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should have 2 users
        self.assertEqual(len(data['summary']), 2)
        
        # Check totals
        self.assertEqual(data['totals']['total_tickets'], 7)
        self.assertEqual(data['totals']['total_pieces'], 7)

    def test_reports_summary_with_date_filters(self):
        """Test reports summary with date filters"""
        today = timezone.localtime().date()
        yesterday = today - timezone.timedelta(days=1)
        
        # Filter by today
        response = self.client.get(
            f'/api/sales/tickets/reports/summary/?group_by=zone&start={today}&end={today}'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['totals']['total_tickets'], 7)

        # Filter by yesterday (should be empty)
        response = self.client.get(
            f'/api/sales/tickets/reports/summary/?group_by=zone&start={yesterday}&end={yesterday}'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['totals']['total_tickets'], 0)

    def test_reports_summary_with_zone_filter(self):
        """Test reports summary with zone filter"""
        response = self.client.get(
            f'/api/sales/tickets/reports/summary/?group_by=zone&zones={self.zone.id}'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should only have Zone A
        self.assertEqual(len(data['summary']), 1)
        self.assertEqual(data['summary'][0]['zone__name'], 'Zone A')

    def test_reports_summary_with_draw_filter(self):
        """Test reports summary with draw type filter"""
        response = self.client.get(
            f'/api/sales/tickets/reports/summary/?group_by=zone&draws={self.draw.id}'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should only have Draw 1
        self.assertEqual(len(data['summary']), 2)  # Both zones for Draw 1

    def test_reports_summary_with_user_filter(self):
        """Test reports summary with user filter"""
        response = self.client.get(
            f'/api/sales/tickets/reports/summary/?group_by=zone&users={self.user.id}'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should only have User 1 tickets
        self.assertEqual(len(data['summary']), 2)  # Both zones for User 1

    def test_reports_summary_pagination(self):
        """Test reports summary pagination"""
        # Create more tickets to test pagination
        for i in range(15):
            response = self.client.post('/api/sales/tickets/', {
                'zone': self.zone.id,
                'draw_type': self.draw.id,
                'items': [{'number': f'{i:02d}', 'pieces': 1}]
            }, format='json')
            assert response.status_code == 201

        # Test first page
        response = self.client.get('/api/sales/tickets/reports/summary/?group_by=zone&page=1&page_size=5')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['summary']), 5)
        self.assertTrue(data['pagination']['has_next'])

        # Test second page
        response = self.client.get('/api/sales/tickets/reports/summary/?group_by=zone&page=2&page_size=5')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['pagination']['has_previous'])

    def test_reports_summary_daily_totals(self):
        """Test reports summary with daily totals"""
        response = self.client.get('/api/sales/tickets/reports/summary/?group_by=zone&daily=1')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should have daily breakdown
        self.assertIn('created_at__date', data['summary'][0])

    def test_reports_summary_invalid_group_by(self):
        """Test reports summary with invalid group_by parameter"""
        response = self.client.get('/api/sales/tickets/reports/summary/?group_by=invalid')
        self.assertEqual(response.status_code, 400)

    def test_reports_summary_invalid_pagination(self):
        """Test reports summary with invalid pagination parameters"""
        response = self.client.get('/api/sales/tickets/reports/summary/?group_by=zone&page=invalid&page_size=invalid')
        self.assertEqual(response.status_code, 400)


class AdvancedExportTests(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(name='TestZone')
        self.draw = DrawType.objects.create(code='test', name='TestDraw')
        User = get_user_model()
        self.user = User.objects.create_user(username='seller', password='pass', role='VENDEDOR')
        
        self.client = APIClient()
        token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token)}')

        # Create test tickets
        for i in range(5):
            response = self.client.post('/api/sales/tickets/', {
                'zone': self.zone.id,
                'draw_type': self.draw.id,
                'items': [{'number': f'{i:02d}', 'pieces': i + 1}]
            }, format='json')
            assert response.status_code == 201

    def test_csv_export(self):
        """Test CSV export functionality"""
        response = self.client.get('/api/sales/tickets/reports/export/?format=csv&group_by=zone')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])

    def test_excel_export(self):
        """Test Excel export functionality"""
        response = self.client.get('/api/sales/tickets/reports/export/?format=excel&group_by=zone')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertIn('attachment', response['Content-Disposition'])

    def test_export_with_filters(self):
        """Test export with various filters"""
        response = self.client.get(
            f'/api/sales/tickets/reports/export/?format=csv&group_by=zone&zones={self.zone.id}'
        )
        self.assertEqual(response.status_code, 200)

    def test_export_invalid_format(self):
        """Test export with invalid format"""
        response = self.client.get('/api/sales/tickets/reports/export/?format=invalid&group_by=zone')
        self.assertEqual(response.status_code, 400)


class AdvancedPDFTests(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(name='TestZone')
        self.draw = DrawType.objects.create(code='test', name='TestDraw')
        User = get_user_model()
        self.user = User.objects.create_user(username='seller', password='pass', role='VENDEDOR')
        
        self.client = APIClient()
        token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token)}')

        # Create test ticket
        response = self.client.post('/api/sales/tickets/', {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [{'number': '12', 'pieces': 3}]
        }, format='json')
        self.ticket_id = response.data['id']

    def test_pdf_generation(self):
        """Test PDF generation for ticket"""
        response = self.client.get(f'/api/sales/tickets/{self.ticket_id}/pdf/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])

    def test_pdf_preview(self):
        """Test PDF preview for ticket"""
        response = self.client.get(f'/api/sales/tickets/{self.ticket_id}/preview/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')

    def test_pdf_nonexistent_ticket(self):
        """Test PDF generation for nonexistent ticket"""
        response = self.client.get('/api/sales/tickets/99999/pdf/')
        self.assertEqual(response.status_code, 404)


class AdvancedModelTests(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(name='TestZone')
        self.draw = DrawType.objects.create(code='test', name='TestDraw')
        User = get_user_model()
        self.user = User.objects.create_user(username='seller', password='pass', role='VENDEDOR')

    def test_ticket_str_representation(self):
        """Test ticket string representation"""
        ticket = Ticket.objects.create(
            zone=self.zone,
            draw_type=self.draw,
            user=self.user,
            total_pieces=5
        )
        expected_str = f'Ticket {ticket.id} - {self.zone.name} - {self.draw.name}'
        self.assertEqual(str(ticket), expected_str)

    def test_ticket_item_str_representation(self):
        """Test ticket item string representation"""
        ticket = Ticket.objects.create(
            zone=self.zone,
            draw_type=self.draw,
            user=self.user,
            total_pieces=5
        )
        item = TicketItem.objects.create(
            ticket=ticket,
            number='12',
            pieces=3
        )
        expected_str = f'{item.number} - {item.pieces} piezas'
        self.assertEqual(str(item), expected_str)

    def test_ticket_total_pieces_calculation(self):
        """Test ticket total pieces calculation"""
        ticket = Ticket.objects.create(
            zone=self.zone,
            draw_type=self.draw,
            user=self.user,
            total_pieces=0
        )
        
        # Add items
        TicketItem.objects.create(ticket=ticket, number='12', pieces=3)
        TicketItem.objects.create(ticket=ticket, number='34', pieces=2)
        
        # Recalculate total
        ticket.total_pieces = sum(item.pieces for item in ticket.items.all())
        ticket.save()
        
        self.assertEqual(ticket.total_pieces, 5)

    def test_ticket_created_updated_timestamps(self):
        """Test ticket created and updated timestamps"""
        ticket = Ticket.objects.create(
            zone=self.zone,
            draw_type=self.draw,
            user=self.user,
            total_pieces=5
        )
        
        self.assertIsNotNone(ticket.created_at)
        self.assertIsNotNone(ticket.updated_at)
        
        # Update ticket
        old_updated = ticket.updated_at
        ticket.total_pieces = 10
        ticket.save()
        
        self.assertGreater(ticket.updated_at, old_updated)

    def test_ticket_item_created_updated_timestamps(self):
        """Test ticket item created and updated timestamps"""
        ticket = Ticket.objects.create(
            zone=self.zone,
            draw_type=self.draw,
            user=self.user,
            total_pieces=5
        )
        
        item = TicketItem.objects.create(
            ticket=ticket,
            number='12',
            pieces=3
        )
        
        self.assertIsNotNone(item.created_at)
        self.assertIsNotNone(item.updated_at)
        
        # Update item
        old_updated = item.updated_at
        item.pieces = 5
        item.save()
        
        self.assertGreater(item.updated_at, old_updated)


class AdvancedSerializerTests(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(name='TestZone')
        self.draw = DrawType.objects.create(code='test', name='TestDraw')
        User = get_user_model()
        self.user = User.objects.create_user(username='seller', password='pass', role='VENDEDOR')

    def test_ticket_serializer_with_items(self):
        """Test ticket serializer with items"""
        ticket_data = {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [
                {'number': '12', 'pieces': 3},
                {'number': '34', 'pieces': 2}
            ]
        }
        serializer = TicketSerializer(data=ticket_data)
        self.assertTrue(serializer.is_valid())

    def test_ticket_serializer_without_items(self):
        """Test ticket serializer without items"""
        ticket_data = {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': []
        }
        serializer = TicketSerializer(data=ticket_data)
        self.assertFalse(serializer.is_valid())

    def test_ticket_item_serializer(self):
        """Test ticket item serializer"""
        item_data = {'number': '12', 'pieces': 3}
        serializer = TicketItemSerializer(data=item_data)
        self.assertTrue(serializer.is_valid())

    def test_ticket_item_serializer_invalid_number(self):
        """Test ticket item serializer with invalid number"""
        item_data = {'number': '123', 'pieces': 3}
        serializer = TicketItemSerializer(data=item_data)
        self.assertFalse(serializer.is_valid())

    def test_ticket_item_serializer_invalid_pieces(self):
        """Test ticket item serializer with invalid pieces"""
        item_data = {'number': '12', 'pieces': -1}
        serializer = TicketItemSerializer(data=item_data)
        self.assertFalse(serializer.is_valid())


class AdvancedIntegrationTests(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(name='TestZone')
        self.draw = DrawType.objects.create(code='test', name='TestDraw')
        self.schedule = DrawSchedule.objects.create(
            zone=self.zone,
            draw_type=self.draw,
            cutoff_time=timezone.localtime().time().replace(hour=23, minute=59, second=0)
        )
        self.limit = NumberLimit.objects.create(
            zone=self.zone,
            draw_type=self.draw,
            number='12',
            max_pieces=10
        )
        User = get_user_model()
        self.user = User.objects.create_user(username='seller', password='pass', role='VENDEDOR')
        
        self.client = APIClient()
        token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token)}')

    def test_complete_ticket_workflow(self):
        """Test complete ticket workflow from creation to report"""
        # 1. Create ticket
        ticket_data = {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [{'number': '12', 'pieces': 3}]
        }
        response = self.client.post('/api/sales/tickets/', ticket_data, format='json')
        self.assertEqual(response.status_code, 201)
        ticket_id = response.data['id']

        # 2. Retrieve ticket
        response = self.client.get(f'/api/sales/tickets/{ticket_id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total_pieces'], 3)

        # 3. Generate PDF
        response = self.client.get(f'/api/sales/tickets/{ticket_id}/pdf/')
        self.assertEqual(response.status_code, 200)

        # 4. Generate report
        response = self.client.get('/api/sales/tickets/reports/summary/?group_by=zone')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['totals']['total_tickets'], 1)

        # 5. Export report
        response = self.client.get('/api/sales/tickets/reports/export/?format=csv&group_by=zone')
        self.assertEqual(response.status_code, 200)

    def test_concurrent_ticket_creation(self):
        """Test concurrent ticket creation with limits"""
        import queue
        import threading

        results = queue.Queue()

        def create_ticket():
            try:
                response = self.client.post('/api/sales/tickets/', {
                    'zone': self.zone.id,
                    'draw_type': self.draw.id,
                    'items': [{'number': '12', 'pieces': 3}]
                }, format='json')
                results.put(response.status_code)
            except Exception as e:
                results.put(f"Error: {e}")

        # Create multiple threads to create tickets simultaneously
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_ticket)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        status_codes = []
        while not results.empty():
            status_codes.append(results.get())

        # Should have some successful and some failed due to limits
        self.assertIn(201, status_codes)  # At least one should succeed
        self.assertIn(400, status_codes)  # At least one should fail due to limits

    def test_ticket_with_large_number_of_items(self):
        """Test ticket creation with large number of items"""
        items = []
        for i in range(100):  # Create 100 items
            items.append({'number': f'{i:02d}', 'pieces': 1})

        ticket_data = {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': items
        }

        response = self.client.post('/api/sales/tickets/', ticket_data, format='json')
        self.assertEqual(response.status_code, 201)
        
        ticket = Ticket.objects.get(id=response.data['id'])
        self.assertEqual(ticket.total_pieces, 100)
        self.assertEqual(ticket.items.count(), 100)

    def test_ticket_performance_with_many_tickets(self):
        """Test performance with many tickets"""
        # Create many tickets
        for i in range(100):
            response = self.client.post('/api/sales/tickets/', {
                'zone': self.zone.id,
                'draw_type': self.draw.id,
                'items': [{'number': f'{i:02d}', 'pieces': 1}]
            }, format='json')
            assert response.status_code == 201

        # Test report generation performance
        import time
        start_time = time.time()
        
        response = self.client.get('/api/sales/tickets/reports/summary/?group_by=zone')
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(execution_time, 1.0)  # Should complete in less than 1 second
