from django.utils.timezone import now
from django.shortcuts import get_object_or_404

def custom_user_display(user):
    return user.last_name

def _get_user_block_status(request):
    from .models import Usuario  # Importación local para evitar circularidad
    usuario_id = request.session.get("usuario_id")
    usuario_bloqueado = False
    msg_bloqueo = ""
    user_obj = None
    if usuario_id:
        user_obj = get_object_or_404(Usuario, id=usuario_id)
        if user_obj.bloqueado_hasta and user_obj.bloqueado_hasta <= now() and not user_obj.pendiente_aceptar_politicas:
            user_obj.bloqueado_hasta = None
            user_obj.pendiente_aceptar_politicas = True
            user_obj.save()
        if (user_obj.bloqueado_hasta and user_obj.bloqueado_hasta > now()) or user_obj.pendiente_aceptar_politicas:
            usuario_bloqueado = True
            msg_bloqueo = "politicas" if user_obj.pendiente_aceptar_politicas else f"Tu cuenta está suspendida hasta el {user_obj.bloqueado_hasta.strftime('%d/%m/%Y %H:%M')}. Motivo: {user_obj.motivo_bloqueo or 'Incumplimiento de normas'}"
    return usuario_bloqueado, msg_bloqueo, user_obj