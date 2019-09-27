# pd-diplom-webshop

Дипломная работа к профессии Python-разработчик (API Сервис заказа товаров для розничных сетей)

## Описание

Приложение предназначено для автоматизации закупок.

**Клиент (покупатель):**

- Менеджер закупок через API делает ежедневные закупки по каталогу, в котором
  представлены товары от нескольких поставщиков.
- В одном заказе можно указать товары от разных поставщиков - это
  повлияет на стоимость доставки.
- Пользователь может авторизироваться, регистрироваться и восстанавливать пароль через API
    
**Поставщик:**
- Через API информирует сервис об обновлении прайса.
- Может включать и отключать прием заказов.
- Может получать список оформленных заказов (с товарами из его прайса)


### Разработана backend-часть (Django) сервиса заказа товаров для розничных сетей.

Базовая часть:
* Разработка сервиса под готовую спецификацию (API).
* Возможность добавления настраиваемых полей (характеристик) товаров.
* Импорт списка товаров.
* Отправка накладной на email администратора (для исполнения заказа).
* Отправка заказа на email клиента (подтверждение приема заказа).
* Выделение медленных методов в отдельные процессы (email, импорт) через Celery.

Продвинутая часть:
* Админка заказов (проставление статуса заказа и уведомление клиента)

### Исходные данные
 
1. Общее описание сервиса (./reference/service.md)
2. Спецификация (API)  (./reference/api.md)
3. Описание страниц сервиса  (./reference/screens.md)
4. Файлы yaml для импорта товаров

### POSTMAN
Схема API опубликована на сервисе POSTMAN:
https://documenter.getpostman.com/view/8939969/SVn3rad3

### База данных
В качестве СУБД использован PostgreSQL

$ sudo apt install postgresql
$ sudo -u postgres psql postgres
> create user diplom_user with password 'password';
> alter role diplom_user set client_encoding to 'utf8';
> alter role diplom_user set default_transaction_isolation to 'read commited';
> alter role diplom_user set timezone to 'Europe/Moscow';
> create database diplom_db owner diplom_user;
> alter user diplom_user createdb;

### Для запуска проекта необходимо:

1. Установить зависимости:
$ pip install -r requirements.txt

2. Выполнить миграцию:
$ python manage.py makemigrations
$ python manage.py migrate

3. Создать администратора
$ python manage.py createsuperuser

4. Запустить приложение:
$ python manage.py runserver 0.0.0.0:8000

5. Запустить сервер Redis:
$ redis-server

6. В каталоге проекта запустить Celery:
$ celery worker -A orders --loglevel=debug --concurrency=4
