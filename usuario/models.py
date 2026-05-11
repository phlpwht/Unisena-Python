from django.db import models
from django.contrib.auth.hashers import make_password


# Create your models here.
class Rol(models.Model):
    nombre_rol = models.CharField(max_length=30)

    def __str__(self):
        return self.nombre_rol


class Usuario(models.Model):
    
    TIPOS_IDENTIFICACION = [
        ('CC', 'Cédula de ciudadanía'),
        ('TI', 'Tarjeta de identidad'),
        ('CE', 'Cedula de extranjeria'),
    ]

    rol = models.ForeignKey(Rol, on_delete=models.CASCADE)

    nombres = models.CharField(max_length=50)
    apellidos = models.CharField(max_length=50)

    correo = models.EmailField(unique=True)

    fecha_nacimiento = models.DateField()

    tipo_identificacion = models.CharField(
        max_length=2,
        choices=TIPOS_IDENTIFICACION
    )    
    num_identificacion = models.CharField(max_length=10, unique=True)    
    password = models.CharField(max_length=255)
    reset_codigo = models.CharField(max_length=6, null=True, blank=True)
    reset_codigo_fecha = models.DateTimeField(null=True, blank=True)
    reset_intentos = models.IntegerField(default=0)
    
    def save(self, *args, **kwargs):

        if not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"