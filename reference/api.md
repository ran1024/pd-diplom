## API для пользователя (регистрация, управление контактами и т.д.)

#### Регистрация нового пользователя
```
POST /api/v1/user/register
{
    "first_name": "имя",
    "last_name": "фамилия",
    "email": "адрес электронной почты",
    "password": "qwer1234A",
    "company": "adidas",
    "position": "Директор",
}

200 OK
{
    "Status": true,         # Пользователю отправлено письмо для подтверждения регистрации.
}

400 BAD REQUEST
{
    "Status": false,
    "Errors": "Не указаны все необходимые аргументы",
}

403 FORBIDDEN
{
    "Status": false,        # Ошибка валидации в сериализаторе или валидации пароля.
    "Errors": "описание ошибки",
}
```


#### Подтверждение email новым пользователем
```
POST /api/v1/user/register/confirm
{
    "email": "адрес электронной почты",
    "token": "5d457b7268789ae558a130724ebde9"
}

200 OK
{
    "Status": true,
}


403 FORBIDDEN
{
    "Status": false,
    "Errors": "Неправильно указан токен или email",
}
```


#### Получить контакты пользователя
```
GET /api/v1/user/contact
{
    "token": "b39d0f93f9e895b82f1724832b7c186a",
}

200 OK
[
    {
        "id": 3,
        "city": "Город",
        "street": "Улица",
        "house": "123",
        "structure": "",
        "building": "",
        "apartment": "",
        "phone": "+7 223-332",
    }
]

401 UNAUTHORIZED
{
    "detail": "Учётные данные не были предоставлены.",
}
```


#### Создать контакт
```
POST /api/v1/user/contact
{
    "token": "b39d0f93f9e895b82f1724832b7c186a",
    "city": "Город",
    "street": "Улица",
    "house": "№ дома",
    "structure": "№ корпуса",
    "building": "№ строения",
    "apartment": "№ квартиры",
    "phone": "+74956453242",
}

201 CREATED
{
    "Status": true,         # Контакт создан.
}

400 BAD REQUEST
{
    "Status": false,
    "Errors": "Не указаны все необходимые аргументы",   # или ошибки сериализатора.
}

401 UNAUTHORIZED
{
    "detail": "Учётные данные не были предоставлены.",
}
```


#### Редактировать контакт
```
PUT /api/v1/user/contact
{
    "token": "b39d0f93f9e895b82f1724832b7c186a",
    "id": 7,
    "city": "Город",
    "street": "Улица",
    "house": "№ дома",
    "structure": "№ корпуса",
    "building": "№ строения",
    "apartment": "№ квартиры",
    "phone": "+74956453242",
}

200 OK
{
    "Status": true,         # Контакт создан.
}

400 BAD REQUEST
{
    "Status": false,
    "Errors": "описание возникшей ошибки",
}

401 UNAUTHORIZED
{
    "detail": "Учётные данные не были предоставлены.",
}
```


#### Удалить контакты
```
DEL /api/v1/user/contact
{
    "token": "b39d0f93f9e895b82f1724832b7c186a",
    "items": "1,4,7",
}

204 NO CONTENT
{
    "Status": true,         # Контакт создан.
}

400 BAD REQUEST
{
    "Status": false,
    "Errors": "описание возникшей ошибки",
}

401 UNAUTHORIZED
{
    "detail": "Учётные данные не были предоставлены.",
}
```


#### Получить все данные пользователя, включая конткты
```
GET /api/v1/user/details
{
    "token": "b39d0f93f9e895b82f1724832b7c186a",
}

200 OK
{
    "id": 6,
    "first_name": "Имя",
    "last_name": "Фамилия",
    "email": "name@domain.com",
    "company": "Adidas",
    "position": "Директор",
    "contacts": [
        {
            "id": 3,
            "city": "Город",
            "street": "Улица",
            "house": "123",
            "structure": "",
            "building": "",
            "apartment": "",
            "phone": "+7 223-332",
        }
    ]
}

401 UNAUTHORIZED
{
    "detail": "Учётные данные не были предоставлены.",
}
```


#### Редактировать данные пользователя
```
POST /api/v1/user/details
{
    "token": "b39d0f93f9e895b82f1724832b7c186a",
    "first_name": "Имя",
    "last_name": "Фамилия",
    "email": "name@domain.com",
    "password": "пароль",
    "company": "Adidas",
    "position": "Директор",
}

201 CREATED
{
    "Status": true,
}

400 BAD REQUEST
{
    "Status": false,
    "Errors": "описание возникшей ошибки",
}

401 UNAUTHORIZED
{
    "detail": "Учётные данные не были предоставлены.",
}
```


#### Авторизация пользователя
```
POST /api/v1/user/login
{
    "email": "name@domain.com",
    "password": "пароль",
}

200 OK
{
    "Status": true,
    "Token": "b39d0f93f9e895b82f1724832b7c186a",
}

400 BAD REQUEST
{
    "Status": false,
    "Errors": "Не указаны все необходимые аргументы",
}

403 FORBIDDEN
{
    "Status": false,
    "Errors": "Не удалось авторизовать",
}
```


#### Сброс пароля пользователя
```
POST /api/v1/user/password_reset
{
    "email": "name@domain.com",
}

200 OK
{
    "status": "OK"
}

400 BAD REQUEST
{
    "email": ["описание ошибки"],
}
```


#### Подтверждение сброса пароля пользователя и установка нового пароля.
```
POST /api/v1/user/password_reset/confirm
{
    "email": "name@domain.com",
    "password": "новый пароль",
    "token": "b39d0f93f9e895b82f1724832b7c186a",
}

200 OK
{
    "status": "OK"
}

400 BAD REQUEST
{
    "email": ["описание ошибки"],
}
```


## API для покупателей

#### Получить список магазинов
```
GET /api/v1/shops

200 OK
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Связной",
            "state": true,
            "url": "https://......",
        },
        {
            "id": 2,
            "name": "Рога и копыта",
            "state": true,
            "url": "https://......",
        }
    ]
}
```


#### Получить список категорий товаров
```
GET /api/v1/categories

200 OK
{
    "count": 3,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 224,
            "name": "Смартфоны"
        },
        {
            "id": 15,
            "name": "Аксессуары"
        },
        {
            "id": 1,
            "name": "Flash-накопители"
        }
    ]
}
```


#### Поиск товара по категории и/или по магазину
```
GET /api/v1/products?shop_id=2&category_id=224
{
    "shop_id": 2,
    "category": 224
}

200 OK
[
    {
        "id": 14,
        "shop": "Рога и копыта",
        "name": "Смартфон Samsung A10 (синий)",
        "category": "Смартфоны",
        "external_id": 5432670,
        "model": "apple/iphone/xr",
        "quantity": 70,
        "price": 20000,
        "price_rrc": 21990,
        "product_parameters": [
            {"parameter": "Диагональ (дюйм)", "value": "6.1"},
            {"parameter": "Разрешение (пикс)", "value": "1792x828"},
            {"parameter": "Встроенная память (Гб)", "value": "32"},
            {"parameter": "Цвет", "value": "синий"}
        ]
    }
]
```


#### Получить содержимое корзины
```
GET /api/v1/basket
{
    "token": "b39d0f93f9e895b82f1724832b7c186a",
}

200 OK
[
    {
        "id": 3,
        "status": "basket",
        "total_quantity": 6,
        "total_sum": 480000,
        "contact": null,
        "ordered_items": [
            {
                "id": 8,
                "prodict_name": "Смартфон Samsung A10 (синий)",
                "external_id": 5432670,
                "quantity": 2,
                "price": 20000,
                "total_amount": 40000,
                "category": "Смартфоны",
                "shop": "Рога и копыта"
            },
            {
                "id": 9,
                "prodict_name": "Смартфон Apple iPhone XS Max 512GB (золотистый)",
                "external_id": 4216292,
                "quantity": 4,
                "price": 110000,
                "total_amount": 440000,
                "category": "Смартфоны",
                "shop": "Связной"
            }
        ]
    }
]

401 UNAUTHORIZED
{
    "detail": "Учётные данные не были предоставлены.",
}
```


#### Добавление товаров в корзину
```
POST /api/v1/basket
{
    "token": "b39d0f93f9e895b82f1724832b7c186a",
    "items": [
        {
            "product_name": "Смартфон Apple iPhone XS Max 512GB (золотистый)",
            "external_id": 4216292,
            "quantity": 4,
            "price": 110000,
        },
    ]
}

200 OK
{
    "status": true,
    "num_objects": 1        # Добавлено в корзину новых объектов.
}

400 BAD REQUEST
{
    "status": false,
    "error": "описание возникшей ошибки",
}

401 UNAUTHORIZED
{
    "detail": "Учётные данные не были предоставлены.",
}
```


#### Редактировать количество товаров в корзине
```
PUT /api/v1/basket
{
    "token": "b39d0f93f9e895b82f1724832b7c186a",
    "items": [
        {"id": 8, "quantity": 12},
        {"id": 9, "quantity": 31},
    ]
}

200 OK
{
    "status": true,
    "num_objects": 1        # Обновлено объектов.
}

400 BAD REQUEST
{
    "status": false,
    "error": "описание возникшей ошибки",
}

401 UNAUTHORIZED
{
    "detail": "Учётные данные не были предоставлены.",
}
```


#### Удалить товары из корзины
```
DEL /api/v1/basket
{
    "token": "b39d0f93f9e895b82f1724832b7c186a",
    "items": "93,15,124",
}

200 OK
{
    "status": true,
    "num_objects": 1        # Удалено объектов из корзины.
}

400 BAD REQUEST
{
    "status": false,
    "error": "Не указаны все необходимые документы",
}

401 UNAUTHORIZED
{
    "detail": "Учётные данные не были предоставлены.",
}
```


#### Получить заказы
```
GET /api/v1/order
{
    "token": "b39d0f93f9e895b82f1724832b7c186a",
}

200 OK
[
    "id": 1,
    "status": "new",
    "total_quantity": 14,
    "total_sum": 1360000,
    "contact": {
        "id": 3,
        "city": "Город",
        "street": "Улица",
        "house": 15,
        "structure": "",
        "building": "",
        "apartment": "",
        "phone": "+7 223-322"
    },
    "ordered_items":[
        {
            "id": 4,
            "product_name": "Смартфон Aple iPhone XS Max 512GB (золотистый)",
            "external_id": 4216292,
            "quantity": 12,
            "price": 110000,
            "total_amount": 1320000,
            "category": "Смартфоны",
            "shop": "Связной"
        }
    ]
]

401 UNAUTHORIZED
{
    "detail": "Учётные данные не были предоставлены.",
}
```


#### Разместить заказ из корзины
```
POST /api/v1/order
{
    "token": "b39d0f93f9e895b82f1724832b7c186a",
    "id": 3,
    "contact": 3
}

200 OK
{
    "status": true,
}

400 BAD REQUEST
{
    "status": false,
    "error": "Не указаны все необходимые документы",
}

401 UNAUTHORIZED
{
    "detail": "Учётные данные не были предоставлены.",
}
```


## API для поставщиков

#### Обновить прайс поставщика
```
POST /api/v1/partner/update
{
    "token": "b39d0f93f9e895b82f1724832b7c186a",
    "url": "https://partner-site.ru/files/price.yaml",
}

200 OK
{
    "status": true,
}

400 BAD REQUEST
{
    "status": false,
    "error": "описание ошибки",
}

401 UNAUTHORIZED
{
    "detail": "Учётные данные не были предоставлены.",
}
```


#### Получить статус магазина поставщика.
```
GET /api/v1/partner/state
{
    "token": "b39d0f93f9e895b82f1724832b7c186a",
}

200 OK
{
    "id": 1,
    "name": "Связной",
    "state": true,
    "url": "https://......"
}

401 UNAUTHORIZED
{
    "detail": "Учётные данные не были предоставлены.",
}
```


#### Включить/выключить приём заказов магазином
```
POST /api/v1/partner/state
{
    "token": "b39d0f93f9e895b82f1724832b7c186a",
    "state": "off",
}

200 OK
{
    "status": true,
}

400 BAD REQUEST
{
    "status": false,
    "error": "описание ошибки",
}

401 UNAUTHORIZED
{
    "detail": "Учётные данные не были предоставлены.",
}
```


#### Получить сформированные заказы для поставщика
```
GET /api/v1/partner/order
{
    "token": "b39d0f93f9e895b82f1724832b7c186a",
}

200 OK
[
    {
        "id": 3,
        "status": "new",
        "total_quantity": 4,
        "total_sum": 440000,
        "contact": {
            "user_id": 6,
            "city": "Город",
            "street": "Улица",
            "house": 15,
            "structure": "",
            "building": "",
            "apartment": "",
            "phone": "+7 223-322"
        },
        "ordered_items": [
            {
                "id": 9,
                "product_name": "Смартфон Aple iPhone XS Max 512GB (золотистый)",
                "external_id": 4216292,
                "quantity": 4,
                "price": 110000,
                "total_amount": 440000,
                "category": "Смартфоны",
                "shop": "Связной
            },
        ]
    },
]

401 UNAUTHORIZED
{
    "detail": "Учётные данные не были предоставлены.",
}
```
