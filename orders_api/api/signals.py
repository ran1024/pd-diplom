from django.core.mail import EmailMultiAlternatives
from django.dispatch import Signal, receiver
from django.conf import settings

from api.models import ConfirmEmailToken

new_user_registered = Signal(
    providing_args=['user_id'],
)


@receiver(new_user_registered)
def new_user_registered_signal(user_id, **kwargs):
    """
    отправляем письмо с подтрердждением почты
    """
    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user_id)

    msg = EmailMultiAlternatives(
        subject=f"Password Reset Token for {token.user.email}",
        body=token.key,
        to=[token.user.email],
        from_email=settings.EMAIL_HOST_USER,
    )
    msg.send()

