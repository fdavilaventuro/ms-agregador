from flask import Flask, jsonify
from flask_restx import Api, Resource, fields
import requests
import os
from datetime import datetime

app = Flask(__name__)

# Configuración con los endpoints del LB
MS_INSCRIPCIONES = os.getenv('MS_INSCRIPCIONES', 'http://LB-Microservicios-34846879.us-east-1.elb.amazonaws.com/inscripciones')
MS_CURSOS = os.getenv('MS_CURSOS', 'http://LB-Microservicios-34846879.us-east-1.elb.amazonaws.com/cursos')
MS_ESTUDIANTES = os.getenv('MS_ESTUDIANTES', 'http://LB-Microservicios-34846879.us-east-1.elb.amazonaws.com/estudiantes')

# Configuración de Swagger con Flask-RESTX
api = Api(app, 
          version='1.0', 
          title='Microservicio Agregador API',
          description='API agregadora para microservicios de estudiantes, cursos e inscripciones',
          doc='/docs',
          default='Agregador',
          default_label='Endpoints principales del agregador')

# Modelos para Swagger basados en tus tipos de datos
progreso_model = api.model('Progreso', {
    'porcentaje': fields.Float(description='Porcentaje de completado'),
    'leccionesCompletadas': fields.List(fields.Integer, description='IDs de lecciones completadas'),
    'ultimaLeccionId': fields.Integer(description='ID de la última lección vista')
})

inscripcion_model = api.model('Inscripcion', {
    'estudianteId': fields.String(description='ID del estudiante (UUID)'),
    'cursoId': fields.Integer(description='ID del curso'),
    'estado': fields.String(description='Estado: activa|completada|cancelada'),
    'metodoPago': fields.String(description='Método de pago utilizado'),
    'monto': fields.Float(description='Monto pagado'),
    'progreso': fields.Nested(progreso_model, description='Información de progreso'),
    'fechaInscripcion': fields.String(description='Fecha de inscripción')
})

estudiante_model = api.model('Estudiante', {
    'id': fields.String(description='ID único del estudiante'),
    'nombres': fields.String(description='Nombres del estudiante'),
    'apellidos': fields.String(description='Apellidos del estudiante'),
    'email': fields.String(description='Email del estudiante'),
    'telefono': fields.String(description='Teléfono del estudiante'),
    'pais': fields.String(description='País del estudiante'),
    'fechaCreacion': fields.String(description='Fecha de creación del registro'),
    'fechaActualizacion': fields.String(description='Fecha de última actualización')
})

curso_model = api.model('Curso', {
    'id': fields.Integer(description='ID del curso'),
    'slug': fields.String(description='Slug del curso'),
    'titulo': fields.String(description='Título del curso'),
    'descripcion': fields.String(description='Descripción del curso'),
    'nivel': fields.String(description='Nivel del curso'),
    'estado': fields.String(description='Estado del curso'),
    'duracion_min': fields.Integer(description='Duración en minutos'),
    'instructores': fields.List(fields.Raw, description='Lista de instructores')
})

leccion_model = api.model('Leccion', {
    'id': fields.Integer(description='ID de la lección'),
    'curso_id': fields.Integer(description='ID del curso'),
    'titulo': fields.String(description='Título de la lección'),
    'orden': fields.Integer(description='Orden de la lección'),
    'contenido_url': fields.String(description='URL del contenido'),
    'duracion_min': fields.Integer(description='Duración en minutos')
})

# Función helper para requests HTTP
def hacer_request(url, method='GET', data=None):
    """Función helper para hacer requests HTTP a los microservicios"""
    try:
        if method.upper() == 'GET':
            response = requests.get(url, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, timeout=10)
        elif method.upper() == 'PATCH':
            response = requests.patch(url, json=data, timeout=10)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, timeout=10)
        
        response.raise_for_status()
        return response.json() if response.content else {}
    except requests.exceptions.RequestException as e:
        # ⚠️ siempre devuelve un dict, nunca una tupla
        return {'error': f'Error conectando con el servicio: {str(e)}'}

### ENDPOINTS DEL AGREGADOR ###

@api.route('/dashboard/estadisticas')
class DashboardEstadisticas(Resource):
    @api.doc(description='Obtener estadísticas generales del sistema')
    @api.response(200, 'Estadísticas obtenidas correctamente')
    def get(self):
        """Estadísticas generales del sistema"""
        try:
            # ---------------- ESTUDIANTES ----------------
            estudiantes_resp = hacer_request(f"{MS_ESTUDIANTES}")
            if 'error' in estudiantes_resp:
                total_estudiantes = 0
            elif isinstance(estudiantes_resp, dict) and 'content' in estudiantes_resp:
                total_estudiantes = estudiantes_resp.get('totalElements', 0)
            else:
                total_estudiantes = len(estudiantes_resp) if isinstance(estudiantes_resp, list) else 0

            # ---------------- CURSOS ----------------
            try:
                cursos_resp = hacer_request(f"{MS_CURSOS}/count")
                if isinstance(cursos_resp, dict) and 'count' in cursos_resp:
                    total_cursos = cursos_resp['count']
                else:
                    total_cursos = 0
            except:
                total_cursos = 0

            # ---------------- INSCRIPCIONES ----------------
            inscripciones_resp = hacer_request(f"{MS_INSCRIPCIONES}")
            if 'error' in inscripciones_resp:
                total_inscripciones = 0
                inscripciones_list = []
            elif isinstance(inscripciones_resp, dict) and 'content' in inscripciones_resp:
                total_inscripciones = len(inscripciones_resp.get('content', []))
                inscripciones_list = inscripciones_resp.get('content', [])
            else:
                total_inscripciones = len(inscripciones_resp) if isinstance(inscripciones_resp, list) else 0
                inscripciones_list = inscripciones_resp if isinstance(inscripciones_resp, list) else []

            # ---------------- INSCRIPCIONES ACTIVAS ----------------
            inscripciones_activas = sum(1 for insc in inscripciones_list 
                                        if isinstance(insc, dict) and insc.get('estado') == 'activa')

            return {
                'total_estudiantes': total_estudiantes,
                'total_cursos': total_cursos,
                'total_inscripciones': total_inscripciones,
                'inscripciones_activas': inscripciones_activas,
                'status': 'success'
            }

        except Exception as e:
            return {'error': str(e), 'status': 'error'}, 500

@api.route('/estudiantes/<string:estudiante_id>/detalles-completos')
class EstudianteDetallesCompletos(Resource):
    @api.doc(description='Obtener detalles completos de un estudiante con sus cursos y progreso')
    @api.response(200, 'Detalles obtenidos correctamente', estudiante_model)
    @api.response(404, 'Estudiante no encontrado')
    def get(self, estudiante_id):
        """Detalles completos de un estudiante con cursos inscritos"""
        try:
            # Obtener datos del estudiante
            estudiante = hacer_request(f"{MS_ESTUDIANTES}/{estudiante_id}")
            if isinstance(estudiante, tuple):
                return estudiante
            
            # Obtener todas las inscripciones
            inscripciones = hacer_request(f"{MS_INSCRIPCIONES}")
            if isinstance(inscripciones, tuple):
                return inscripciones
            
            # Filtrar inscripciones del estudiante
            inscripciones_estudiante = [
                insc for insc in inscripciones 
                if isinstance(insc, dict) and insc.get('estudianteId') == estudiante_id
            ]
            
            # Obtener detalles de cada curso
            cursos_detallados = []
            for insc in inscripciones_estudiante:
                curso_id = insc.get('cursoId')
                if curso_id:
                    curso = hacer_request(f"{MS_CURSOS}/{curso_id}")
                    if not isinstance(curso, tuple):
                        curso_detallado = {
                            **curso,
                            'progreso': insc.get('progreso', {}),
                            'estado_inscripcion': insc.get('estado'),
                            'fecha_inscripcion': insc.get('fechaInscripcion')
                        }
                        cursos_detallados.append(curso_detallado)
            
            return {
                'estudiante': estudiante,
                'cursos_inscritos': cursos_detallados,
                'total_cursos': len(cursos_detallados),
                'cursos_activos': sum(1 for curso in cursos_detallados 
                                    if curso.get('estado_inscripcion') == 'activa'),
                'cursos_completados': sum(1 for curso in cursos_detallados 
                                        if curso.get('estado_inscripcion') == 'completada'),
                'status': 'success'
            }
        except Exception as e:
            return {'error': str(e), 'status': 'error'}, 500

@api.route('/cursos/<int:curso_id>/informacion-completa')
class CursoInformacionCompleta(Resource):
    @api.doc(description='Obtener información completa de un curso con estudiantes inscritos y lecciones')
    @api.response(200, 'Información del curso obtenida correctamente')
    @api.response(404, 'Curso no encontrado')
    def get(self, curso_id):
        """Información completa de un curso"""
        try:
            # Obtener datos del curso
            curso = hacer_request(f"{MS_CURSOS}/{curso_id}")
            if isinstance(curso, tuple):
                return curso
            
            # Obtener lecciones del curso
            lecciones = hacer_request(f"{MS_CURSOS}/{curso_id}/lecciones")
            if isinstance(lecciones, tuple):
                lecciones = []
            
            # Obtener todas las inscripciones y estudiantes
            inscripciones = hacer_request(f"{MS_INSCRIPCIONES}")
            estudiantes_resp = hacer_request(f"{MS_ESTUDIANTES}")
            
            if isinstance(inscripciones, tuple):
                inscripciones = []
            
            # Procesar estudiantes (puede venir paginado)
            if isinstance(estudiantes_resp, dict) and 'content' in estudiantes_resp:
                todos_estudiantes = estudiantes_resp.get('content', [])
            else:
                todos_estudiantes = estudiantes_resp if isinstance(estudiantes_resp, list) else []
            
            # Crear mapa de estudiantes para búsqueda rápida
            mapa_estudiantes = {est['id']: est for est in todos_estudiantes if isinstance(est, dict)}
            
            # Filtrar estudiantes inscritos en este curso
            estudiantes_inscritos = []
            for insc in inscripciones:
                if isinstance(insc, dict) and insc.get('cursoId') == curso_id:
                    estudiante_id = insc.get('estudianteId')
                    if estudiante_id in mapa_estudiantes:
                        estudiante_con_progreso = {
                            **mapa_estudiantes[estudiante_id],
                            'progreso': insc.get('progreso', {}),
                            'estado_inscripcion': insc.get('estado'),
                            'fecha_inscripcion': insc.get('fechaInscripcion')
                        }
                        estudiantes_inscritos.append(estudiante_con_progreso)
            
            # Calcular estadísticas de progreso
            progresos = [est['progreso'].get('porcentaje', 0) 
                        for est in estudiantes_inscritos 
                        if est.get('progreso')]
            progreso_promedio = sum(progresos) / len(progresos) if progresos else 0
            
            return {
                'curso': curso,
                'lecciones': lecciones,
                'estudiantes_inscritos': estudiantes_inscritos,
                'estadisticas': {
                    'total_estudiantes': len(estudiantes_inscritos),
                    'total_lecciones': len(lecciones),
                    'progreso_promedio': round(progreso_promedio, 2),
                    'estudiantes_activos': sum(1 for est in estudiantes_inscritos 
                                             if est.get('estado_inscripcion') == 'activa')
                },
                'status': 'success'
            }
        except Exception as e:
            return {'error': str(e), 'status': 'error'}, 500

@api.route('/inscripciones/estadisticas-progreso')
class EstadisticasProgreso(Resource):
    @api.doc(description='Obtener estadísticas de progreso de todas las inscripciones')
    @api.response(200, 'Estadísticas de progreso obtenidas correctamente')
    def get(self):
        """Estadísticas de progreso general"""
        try:
            inscripciones = hacer_request(f"{MS_INSCRIPCIONES}")
            if isinstance(inscripciones, tuple):
                return inscripciones
            
            if not isinstance(inscripciones, list):
                return {'error': 'Formato de respuesta inválido', 'status': 'error'}, 500
            
            # Calcular estadísticas
            progresos = []
            estados = {}
            metodos_pago = {}
            
            for insc in inscripciones:
                if isinstance(insc, dict):
                    # Progreso
                    progreso = insc.get('progreso', {})
                    if isinstance(progreso, dict):
                        porcentaje = progreso.get('porcentaje', 0)
                        progresos.append(porcentaje)
                    
                    # Conteo por estado
                    estado = insc.get('estado', 'desconocido')
                    estados[estado] = estados.get(estado, 0) + 1
                    
                    # Conteo por método de pago
                    metodo = insc.get('metodoPago', 'desconocido')
                    metodos_pago[metodo] = metodos_pago.get(metodo, 0) + 1
            
            return {
                'estadisticas_progreso': {
                    'promedio': sum(progresos) / len(progresos) if progresos else 0,
                    'maximo': max(progresos) if progresos else 0,
                    'minimo': min(progresos) if progresos else 0,
                    'distribucion': {
                        '0-25%': sum(1 for p in progresos if 0 <= p < 25),
                        '25-50%': sum(1 for p in progresos if 25 <= p < 50),
                        '50-75%': sum(1 for p in progresos if 50 <= p < 75),
                        '75-99%': sum(1 for p in progresos if 75 <= p < 100),
                        '100%': sum(1 for p in progresos if p >= 100)
                    }
                },
                'estados_inscripciones': estados,
                'metodos_pago': metodos_pago,
                'total_inscripciones': len(inscripciones),
                'status': 'success'
            }
        except Exception as e:
            return {'error': str(e), 'status': 'error'}, 500

@api.route('/cursos/populares')
class CursosPopulares(Resource):
    @api.doc(description='Obtener los cursos más populares por número de inscripciones')
    @api.response(200, 'Cursos populares obtenidos correctamente')
    def get(self):
        """Cursos más populares por número de inscripciones"""
        try:
            cursos = hacer_request(f"{MS_CURSOS}")
            inscripciones = hacer_request(f"{MS_INSCRIPCIONES}")
            
            if isinstance(cursos, tuple):
                return cursos
            if isinstance(inscripciones, tuple):
                return inscripciones
            
            # Contar inscripciones por curso
            contador_inscripciones = {}
            for insc in inscripciones:
                if isinstance(insc, dict):
                    curso_id = insc.get('cursoId')
                    if curso_id is not None:
                        contador_inscripciones[curso_id] = contador_inscripciones.get(curso_id, 0) + 1
            
            # Combinar información de cursos con conteo de inscripciones
            cursos_populares = []
            for curso in cursos:
                if isinstance(curso, dict):
                    curso_id = curso.get('id')
                    cursos_populares.append({
                        **curso,
                        'total_inscripciones': contador_inscripciones.get(curso_id, 0),
                        'inscripciones_activas': sum(1 for insc in inscripciones 
                                                   if isinstance(insc, dict) and 
                                                   insc.get('cursoId') == curso_id and 
                                                   insc.get('estado') == 'activa')
                    })
            
            # Ordenar por popularidad
            cursos_populares.sort(key=lambda x: x['total_inscripciones'], reverse=True)
            
            return {
                'cursos_populares': cursos_populares[:10],  # Top 10
                'status': 'success'
            }
        except Exception as e:
            return {'error': str(e), 'status': 'error'}, 500

@api.route('/health')
class HealthCheck(Resource):
    @api.doc(description='Health check del agregador y todos los microservicios')
    def get(self):
        """Health check completo del sistema"""
        servicios = {}
        
        # Verificar salud de cada microservicio
        try:
            servicios['ms_inscripciones'] = hacer_request(f"{MS_INSCRIPCIONES}")
        except:
            servicios['ms_inscripciones'] = 'error'
        
        try:
            servicios['ms_cursos'] = hacer_request(f"{MS_CURSOS}")
        except:
            servicios['ms_cursos'] = 'error'
        
        try:
            # Si estudiantes no tiene health endpoint, usamos un endpoint básico
            servicios['ms_estudiantes'] = hacer_request(f"{MS_ESTUDIANTES}")
            if servicios['ms_estudiantes'] and not isinstance(servicios['ms_estudiantes'], tuple):
                servicios['ms_estudiantes'] = 'healthy'
            else:
                servicios['ms_estudiantes'] = 'error'
        except:
            servicios['ms_estudiantes'] = 'error'
        
        status = 'healthy' if all(
            serv != 'error' for serv in servicios.values()
        ) else 'degraded'
        
        return {
            'status': status,
            'servicios': servicios,
            'timestamp': datetime.now().isoformat()
        }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)