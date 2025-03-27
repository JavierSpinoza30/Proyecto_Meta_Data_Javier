#!/usr/bin/env python
"""
Servicio de moderación automática de reviews en segundo plano.
Este script ejecuta el controlador de reviews que revisa continuamente
las reviews pendientes y las evalúa usando IA para su aprobación automática.
"""

import os
import sys
import time
import signal
import argparse
import logging
from datetime import datetime
from controllers.review_controller import ReviewController

# Variable global para almacenar la instancia del controlador
controller = None

# Obtener el logger
logger = logging.getLogger('ReviewDaemon')

def signal_handler(sig, frame):
    """Maneja señales de terminación para detener el servicio correctamente"""
    global controller
    if controller:
        logger.info("Deteniendo servicio de moderación de reviews...")
        print("\n🛑 Deteniendo servicio de moderación de reviews...")
        controller.stop()
    sys.exit(0)

def start_service():
    """Inicia el servicio de moderación de reviews"""
    global controller
    
    logger.info(f"Iniciando servicio de moderación automática de reviews - {datetime.now()}")
    print(f"🚀 Iniciando servicio de moderación automática de reviews - {datetime.now()}")
    
    # Registrar manejadores de señal para terminar correctamente
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # kill
    
    # Iniciar controlador
    controller = ReviewController()
    controller.start()
    
    try:
        # Mantener el proceso en ejecución
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        controller.stop()
        logger.info("Servicio detenido por el usuario")
        print("👋 Servicio detenido por el usuario")

def run_once():
    """Ejecuta un solo ciclo de procesamiento de reviews"""
    logger.info("Ejecutando procesamiento único de reviews")
    controller = ReviewController()
    controller.run_once()

if __name__ == "__main__":
    # Configurar logging para este script si no se ejecuta desde el controlador
    if not logging.getLogger().handlers:
        # Crear directorio de logs si no existe
        log_dir = os.path.join(os.getcwd(), 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Configurar handler
        from logging.handlers import RotatingFileHandler
        handler = RotatingFileHandler(
            os.path.join(log_dir, 'log_reviews.txt'),
            maxBytes=10*1024*1024,
            backupCount=5
        )
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Configurar logger raíz
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(handler)
        
        # Configurar logger para este script
        logger.setLevel(logging.INFO)
    
    parser = argparse.ArgumentParser(description='Servicio de moderación automática de reviews')
    parser.add_argument('--once', action='store_true', help='Ejecutar un solo ciclo de procesamiento y terminar')
    
    args = parser.parse_args()
    
    if args.once:
        run_once()
    else:
        start_service() 