from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from catalog.models import DrawSchedule, DrawType, NumberLimit, Zone

from .models import Ticket, TicketItem


class TicketRulesTests(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(name='TestZone')
        self.draw = DrawType.objects.create(code='test', name='TestDraw')
        DrawSchedule.objects.create(zone=self.zone, draw_type=self.draw, cutoff_time=timezone.localtime().time().replace(hour=23, minute=59, second=0))
        NumberLimit.objects.create(zone=self.zone, draw_type=self.draw, number='12', max_pieces=5)
        User = get_user_model()
        self.user = User.objects.create_user(username='seller', password='pass', role='SELLER')
        self.client = APIClient()
        # Auth
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token)}')

    def test_ticket_creation_and_total(self):
        res = self.client.post('/api/sales/tickets/', {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [{'number': '12', 'pieces': 3}, {'number': '34', 'pieces': 2}],
        }, format='json')
        self.assertEqual(res.status_code, 201, res.content)
        ticket = Ticket.objects.get(id=res.data['id'])
        self.assertEqual(ticket.total_pieces, 5)

    def test_accumulated_limit(self):
        # First sale 3 pieces of 12
        self.client.post('/api/sales/tickets/', {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [{'number': '12', 'pieces': 3}],
        }, format='json')
        # Second sale exceeding limit (3 already + 3 > 5)
        res = self.client.post('/api/sales/tickets/', {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [{'number': '12', 'pieces': 3}],
        }, format='json')
        self.assertEqual(res.status_code, 400)

    def test_cutoff_block(self):
        # Move cutoff earlier
        sched = DrawSchedule.objects.get(zone=self.zone, draw_type=self.draw)
        sched.cutoff_time = timezone.localtime().time().replace(hour=0, minute=0, second=0)
        sched.save()
        res = self.client.post('/api/sales/tickets/', {
            'zone': self.zone.id,
            'draw_type': self.draw.id,
            'items': [{'number': '12', 'pieces': 1}],
        }, format='json')
        self.assertEqual(res.status_code, 400)


class ReportsTests(TestCase):
    def setUp(self):
        self.zone = Zone.objects.create(name='Z')
        self.draw = DrawType.objects.create(code='d', name='D')
        DrawSchedule.objects.create(zone=self.zone, draw_type=self.draw, cutoff_time=timezone.localtime().time().replace(hour=23, minute=59, second=0))
        User = get_user_model()
        self.user = User.objects.create_user(username='s', password='p', role='SELLER')
        self.client = APIClient()
        from rest_framework_simplejwt.tokens import RefreshToken
        token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token)}')
        # Create some tickets
        for i in range(3):
            res = self.client.post('/api/sales/tickets/', {
                'zone': self.zone.id,
                'draw_type': self.draw.id,
                'items': [{'number': '01', 'pieces': 1}],
            }, format='json')
            assert res.status_code == 201

    def test_reports_summary_by_zone(self):
        res = self.client.get('/api/sales/tickets/reports/summary/?group_by=zone')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['totals']['total_tickets'], 3)


