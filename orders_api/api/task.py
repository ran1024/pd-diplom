import logging
import smtplib
from django.conf import settings
from django.core.mail import send_mail

from orders import celery_app
from .models import ConfirmEmailToken, Product, ProductParameter, Category, Parameter


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


def _import_product(product_data, shop_id):
    product = Product(name=product_data['name'],
                      category_id=product_data['category'],
                      model=product_data['model'],
                      external_id=product_data['id'],
                      shop_id=shop_id,
                      quantity=product_data['quantity'],
                      price=product_data['price'],
                      price_rrc=product_data['price_rrc'])
    return product


def _import_parameter(parameter_list, items_dict, prod):
    for key, value in items_dict[prod.external_id].items():
        parameter_list.append(ProductParameter(product_id=prod.id,
                                               parameter_id=key,
                                               value=value))


@celery_app.task
def do_import(data, shop_id):
    for category in data['categories']:
        category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
        category_object.shops.add(shop_id)
        category_object.save()

    Product.objects.filter(shop_id=shop_id).delete()
    product_items = []
    parameter_items = {}
    parameter_list = []
    for item in data['goods']:
        product_items.append(_import_product(item, shop_id))
        parameter_items[item['id']] = {}
        for name, value in item['parameters'].items():
            parameter, _ = Parameter.objects.get_or_create(name=name)
            parameter_items[item['id']].update({parameter.id: value})

    list_of_products = Product.objects.bulk_create(product_items)

    for product in list_of_products:
        _import_parameter(parameter_list, parameter_items, product)

    ProductParameter.objects.bulk_create(parameter_list)
