from services.review_service import ReviewService
import time
import threading
import queue
import logging
from datetime import datetime
import os

# Configurar logging con rotación de archivos
from logging.handlers import RotatingFileHandler

# Crear directorio de logs si no existe
log_dir = os.path.join(os.getcwd(), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configurar logging
log_file = os.path.join(log_dir, 'log_reviews.txt')

# Configurar handler con rotación de archivos (máximo 5 archivos de 4MB cada uno)
handler = RotatingFileHandler(
    log_file,
    maxBytes=4*1024*1024,  # 4 MB
    backupCount=5
)

# Configurar el formato del log
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Configurar logger
logger = logging.getLogger('ReviewController')
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Redirigir los prints a logging
import builtins
original_print = builtins.print

def print_to_log(*args, **kwargs):
    # Convertir args a string y pasarlo al log
    message = ' '.join(str(arg) for arg in args)
    logger.info(message)
    # También mostrar en consola si se ejecuta interactivamente
    if os.isatty(0):
        original_print(*args, **kwargs)

# Reemplazar la función print con nuestra versión
builtins.print = print_to_log

class ReviewController:
    def __init__(self):
        self.review_service = ReviewService()
        self.processing_queue = queue.Queue()
        self.is_running = False
        self.worker_thread = None
        
    def add_to_queue(self, review_id):
        """Añade una review a la cola de procesamiento"""
        self.processing_queue.put(review_id)
        logger.info(f"Review #{review_id} añadida a la cola de procesamiento")
        
    def process_queue(self):
        """Procesa las reviews en la cola"""
        while self.is_running:
            try:
                # Verificar si hay elementos en la cola
                if not self.processing_queue.empty():
                    review_id = self.processing_queue.get()
                    logger.info(f"Procesando review #{review_id} desde la cola")
                    
                    # Aquí podríamos procesar reviews individuales si tuviéramos una API para ello
                    # Por ahora, dejamos que process_pending_reviews maneje todas las pendientes
                    
                    self.processing_queue.task_done()
                
                # Procesar todas las reviews pendientes
                logger.info("Verificando reviews pendientes...")
                self.review_service.process_pending_reviews()
                
                # Esperar 60 segundos antes de la próxima verificación
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error en el procesamiento de la cola: {str(e)}")
                time.sleep(30)  # Esperar un poco antes de reintentar si hay error
                
    def start(self):
        """Inicia el procesamiento en segundo plano"""
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self.process_queue)
            self.worker_thread.daemon = True
            self.worker_thread.start()
            logger.info(f"Servicio de procesamiento de reviews iniciado - {datetime.now()}")
            print(f"✅ Servicio de procesamiento de reviews iniciado - {datetime.now()}")
            
    def stop(self):
        """Detiene el procesamiento en segundo plano"""
        if self.is_running:
            self.is_running = False
            if self.worker_thread:
                self.worker_thread.join(timeout=2)
            logger.info(f"Servicio de procesamiento de reviews detenido - {datetime.now()}")
            print(f"✅ Servicio de procesamiento de reviews detenido - {datetime.now()}")
            
    def run_once(self):
        """Ejecuta un solo ciclo de procesamiento para revisión manual"""
        try:
            logger.info("Ejecutando procesamiento manual de reviews pendientes")
            print("🔄 Procesando reviews pendientes...")
            self.review_service.process_pending_reviews()
            print("✅ Procesamiento completado")
        except Exception as e:
            logger.error(f"Error en procesamiento manual: {str(e)}")
            print(f"❌ Error: {str(e)}")
            
# Para pruebas
if __name__ == "__main__":
    controller = ReviewController()
    controller.start()
    
    try:
        # Mantener el script en ejecución
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        controller.stop()
        print("👋 Servicio detenido por el usuario") 