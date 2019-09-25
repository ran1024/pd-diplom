from distutils.util import strtobool

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import URLValidator
from django.db import IntegrityError
from django.db.models import Q, Sum, Prefetch
from requests import get
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from ujson import loads as load_json
from yaml import load as load_yaml, Loader

from api.serializers import UserSerializer, ContactSerializer, ShopSerializer, CategorySerializer, \
    ProductSerializer, OrderItemSerializer, OrderSerializer, OrderModifySerializer
from api.models import ConfirmEmailToken, Contact, Shop, Category, Product, Parameter, ProductParameter, \
    Order, OrderItem
from .task import send_verification_email, send_change_order_email, do_import


class RegisterAccount(APIView):
    """
    Для регистрации покупателей
    """
    def post(self, request, *args, **kwargs):
        # проверяем обязательные аргументы
        if {'first_name', 'last_name', 'email', 'password', 'company', 'position'}.issubset(request.data):
            # проверяем пароль на сложность
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                return Response({'status': False, 'error': {'password': password_error}},
                                status=status.HTTP_403_FORBIDDEN)
            else:
                # проверяем данные для уникальности имени пользователя
                request.data._mutable = True
                request.data.update({})
                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
                    user = user_serializer.save()
                    user.set_password(request.data['password'])
                    user.save()
                    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user.id)
                    # посылаем письмо с токеном для верификации (с помощью Celery)
                    send_verification_email.delay(user.id)
                    return Response({'status': True})
                else:
                    return Response({'status': False, 'error': user_serializer.errors},
                                    status=status.HTTP_403_FORBIDDEN)
        return Response({'status': False, 'error': 'Не указаны все необходимые аргументы'},
                        status=status.HTTP_400_BAD_REQUEST)


class ConfirmAccount(APIView):
    """
    Класс для подтверждения почтового адреса
    """
    def post(self, request, *args, **kwargs):
        # проверяем обязательные аргументы
        if {'email', 'token'}.issubset(request.data):

            token = ConfirmEmailToken.objects.filter(user__email=request.data['email'],
                                                     key=request.data['token']).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return Response({'status': True})
            else:
                return Response({'status': False, 'error': 'Неправильно указан токен или email'},
                                status=status.HTTP_403_FORBIDDEN)
        return Response({'status': False, 'error': 'Не указаны все необходимые аргументы'},
                        status=status.HTTP_400_BAD_REQUEST)


class LoginAccount(APIView):
    """
    Класс для авторизации пользователей
    """
    def post(self, request, *args, **kwargs):
        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['email'], password=request.data['password'])

            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)

                    return Response({'status': True, 'token': token.key})

            return Response({'status': False, 'error': 'Не удалось авторизовать'}, status=status.HTTP_403_FORBIDDEN)

        return Response({'status': False, 'error': 'Не указаны все необходимые аргументы'},
                        status=status.HTTP_400_BAD_REQUEST)


class AccountDetails(APIView):
    """
    Класс для работы данными пользователя
    """
    # Возвращает все данные пользователя включая все контакты.
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'status': False, 'error': 'Login required'}, status=status.HTTP_403_FORBIDDEN)

        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    # Изменяем данные пользователя.
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'status': False, 'error': 'Login required'}, status=status.HTTP_403_FORBIDDEN)

        # Если есть пароль, проверяем его и сохраняем.
        if 'password' in request.data:
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                return Response({'status': False, 'error': {'password': password_error}},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                request.user.set_password(request.data['password'])

        # Проверяем остальные данные
        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return Response({'status': True}, status=status.HTTP_201_CREATED)
        else:
            return Response({'status': False, 'error': user_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ContactView(APIView):
    """
    Класс для работы с контактами пользователей
    """
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'status': False, 'error': 'Вы не авторизовались!'}, status=status.HTTP_403_FORBIDDEN)

        contact = Contact.objects.filter(user__id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

    # Добавить новый контакт
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'status': False, 'error': 'Вы не авторизовались!'}, status=status.HTTP_403_FORBIDDEN)

        if {'city', 'street', 'phone'}.issubset(request.data):
            request.data._mutable = True
            request.data.update({'user': request.user.id})
            serializer = ContactSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return Response({'status': True}, status=status.HTTP_201_CREATED)
            else:
                Response({'status': False, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': False, 'error': 'Не указаны все необходимые аргументы'},
                        status=status.HTTP_400_BAD_REQUEST)

    # Редактируем контакт
    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'status': False, 'error': 'Вы не авторизовались!'}, status=status.HTTP_403_FORBIDDEN)

        if {'id'}.issubset(request.data):
            try:
                contact = Contact.objects.get(pk=int(request.data["id"]))
            except ValueError:
                return Response(
                    {'status': False, 'error': 'Неверный тип аргумента ID.'}, status=status.HTTP_400_BAD_REQUEST)
            except ObjectDoesNotExist:
                return Response(
                    {'status': False, 'error': f"Контакта с ID={request.data['id']} не существует."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = ContactSerializer(contact, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': True}, status=status.HTTP_200_OK)
            return Response({'status': False, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': False, 'error': 'Не указаны все необходимые аргументы'},
                        status=status.HTTP_400_BAD_REQUEST)

    # Удаляем указанные контакты
    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'status': False, 'error': 'Вы не авторизовались!'}, status=status.HTTP_403_FORBIDDEN)

        if {'items'}.issubset(request.data):
            for item in request.data["items"].split(','):
                try:
                    contact = Contact.objects.get(pk=int(item))
                    contact.delete()
                except ValueError:
                    return Response({'status': False, 'error': 'Неверный тип аргумента (items).'},
                                    status=status.HTTP_400_BAD_REQUEST)
                except ObjectDoesNotExist:
                    return Response({'status': False, 'error': f'Контакта с ID={item} не существует.'},
                                    status=status.HTTP_400_BAD_REQUEST)
            return Response({'status': True}, status=status.HTTP_204_NO_CONTENT)

        return Response({'status': False, 'error': 'Не указаны ID контактов'},
                        status=status.HTTP_400_BAD_REQUEST)


class PartnerUpdate(APIView):
    """
    Класс для обновления прайса от поставщика
    """
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'status': False, 'error': 'Log in required'}, status=status.HTTP_403_FORBIDDEN)

        if request.user.type != 'shop':
            return Response({'status': False, 'error': 'Только для магазинов'}, status=status.HTTP_403_FORBIDDEN)

        url = request.data.get('url')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return Response({'status': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            else:
                stream = get(url).content

                data = load_yaml(stream, Loader=Loader)

                shop, _ = Shop.objects.get_or_create(user_id=request.user.id,
                                                     defaults={'name': data['shop'], 'url': url})
                if shop.name != data['shop']:
                    return Response({'status': False, 'error': 'В прайсе указано некорректное название магазина!'},
                                    status=status.HTTP_400_BAD_REQUEST)

                # заносим прайс в базу асинхронно (с помощью Celery)
                do_import.delay(data, shop.id)

                return Response({'status': True})

        return Response({'status': False, 'error': 'Не указаны все необходимые аргументы'},
                        status=status.HTTP_400_BAD_REQUEST)


class PartnerState(APIView):
    """
    Класс для работы со статусом поставщика
    """
    # Получить текущий статус получения заказов у магазина
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'status': False, 'error': 'Login required'}, status=status.HTTP_403_FORBIDDEN)

        if request.user.type != 'shop':
            return Response({'status': False, 'error': 'Только для магазинов'}, status=status.HTTP_403_FORBIDDEN)

        shop = request.user.shop
        serializer = ShopSerializer(shop)
        return Response(serializer.data)

    # Изменить текущий статус получения заказов у магазина
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'status': False, 'error': 'Log in required'}, status=status.HTTP_403_FORBIDDEN)

        if request.user.type != 'shop':
            return Response({'status': False, 'error': 'Только для магазинов'}, status=status.HTTP_403_FORBIDDEN)

        state = request.data.get('state')
        if state:
            try:
                Shop.objects.filter(user_id=request.user.id).update(state=strtobool(state))
                return Response({'status': True})
            except ValueError as error:
                return Response({'status': False, 'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': False, 'error': 'Не указан аргумент state.'}, status=status.HTTP_400_BAD_REQUEST)


class PartnerOrders(APIView):
    """
    Класс для получения заказов поставщиками
    """
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'status': False, 'error': 'Login required'}, status=status.HTTP_403_FORBIDDEN)

        if request.user.type != 'shop':
            return Response({'status': False, 'error': 'Только для магазинов'}, status=status.HTTP_403_FORBIDDEN)

        pr = Prefetch('ordered_items', queryset=OrderItem.objects.filter(shop__user_id=request.user.id))
        order = Order.objects.filter(
            ordered_items__shop__user_id=request.user.id).exclude(status='basket')\
            .prefetch_related(pr).select_related('contact').annotate(
            total_sum=Sum('ordered_items__total_amount'),
            total_quantity=Sum('ordered_items__quantity'))

        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)


class ShopView(ListAPIView):
    """
    Класс для просмотра списка магазинов
    """
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSerializer


class CategoryView(ListAPIView):
    """
    Класс для просмотра категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductView(APIView):
    """
    Класс для поиска товаров по выбранной категории и/или по выбранному магазину
    """
    def get(self, request, *args, **kwargs):

        query = Q(shop__state=True)
        shop_id = request.query_params.get('shop_id')
        category_id = request.query_params.get('category_id')

        if shop_id:
            query = query & Q(shop_id=shop_id)

        if category_id:
            query = query & Q(category_id=category_id)

        queryset = Product.objects.filter(
            query).select_related(
            'shop', 'category').prefetch_related(
            'product_parameters').distinct()

        serializer = ProductSerializer(queryset, many=True)

        return Response(serializer.data)


class BasketView(APIView):
    """
    Класс для работы с корзиной пользователя
    """
    # Получить содержимое корзины
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'status': False, 'error': 'Вы не авторизовались!'}, status=status.HTTP_403_FORBIDDEN)

        basket = Order.objects.filter(
            user_id=request.user.id, status='basket').prefetch_related(
            'ordered_items').annotate(
            total_sum=Sum('ordered_items__total_amount'),
            total_quantity=Sum('ordered_items__quantity'))

        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        """
        Добавление товаров в корзину. Принимает запрос:
        curl --location --request POST "http://.../api/v1/basket" --header "Authorization: Token ...."
             --form "items=[{\"product_name\": ..., \"external_id\": ..., \"quantity\": ..., \"price\": ...}, {...}]"
        """
        if not request.user.is_authenticated:
            return Response({'status': False, 'error': 'Вы не авторизовались!'}, status=status.HTTP_403_FORBIDDEN)

        items_string = request.data.get('items')
        if items_string:
            try:
                items = load_json(items_string)
            except ValueError:
                return Response({'status': False, 'error': 'Неверный формат запроса'},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                basket, _ = Order.objects.get_or_create(user_id=request.user.id, status='basket')
                objects_created = 0
                for order_item in items:
                    order_item.update({'order': basket.id})

                    product = Product.objects.filter(external_id=order_item['external_id']).values('category', 'shop')
                    order_item.update({'category': product[0]['category'], 'shop': product[0]['shop']})

                    serializer = OrderItemSerializer(data=order_item)
                    if serializer.is_valid():
                        try:
                            serializer.save()
                        except IntegrityError as error:
                            return Response({'status': False, 'errors': str(error)},
                                            status=status.HTTP_400_BAD_REQUEST)
                        else:
                            objects_created += 1
                    else:
                        return Response({'status': False, 'error': serializer.errors},
                                        status=status.HTTP_400_BAD_REQUEST)
                return Response({'status': True, 'num_objects': objects_created})

        return Response({'status': False, 'error': 'Не указаны все необходимые аргументы'},
                        status=status.HTTP_400_BAD_REQUEST)

    # Редактируем количество товаров в корзине
    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'status': False, 'error': 'Вы не авторизовались!'}, status=status.HTTP_403_FORBIDDEN)

        items_sting = request.data.get('items')
        if items_sting:
            try:
                items = load_json(items_sting)
            except ValueError:
                return Response({'status': False, 'error': 'Неверный формат запроса'},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                basket, _ = Order.objects.get_or_create(user_id=request.user.id, status='basket')
                objects_updated = 0
                for order_item in items:
                    if isinstance(order_item['id'], int) and isinstance(order_item['quantity'], int):
                        objects_updated += OrderItem.objects.filter(order_id=basket.id, id=order_item['id']).update(
                            quantity=order_item['quantity'])

                return Response({'status': True, 'num_objects': objects_updated})
        return Response({'status': False, 'error': 'Не указаны все необходимые аргументы'},
                        status=status.HTTP_400_BAD_REQUEST)

    # Удаляем товары из корзины
    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'status': False, 'error': 'Вы не авторизовались!'}, status=status.HTTP_403_FORBIDDEN)

        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            basket, _ = Order.objects.get_or_create(user_id=request.user.id, status='basket')
            query = Q()
            objects_deleted = False
            for order_item_id in items_list:
                if order_item_id.isdigit():
                    query = query | Q(order_id=basket.id, id=order_item_id)
                    objects_deleted = True

            if objects_deleted:
                deleted_count = OrderItem.objects.filter(query).delete()[0]
                return Response({'status': True, 'num_objects': deleted_count})
        return Response({'status': False, 'error': 'Не указаны все необходимые аргументы'},
                        status=status.HTTP_400_BAD_REQUEST)


class OrderView(APIView):
    """
    Класс для получения и размешения заказов пользователями
    """
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'status': False, 'error': 'Вы не авторизовались!'}, status=status.HTTP_403_FORBIDDEN)

        order = Order.objects.filter(
            user_id=request.user.id).exclude(status='basket').select_related('contact').prefetch_related(
            'ordered_items').annotate(
            total_quantity=Sum('ordered_items__quantity'),
            total_sum=Sum('ordered_items__total_amount')).distinct()

        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)

    # Размещаем заказ из корзины и посылаем письмо об изменении статуса заказа.
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'status': False, 'error': 'Вы не авторизовались!'}, status=status.HTTP_403_FORBIDDEN)

        if request.data['id'].isdigit():
            try:
                is_updated = Order.objects.filter(
                    id=request.data['id'], user_id=request.user.id).update(
                    contact_id=request.data['contact'],
                    status='new')
            except IntegrityError as error:
                return Response({'status': False, 'error': 'Неправильно указаны аргументы'},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                if is_updated:
                    # посылаем письмо об обновление статуса заказа (с помощью Celery)
                    send_change_order_email.delay(request.user.email, request.data["id"])
                    return Response({'status': True})

        return Response({'status': False, 'error': 'Не указаны все необходимые аргументы'},
                        status=status.HTTP_400_BAD_REQUEST)
