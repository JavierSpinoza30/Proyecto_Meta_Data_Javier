# Sistema de Generación de MetaData SEO Rutavity

Este proyecto permite generar y gestionar metadatos SEO para productos de Magento, incluyendo descripciones, meta títulos, meta keywords y un sistema automático de moderación de reviews mediante inteligencia artificial.

## Características Principales

- Generación de meta títulos optimizados para SEO
- Generación de meta descripciones y palabras clave
- Generación de descripciones completas de productos
- Moderación automática de reviews de productos mediante IA
- Sincronización con Magento y SAP HANA

## Requisitos

- Python 3.8+
- MySQL/MariaDB
- Acceso a la API de Magento
- Cuenta de OpenAI con clave API
- Dependencias en `requirements.txt`

## Configuración

1. Clone el repositorio en su servidor
2. Copie `.env.example` a `.env` y configure sus credenciales:
   ```bash
   cp .env.example .env
   nano .env
   ```
3. Instale las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Estructura del Proyecto

- `main.py`: Punto de entrada principal
- `appMetaData.py`: Aplicación web Flask para gestión y reportes
- `controllers/`: Controladores para diferentes funcionalidades
- `services/`: Servicios que interactúan con APIs y bases de datos
- `templates/`: Plantillas para la interfaz web

## Servicio de Moderación Automática de Reviews

El sistema incluye un servicio para moderar automáticamente las reviews de productos utilizando IA:

- Evalúa reviews pendientes (estado 2) 
- Aprueba automáticamente (estado 1) o envía a revisión humana (estado 4)
- Funciona en tiempo real, verificando nuevas reviews cada minuto

### Ejecutar el Servicio de Reviews

Puede ejecutar el servicio de reviews de dos formas:

#### 1. Como un servicio independiente:

```bash
python review_daemon.py
```

Para ejecutar una sola vez, procesando todas las reviews pendientes:

```bash
python review_daemon.py --once
```

### Configuración como Servicio Systemd (Recomendado)

Para mantener el servicio de reviews funcionando permanentemente:

1. Crear archivo de servicio systemd:

```bash
sudo nano /etc/systemd/system/review-moderator.service
```

2. Añadir la siguiente configuración (ajuste las rutas según su sistema):

```ini
[Unit]
Description=Servicio de Moderación de Reviews Rutavity
After=network.target

[Service]
User=user-magento
WorkingDirectory=/var/www/html/GenerarMetaDataSeoRutavity
ExecStart=/usr/bin/python3 /var/www/html/GenerarMetaDataSeoRutavity/review_daemon.py
Restart=always
RestartSec=10
StandardOutput=null
StandardError=null
SyslogIdentifier=review-moderator
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

> **IMPORTANTE**: Cambie `User=user-magento` por el usuario que tenga permisos de acceso al directorio del proyecto.

3. Habilitar y arrancar el servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable review-moderator
sudo systemctl start review-moderator
```

### Gestión del Servicio de Reviews

A continuación se detallan los comandos para gestionar el servicio de moderación de reviews:

#### Ver el estado del servicio
```bash
sudo systemctl status review-moderator
```
Este comando muestra si el servicio está activo (running), detenido (stopped) o si ha tenido errores.

#### Iniciar el servicio
```bash
sudo systemctl start review-moderator
```

#### Detener el servicio
```bash
sudo systemctl stop review-moderator
```

#### Reiniciar el servicio
```bash
sudo systemctl restart review-moderator
```

#### Recargar la configuración sin reiniciar
```bash
sudo systemctl reload review-moderator
```

#### Ver los logs del servicio en tiempo real
```bash
# Ver logs generales del servicio
sudo journalctl -u review-moderator -f

# Ver logs específicos de la aplicación
tail -f logs/log_reviews.txt
```

#### Habilitar el servicio para que inicie automáticamente
```bash
sudo systemctl enable review-moderator
```

#### Deshabilitar el inicio automático
```bash
sudo systemctl disable review-moderator
```

#### Verificar si existen errores en el servicio
```bash
sudo systemctl --failed | grep review-moderator
```

> **Nota**: Después de modificar el archivo de configuración del servicio (.service), siempre debe ejecutar `sudo systemctl daemon-reload` para que systemd reconozca los cambios.``

### Configuración de Logs

Los logs del servicio se almacenan exclusivamente en el directorio `logs/` del proyecto:
- `logs/log_reviews.txt` - archivo principal de logs
- `logs/log_reviews.txt.1` a `logs/log_reviews.txt.5` - archivos de rotación

El sistema implementa rotación automática de logs (máximo 5 archivos de 10MB cada uno) para evitar llenar el espacio en disco.

> **IMPORTANTE**: Para asegurar que los logs se almacenen únicamente en el archivo del proyecto y no en el journal de systemd, la configuración del servicio incluye:
> ```ini
> StandardOutput=null
> StandardError=null
> ```
> Esto garantiza que toda la salida sea manejada internamente por la aplicación y dirigida a los archivos de log del proyecto.

## Flujo de trabajo completo
El demonio inicia e inicializa el controlador de reviews.
Cada minuto, el controlador consulta la API de Magento para obtener reviews pendientes.
Para cada review pendiente:
Extrae su contenido (título, detalles, autor)
Envía este contenido a OpenAI para evaluarlo
Basado en la respuesta de la IA, decide aprobar automáticamente o enviar a revisión humana
Actualiza el estado de la review en Magento mediante su API
Todo el proceso se registra en los archivos de log para revisión posterior.
El servicio se mantiene en ejecución indefinidamente, reiniciándose automáticamente si ocurre algún error.

## Licencia
Este proyecto es propiedad de Rutavity. Todos los derechos reservados.