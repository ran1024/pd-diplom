import logging
import smtplib

# from celery.backends.database import retry
from orders import celery_app
from api.models import ConfirmEmailToken
from django.conf import settings
from django.core.mail import send_mail


@celery_app.task(bind=True, default_retry_delay=3 * 60, max_retries=5)
def send_verification_email(self, user_id):
    try:
        token = ConfirmEmailToken.objects.select_related('user').get(user_id=user_id)
    except ConfirmEmailToken.DoesNotExist:
        logging.warning(f'Не существует пользователя с id: {user_id} или токена для этого пользователя.')
    else:
        try:
            send_mail(
                subject=f'Token для подтверждения регистрации пользователя {token[0].user.email}',
                message=token[0].key,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[token[0].user.email],
                fail_silently=False
            )
        except smtplib.SMTPException as ex:
            self.retry(exc=ex)


@celery_app.task(bind=True, default_retry_delay=3 * 60, max_retries=5)
def send_change_order_email(self, user_email, order_id):
    try:
        send_mail(
            subject=f'Обновление статуса заказа',
            message=f'Заказ номер {order_id} сформирован.',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user_email],
            fail_silently=False
        )
    except smtplib.SMTPException as ex:
        self.retry(exc=ex)
