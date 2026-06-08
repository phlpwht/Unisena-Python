from django.db import migrations

def populate_roles(apps, schema_editor):
    # Obtenemos el modelo 'Rol' de la app 'usuario'
    Rol = apps.get_model('usuario', 'Rol')
    roles = ['Cliente', 'Administrador', 'Vendedor']
    
    for nombre_rol in roles:
        Rol.objects.get_or_create(nombre_rol=nombre_rol)

class Migration(migrations.Migration):
    dependencies = [
        ('usuario', '0012_alter_usuario_num_identificacion'),
    ]

    operations = [
        migrations.RunPython(populate_roles),
    ]