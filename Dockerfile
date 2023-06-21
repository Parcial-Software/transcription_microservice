# Usar una imagen base de Python
FROM python:3.9

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar los archivos de la aplicación en el contenedor
COPY . /app

# Instalar las dependencias del proyecto
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto en el contenedor
EXPOSE 8001

# Ejecutar la aplicación Flask con Gunicorn cuando se inicie el contenedor
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8001"]