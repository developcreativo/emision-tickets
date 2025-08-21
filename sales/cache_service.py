import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from django.conf import settings
from django.core.cache import cache
from django.db.models import Count, Sum
from django.utils import timezone

from .models import Ticket


class ReportCacheService:
    """Servicio para manejar el cache de reportes de ventas"""
    
    @staticmethod
    def _generate_cache_key(prefix: str, params: Dict[str, Any]) -> str:
        """Genera una clave única para el cache basada en los parámetros"""
        # Ordenar parámetros para consistencia
        sorted_params = sorted(params.items())
        params_str = json.dumps(sorted_params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        return f"report_{prefix}_{params_hash}"
    
    @staticmethod
    def _get_cache_timeout(include_daily: bool = False) -> int:
        """Obtiene el timeout del cache según el tipo de reporte"""
        if include_daily:
            return getattr(settings, 'DAILY_REPORTS_CACHE_TIMEOUT', 3600)
        return getattr(settings, 'REPORTS_CACHE_TIMEOUT', 600)
    
    @staticmethod
    def get_summary_report(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        zone: Optional[str] = None,
        draw_type: Optional[str] = None,
        user: Optional[str] = None,
        group_by: str = 'zone',
        page: int = 1,
        page_size: int = 50,
        include_daily: bool = False,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Obtiene el reporte de resumen con cache
        
        Args:
            start_date: Fecha de inicio (YYYY-MM-DD)
            end_date: Fecha de fin (YYYY-MM-DD)
            zone: ID de zona(s) separados por coma
            draw_type: ID de tipo(s) de sorteo separados por coma
            user: ID de usuario(s) separados por coma
            group_by: Campo por el cual agrupar (zone, draw_type, user)
            page: Número de página
            page_size: Tamaño de página
            include_daily: Incluir datos diarios
            force_refresh: Forzar refrescar cache
            
        Returns:
            Dict con los datos del reporte
        """
        # Generar parámetros para la clave del cache
        cache_params = {
            'start_date': start_date,
            'end_date': end_date,
            'zone': zone,
            'draw_type': draw_type,
            'user': user,
            'group_by': group_by,
            'page': page,
            'page_size': page_size,
            'include_daily': include_daily
        }
        
        cache_key = ReportCacheService._generate_cache_key('summary', cache_params)
        
        # Si no se fuerza refrescar, intentar obtener del cache
        if not force_refresh:
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data
        
        # Generar el reporte
        report_data = ReportCacheService._generate_summary_report(
            start_date, end_date, zone, draw_type, user,
            group_by, page, page_size, include_daily
        )
        
        # Guardar en cache
        timeout = ReportCacheService._get_cache_timeout(include_daily)
        cache.set(cache_key, report_data, timeout)
        
        return report_data
    
    @staticmethod
    def _generate_summary_report(
        start_date: Optional[str],
        end_date: Optional[str],
        zone: Optional[str],
        draw_type: Optional[str],
        user: Optional[str],
        group_by: str,
        page: int,
        page_size: int,
        include_daily: bool
    ) -> Dict[str, Any]:
        """Genera el reporte de resumen sin cache"""
        # Construir filtros
        filters = {}
        if start_date:
            filters['created_at__date__gte'] = start_date
        if end_date:
            filters['created_at__date__lte'] = end_date
        if zone:
            filters['zone_id__in'] = [z.strip() for z in zone.split(',') if z.strip()]
        if draw_type:
            filters['draw_type_id__in'] = [d.strip() for d in draw_type.split(',') if d.strip()]
        if user:
            filters['user_id__in'] = [u.strip() for u in user.split(',') if u.strip()]
        
        # Validar group_by
        if group_by not in {'zone', 'draw_type', 'user'}:
            return {'error': 'group_by inválido'}
        
        # Query base
        qs = Ticket.objects.filter(**filters)
        
        # Configurar campos según group_by
        if group_by == 'zone':
            values = ('zone__name',)
            label_field = 'zone__name'
        elif group_by == 'draw_type':
            values = ('draw_type__name',)
            label_field = 'draw_type__name'
        else:  # user
            values = ('user__username',)
            label_field = 'user__username'
        
        # Generar datos agrupados
        data = (
            qs.values(*values)
            .annotate(total_tickets=Count('id'), total_pieces=Sum('total_pieces'))
            .order_by()
        )
        
        result = [
            {
                'group': row[label_field] or '',
                'total_tickets': row['total_tickets'] or 0,
                'total_pieces': row['total_pieces'] or 0,
            }
            for row in data
        ]
        
        # Paginación
        total_items = len(result)
        total_pages = (total_items + page_size - 1) // page_size if page_size else 1
        start = (page - 1) * page_size
        end = start + page_size
        paged = result[start:end]
        
        # Totales generales
        totals = qs.aggregate(
            total_tickets=Count('id'),
            total_pieces=Sum('total_pieces')
        )
        totals = {k: totals.get(k) or 0 for k in ['total_tickets', 'total_pieces']}
        
        # Datos diarios opcionales
        daily = None
        if include_daily:
            daily_qs = (
                qs.values('created_at__date')
                .annotate(total_tickets=Count('id'), total_pieces=Sum('total_pieces'))
                .order_by('created_at__date')
            )
            daily = [
                {
                    'date': str(row['created_at__date']),
                    'total_tickets': row['total_tickets'] or 0,
                    'total_pieces': row['total_pieces'] or 0,
                }
                for row in daily_qs
            ]
        
        # Construir respuesta
        payload = {
            'summary': paged,
            'totals': totals,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_items': total_items,
                'total_pages': total_pages,
            },
            'cache_info': {
                'cached_at': timezone.now().isoformat(),
                'cache_key': ReportCacheService._generate_cache_key('summary', {
                    'start_date': start_date,
                    'end_date': end_date,
                    'zone': zone,
                    'draw_type': draw_type,
                    'user': user,
                    'group_by': group_by,
                    'page': page,
                    'page_size': page_size,
                    'include_daily': include_daily
                })
            }
        }
        
        if daily is not None:
            payload['daily'] = daily
            
        return payload
    
    @staticmethod
    def invalidate_cache(pattern: str = "report_*") -> int:
        """
        Invalida el cache de reportes
        
        Args:
            pattern: Patrón para buscar claves a invalidar
            
        Returns:
            Número de claves invalidadas
        """
        # Obtener todas las claves que coincidan con el patrón
        keys = cache.keys(pattern)
        if keys:
            cache.delete_many(keys)
            return len(keys)
        return 0
    
    @staticmethod
    def get_cache_stats() -> Dict[str, Any]:
        """Obtiene estadísticas del cache"""
        try:
            # Intentar obtener información del cache
            cache_info = cache.get('cache_stats', {})
            return {
                'cache_enabled': True,
                'cache_info': cache_info,
                'timestamp': timezone.now().isoformat()
            }
        except Exception as e:
            return {
                'cache_enabled': False,
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
    
    @staticmethod
    def clear_all_reports_cache() -> Dict[str, Any]:
        """Limpia todo el cache de reportes"""
        try:
            deleted_count = ReportCacheService.invalidate_cache("report_*")
            return {
                'success': True,
                'deleted_keys': deleted_count,
                'message': f'Se eliminaron {deleted_count} claves del cache'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Error al limpiar el cache'
            }
