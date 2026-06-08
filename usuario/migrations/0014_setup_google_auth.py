from django.db import migrations
import os

def setup_google_social_app(apps, schema_editor):
    # 1. Configurar el Sitio
    Site = apps.get_model('sites', 'Site')
    # Actualizamos el sitio por defecto (ID 1)
    site, created = Site.objects.get_or_create(id=1)
    # Usamos strip para limpiar posibles comillas o espacios accidentales
    domain = os.environ.get('SITE_DOMAIN', '127.0.0.1:8000').strip("'").strip('"').strip()
    site.domain = domain
    site.name = domain
    site.save()

    # 2. Configurar la Social App (requiere django-allauth)
    SocialApp = apps.get_model('socialaccount', 'SocialApp')
    
    client_id = os.environ.get('GOOGLE_CLIENT_ID', '').strip("'").strip('"').strip()
    secret = os.environ.get('GOOGLE_SECRET_KEY', '').strip("'").strip('"').strip()

    app, created = SocialApp.objects.update_or_create(
        provider='google', 
        defaults={
            'name': 'Google Auth',
            'client_id': client_id or 'cambiame-en-el-.env',
            'secret': secret or 'cambiame-en-el-.env',
        }
    )

    # Vincular la app al sitio
    app.sites.add(site)

class Migration(migrations.Migration):
    dependencies = [
        ('usuario', '0013_populate_roles'), # O la última que tengas
        ('sites', '0001_initial'),
        ('socialaccount', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(setup_google_social_app),
    ]
