from tortoise.functions import Max
from fastapi import APIRouter, Depends, status, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Annotated
from ..models.buy import BuyerProd
from fastapi.templating import Jinja2Templates
from ..depends import get_product, update_count_product, get_shop, get_shop_list, get_current_user, get_shop_model, \
    get_product_model, get_user_model
from ..shemas import Car, Payment, user_pydantic


buy_router = APIRouter(prefix='/buy', tags=['buy'])
templates = Jinja2Templates(directory='app/templates/buy/')


class CarView:
    """
    Класс представляющий товар в корзине пользователя
    """
    def __init__(self, number, id_prod, name, price, count):
        self.number = number
        self.id_prod = id_prod
        self.name = name
        self.price = price
        self.count = count


# корзины для покупки
cars = {}


@buy_router.get('/payment')
async def payment_get(request: Request, user: Annotated[user_pydantic | None, Depends(get_current_user)],
                      shop: str = ''):
    """
    Оплата товара. Отображение страницы оплаты.
    :param request: Запрос.
    :param shop: Идентификатор выбранного магазина.
    :param user: Текущий пользователь.
    :return: Отображение страницы оплаты
    """
    info = {'request': request, 'title': 'Оплата товара'}
    cost = 0
    car = cars[user.id]
    info['car'] = car
    info['user'] = user
    for item in car:
        cost += item.price * item.count
    info['cost'] = cost
    shop = await get_shop(int(shop))
    info['shop'] = shop
    info['display'] = True
    return templates.TemplateResponse('payment.html', info)


@buy_router.post('/payment')
async def payment_post(request: Request, user: Annotated[user_pydantic | None, Depends(get_current_user)],
                       pay: Payment = Form(), shop: str = ''):
    """
    Оплата товара. Выполнение оплаты.
    :param pay: Платёжные данные покупателя.
    :param request: Запрос.
    :param user: Текущий пользователь.
    :param shop: Идентификатор магазина.
    :return: Сообщение об оплате.
    """
    info = {'request': request, 'title': 'Спасибо за покупку'}
    max_operation = \
        (await BuyerProd.annotate(max_operation=Max("id_operation")).values_list("max_operation", flat=True))[0]
    if max_operation is None:
        max_operation = 1
    else:
        max_operation = max_operation + 1
    shop_sel = await get_shop_model(int(shop))
    user_buy = await get_user_model(user.id)
    for item in cars[user.id]:
        prod = await get_product_model(item.id_prod)
        await BuyerProd.create(user=user_buy, product=prod, id_operation=max_operation, id_shop=shop_sel,
                               count=item.count)
    cars.pop(user.id)
    print(pay.name, pay.card_number)
    info['message'] = f'Заказ номер: {max_operation}'
    return templates.TemplateResponse('payment.html', info)


@buy_router.post('/car/{id_product}')
async def car_post(request: Request, user: Annotated[user_pydantic | None, Depends(get_current_user)],
                   id_product: int = -1, car_user: Car = Form()):
    """
    Добавление товара в корзину.
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :param car_user: Данные по количеству товара
    :param user: Текущий пользователь.
    :return: Страница с формой корзины.
    """
    info = {'request': request, 'title': 'Корзина'}
    if user is None:
        return RedirectResponse(f'/user/login', status_code=status.HTTP_303_SEE_OTHER)
    product = await get_product(id_product)
    if product is None:
        return HTTPException(status.HTTP_404_NOT_FOUND, 'Товар не найден')
    if car_user.count < 1:
        info['message'] = 'Требуемое количество товара не может быть меньше 1'
    else:
        info['user'] = user
        new_count = product.count - car_user.count
        if new_count < 0:
            info['buy'] = 1
            info['message'] = 'Не достаточно товара'
            info['count'] = product.count
        else:
            await update_count_product(id_product, -car_user.count)
            product = await get_product(id_product)
        info['product'] = product
        if user.id not in cars.keys():
            cars[user.id] = []

        cars[user.id].append(CarView(len(cars[user.id]), product.id, product.name, product.price, car_user.count))

        print(cars)
    return templates.TemplateResponse('car.html', info)


@buy_router.get('/car/{id_product}')
async def car_get(request: Request, user: Annotated[user_pydantic | None, Depends(get_current_user)],
                  id_product: int = -1):
    """
    Отображение страницы корзины товара. На странице необходимо ввести количество товара.
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :param user: Текущий пользователь.
    :return: Страница корзины товара
    """
    info = {'request': request, 'title': 'Корзина'}
    if user is None:
        return RedirectResponse(f'/user/login', status_code=status.HTTP_303_SEE_OTHER)
    product = await get_product(id_product)
    if product is None:
        return HTTPException(status.HTTP_404_NOT_FOUND, 'Товар не найден')
    info['product'] = product
    info['user'] = user
    info['count'] = 1
    info['buy'] = 1
    return templates.TemplateResponse('car.html', info)


@buy_router.get('')
async def buy_get(request: Request, delet: int = -1, shop: str = '', user=Depends(get_current_user)):
    """
    Отображение страницы корзины текущего пользователя.
    :param request: Запрос.
    :param delet: Идентификатор удаляемого товара.
    :param shop:  Идентификатор выбранного магазина
    :param user:  Текущий пользователь.
    :return: Страница корзины текущего пользователя.
    """
    info = {'request': request, 'title': 'Корзина'}
    print('buy')
    cost = 0
    if user.id not in cars.keys():
        info['message'] = 'Корзина пуста'
    else:
        if delet > -1:
            for i in range(len(cars[user.id])):
                if cars[user.id][i].number == delet:
                    await update_count_product(cars[user.id][i].id_prod, cars[user.id][i].count)
                    cars[user.id].pop(i)
                    break
        info['display'] = 1
        car = cars[user.id]
        info['car'] = car
        info['user'] = user
        info['shops'] = await get_shop_list()
        for item in car:
            cost += item.price * item.count
        info['cost'] = cost
    return templates.TemplateResponse('buy.html', info)


@buy_router.post('')
async def buy_post(request: Request, user: Annotated[user_pydantic | None, Depends(get_current_user)],
                   shop: str = Form(...)):
    """
    Отображение страницы корзины текущего пользователя. Выбор магазина.
    :param request: Запрос.
    :param user: Текущий пользователь.
    :param shop: Идентификатор выбранного магазина.
    :return: Переход к оплате или отображение страницы корзины пользователя.
    """
    info = {'request': request, 'title': 'Оплата товара'}
    cost = 0
    car = cars[user.id]
    info['car'] = car
    info['user'] = user
    for item in car:
        cost += item.price * item.count
    info['cost'] = cost
    if shop == '':
        info['message'] = 'Выберите магазин'
        return templates.TemplateResponse('buy.html', info)

    return RedirectResponse(f'/buy/payment?shop={shop}', status_code=status.HTTP_303_SEE_OTHER)
