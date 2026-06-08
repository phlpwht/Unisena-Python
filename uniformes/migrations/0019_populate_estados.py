from django.db import migrations

def populate_estados(apps, schema_editor):
    EstadoPedido = apps.get_model('uniformes', 'EstadoPedido')
    # Usamos las llaves definidas en ESTADO_CHOICES de tu modelo
    estados = [
        'PENDIENTE',
        'En Proceso',
        'COMPLETADO',
        'CANCELADO'
    ]
    for estado in estados:
        # get_or_create evita errores si el estado ya existe
        EstadoPedido.objects.get_or_create(estado_pedido=estado)

class Migration(migrations.Migration):
    dependencies = [
        ('uniformes', '0018_alter_prendas_stock'),  # Apuntamos a la última existente para unir las ramas
    ]

    operations = [
        migrations.RunPython(populate_estados),
    ]