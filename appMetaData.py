from flask import Flask, render_template, request, redirect, url_for
from database import DatabaseConnection
from math import ceil
from controllers.description_controller import DescriptionController
from datetime import datetime, timedelta
import json

app = Flask(__name__)

# Pasar las funciones 'max' y 'min' al contexto de Jinja2
app.jinja_env.globals.update(max=max, min=min)

@app.template_filter('datetime_format')
def datetime_format(value, format="%d/%m/%Y %H:%M"):
    """Filtro para formatear fechas en las plantillas"""
    if value is None:
        return ""
    # Si el valor es string, convertirlo a datetime
    if isinstance(value, str):
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S').strftime(format)
    return value.strftime(format)

@app.context_processor
def inject_quick_stats():
    """Inyecta estadísticas rápidas en todas las plantillas"""
    dashboard = DashboardController()
    return dict(quick_stats=dashboard.get_quick_stats())

class DashboardController:
    def __init__(self):
        self.items_per_page = 6
        self.valid_columns = {
            'id': 'id',
            'sku': 'sku',
            'name': 'name',
            'type_id': 'type_id',
            'status_product_description': 'status_product_description',
            'status_product_meta_description': 'status_product_meta_description',
            'status_product_meta_title': 'status_product_meta_title',
            'status_product_keyword': 'status_product_keyword',
            'created_at': 'created_at',
            'updated_at': 'updated_at'
        }

    def get_products(self, page=1, sort_by='id', order='desc', search=None, status=None):
        db = DatabaseConnection()
        connection = db.connect()
        cursor = connection.cursor(dictionary=True)
        
        try:
            # Validar columna de ordenamiento
            sort_column = self.valid_columns.get(sort_by, 'id')
            order_direction = 'DESC' if order.lower() == 'desc' else 'ASC'
            
            # Construir la consulta base
            query_base = """
                FROM products
                WHERE 1=1
            """
            params = []
            
            # Añadir condición de búsqueda si se proporciona
            if search:
                query_base += " AND (sku LIKE %s OR name LIKE %s)"
                search_term = f"%{search}%"
                params.extend([search_term, search_term])
            
            # Añadir condición de filtro por estado si se proporciona
            if status:
                # Dividir el valor del estado en categoría y estado
                try:
                    category, status_value = status.split('-')
                    # Validar la categoría
                    valid_categories = ['description', 'meta_description', 'meta_title', 'keyword']
                    if category in valid_categories and status_value in ['completed', 'pending']:
                        column_name = f"status_product_{category}"
                        query_base += f" AND {column_name} = %s"
                        params.append(status_value)
                except ValueError:
                    # Si el formato no es correcto, ignorar el filtro
                    pass
            
            # Obtener el total de productos con los filtros aplicados
            count_query = f"SELECT COUNT(*) as total {query_base}"
            cursor.execute(count_query, params)
            total_products = cursor.fetchone()['total']
            total_pages = ceil(total_products / self.items_per_page) if total_products > 0 else 1
            
            # Asegurar que la página está dentro del rango válido
            page = max(1, min(page, total_pages))
            
            # Obtener productos paginados, ordenados y filtrados
            offset = (page - 1) * self.items_per_page
            select_query = f"""
                SELECT id, sku, name, type_id, meta_title, meta_description, meta_keyword,
                       status_product_description, status_product_meta_description,
                       status_product_meta_title, status_product_keyword,
                       created_at, updated_at
                {query_base}
                ORDER BY {sort_column} {order_direction}
                LIMIT %s OFFSET %s
            """
            params.extend([self.items_per_page, offset])
            cursor.execute(select_query, params)
            
            products = cursor.fetchall()
            
            return {
                'products': products,
                'total_pages': total_pages,
                'current_page': page,
                'total_products': total_products,
                'sort_by': sort_by,
                'order': order,
                'search': search,
                'status': status
            }
            
        finally:
            cursor.close()
            db.disconnect()
            
    def get_report_data(self):
        """Obtiene datos para la vista de informes"""
        db = DatabaseConnection()
        connection = db.connect()
        cursor = connection.cursor(dictionary=True)
        
        try:
            # Obtener total de productos
            cursor.execute("SELECT COUNT(*) as total FROM products")
            total_products = cursor.fetchone()['total']
            
            # Obtener productos completados y pendientes para cada categoría
            status_counts = {}
            
            # Categorías a verificar
            categories = [
                'description', 
                'meta_description', 
                'meta_title', 
                'keyword'
            ]
            
            for category in categories:
                # Productos completados
                cursor.execute(f"SELECT COUNT(*) as total FROM products WHERE status_product_{category} = 'completed'")
                completed = cursor.fetchone()['total']
                
                # Productos pendientes
                pending = total_products - completed
                
                # Calcular porcentajes
                completed_percentage = round((completed / total_products) * 100) if total_products > 0 else 0
                pending_percentage = round((pending / total_products) * 100) if total_products > 0 else 0
                
                status_counts[category] = {
                    'completed': completed,
                    'pending': pending,
                    'completed_percentage': completed_percentage,
                    'pending_percentage': pending_percentage
                }
            
            # Obtener último procesado
            cursor.execute("SELECT MAX(updated_at) as last_update FROM products WHERE status_product_description = 'completed'")
            last_update = cursor.fetchone()['last_update']
            
            # Calcular días desde el último procesado
            if last_update:
                last_processed_days = (datetime.now() - last_update).days
            else:
                last_processed_days = 0
                
            # Obtener tipos de productos
            cursor.execute("SELECT type_id, COUNT(*) as count FROM products GROUP BY type_id ORDER BY count DESC")
            types = cursor.fetchall()
            
            type_labels = json.dumps([t['type_id'] for t in types])
            type_counts = json.dumps([t['count'] for t in types])
            
            # Generar datos de tendencia (simulados para este ejemplo)
            # En un caso real, se obtendrían de la base de datos
            trend_dates = []
            completed_trends = {}
            pending_trends = {}
            
            # Inicializar tendencias para cada categoría
            for category in categories:
                completed_trends[category] = []
                pending_trends[category] = []
            
            # Generar datos para los últimos 7 días
            for i in range(6, -1, -1):
                date = datetime.now() - timedelta(days=i)
                trend_dates.append(date.strftime('%d/%m'))
                
                # Simulación de datos - en un caso real se obtendrían de la BD
                for category in categories:
                    completed = status_counts[category]['completed']
                    pending = status_counts[category]['pending']
                    
                    # Simular variación en los datos
                    factor_completed = 0.85 + 0.15 * (7-i) / 7
                    factor_pending = 1 - 0.1 * (7-i) / 7
                    
                    completed_trends[category].append(int(completed * factor_completed))
                    pending_trends[category].append(int(pending * factor_pending))
            
            trend_labels = json.dumps(trend_dates)
            
            # Convertir tendencias a JSON
            completed_trends_json = {}
            pending_trends_json = {}
            
            for category in categories:
                completed_trends_json[category] = json.dumps(completed_trends[category])
                pending_trends_json[category] = json.dumps(pending_trends[category])
            
            return {
                'total_products': total_products,
                'status_counts': status_counts,
                'last_processed_days': last_processed_days,
                'type_labels': type_labels,
                'type_counts': type_counts,
                'trend_labels': trend_labels,
                'completed_trends': completed_trends_json,
                'pending_trends': pending_trends_json,
                'categories': categories
            }
            
        finally:
            cursor.close()
            db.disconnect()

    def get_quick_stats(self):
        """Obtiene estadísticas rápidas para mostrar en el sidebar"""
        db = DatabaseConnection()
        connection = db.connect()
        cursor = connection.cursor(dictionary=True)
        
        try:
            # Obtener total de productos
            cursor.execute("SELECT COUNT(*) as total FROM products")
            total_products = cursor.fetchone()['total']
            
            if total_products == 0:
                return {
                    'completed_percentage': 0,
                    'pending_percentage': 100
                }
            
            # Categorías a verificar
            categories = [
                'description', 
                'meta_description', 
                'meta_title', 
                'keyword'
            ]
            
            # Contar todos los estados posibles (total_products * número de categorías)
            total_states = total_products * len(categories)
            total_completed = 0
            
            # Contar completados en todas las categorías
            for category in categories:
                cursor.execute(f"SELECT COUNT(*) as completed FROM products WHERE status_product_{category} = 'completed'")
                total_completed += cursor.fetchone()['completed']
            
            # Calcular pendientes y porcentajes
            completed_percentage = round((total_completed / total_states) * 100)
            pending_percentage = 100 - completed_percentage
            
            return {
                'completed_percentage': completed_percentage,
                'pending_percentage': pending_percentage
            }
            
        finally:
            cursor.close()
            db.disconnect()

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort', 'id')
    order = request.args.get('order', 'desc')
    search = request.args.get('search', None)
    status = request.args.get('status', None)
    
    dashboard = DashboardController()
    data = dashboard.get_products(page, sort_by, order, search, status)
    return render_template('list_products.html', **data)

@app.route('/reports')
def reports():
    dashboard = DashboardController()
    data = dashboard.get_report_data()
    return render_template('reports.html', **data)

# para que funcione el botton de generar la descripcion de forma manual
@app.route('/process-descriptions')
def process_descriptions():
    controller = DescriptionController()
    controller.process_pending_descriptions()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5017)