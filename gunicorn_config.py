"""
Configuración de Gunicorn para producción.
"""
import multiprocessing

# Dirección y puerto de escucha
bind = "0.0.0.0:8000"

# Trabajadores (Workers)
# Fórmula recomendada: (2 x CPUs) + 1
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'

# Timeouts
timeout = 120
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Nombre del proceso
proc_name = 'edu_polo'
