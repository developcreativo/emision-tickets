import random

from locust import HttpUser, between, task


class TicketSystemUser(HttpUser):
    """
    Usuario simulado para tests de carga del sistema de tickets
    """
    wait_time = between(1, 3)  # Esperar entre 1-3 segundos entre requests
    
    def on_start(self):
        """Autenticación al inicio de la sesión"""
        # Login para obtener token
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = self.client.post("/api/auth/token/", json=login_data)
        if response.status_code == 200:
            token = response.json()["access"]
            self.client.headers.update({"Authorization": f"Bearer {token}"})
    
    @task(3)
    def get_tickets_list(self):
        """Obtener lista de tickets (alta frecuencia)"""
        self.client.get("/api/sales/tickets/")
    
    @task(2)
    def get_ticket_detail(self):
        """Obtener detalle de un ticket específico"""
        # Simular ID de ticket (en producción usar IDs reales)
        ticket_id = random.randint(1, 100)
        self.client.get(f"/api/sales/tickets/{ticket_id}/")
    
    @task(1)
    def create_ticket(self):
        """Crear un nuevo ticket (baja frecuencia)"""
        ticket_data = {
            "zone": 1,
            "draw_type": 1,
            "items": [
                {
                    "number": f"{random.randint(0, 99):02d}", 
                    "pieces": random.randint(1, 5)
                }
                for _ in range(random.randint(1, 3))
            ]
        }
        self.client.post("/api/sales/tickets/", json=ticket_data)
    
    @task(2)
    def get_reports(self):
        """Obtener reportes (frecuencia media)"""
        self.client.get("/api/sales/reports/summary/")
    
    @task(1)
    def get_catalog_data(self):
        """Obtener datos del catálogo"""
        self.client.get("/api/catalog/zones/")
        self.client.get("/api/catalog/draw-types/")


class ReportUser(HttpUser):
    """
    Usuario especializado en generar reportes
    """
    wait_time = between(5, 10)  # Más tiempo entre requests
    
    def on_start(self):
        """Autenticación"""
        login_data = {"username": "admin", "password": "admin123"}
        response = self.client.post("/api/auth/token/", json=login_data)
        if response.status_code == 200:
            token = response.json()["access"]
            self.client.headers.update({"Authorization": f"Bearer {token}"})
    
    @task(3)
    def get_summary_report(self):
        """Obtener reporte de resumen"""
        params = {
            "group_by": random.choice(["zone", "draw_type", "user"]),
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        }
        self.client.get("/api/sales/reports/summary/", params=params)
    
    @task(2)
    def get_detailed_report(self):
        """Obtener reporte detallado"""
        self.client.get("/api/sales/reports/detailed/")
    
    @task(1)
    def export_report(self):
        """Exportar reporte"""
        format_type = random.choice(["csv", "xlsx"])
        self.client.get(f"/api/sales/reports/export/?format={format_type}")


class AdminUser(HttpUser):
    """
    Usuario administrador con acceso completo
    """
    wait_time = between(2, 5)
    
    def on_start(self):
        """Autenticación de admin"""
        login_data = {"username": "admin", "password": "admin123"}
        response = self.client.post("/api/auth/token/", json=login_data)
        if response.status_code == 200:
            token = response.json()["access"]
            self.client.headers.update({"Authorization": f"Bearer {token}"})
    
    @task(2)
    def manage_users(self):
        """Gestión de usuarios"""
        self.client.get("/api/accounts/users/")
    
    @task(1)
    def manage_catalog(self):
        """Gestión del catálogo"""
        self.client.get("/api/catalog/zones/")
        self.client.get("/api/catalog/draw-types/")
        self.client.get("/api/catalog/schedules/")
    
    @task(1)
    def system_health(self):
        """Verificar salud del sistema"""
        self.client.get("/api/health/")


# Configuración para diferentes escenarios de carga
class LightLoadUser(TicketSystemUser):
    """Carga ligera - solo lectura"""
    wait_time = between(3, 6)
    
    @task(5)
    def read_only_operations(self):
        """Solo operaciones de lectura"""
        self.client.get("/api/sales/tickets/")
        self.client.get("/api/catalog/zones/")


class HeavyLoadUser(TicketSystemUser):
    """Carga pesada - muchas operaciones de escritura"""
    wait_time = between(0.5, 1.5)
    
    @task(4)
    def create_many_tickets(self):
        """Crear muchos tickets rápidamente"""
        for _ in range(3):
            ticket_data = {
                "zone": random.randint(1, 5),
                "draw_type": random.randint(1, 3),
                "items": [
                    {
                        "number": f"{random.randint(0, 99):02d}", 
                        "pieces": random.randint(1, 10)
                    }
                    for _ in range(random.randint(1, 5))
                ]
            }
            self.client.post("/api/sales/tickets/", json=ticket_data)
