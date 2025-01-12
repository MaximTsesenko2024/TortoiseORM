from typing import Annotated
from fastapi import APIRouter, Depends, status, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from ..models.shop import Shops
from ..depends import get_current_user
from ..shemas import Shop, user_pydantic

shop_router = APIRouter(prefix='/shop', tags=['shop'])
templates = Jinja2Templates(directory='app/templates/shop/')


# Обработка таблицы Shops
@shop_router.get('/create')
async def create_shop_get(request: Request, user: Annotated[user_pydantic | None, Depends(get_current_user)]):
    """
    Добавление нового магазина. Отображение страницы с формой добавления нового магазина, если пользователь - сотрудник.
    Если пользователь не определён, то переход к странице входа в систему. Если пользователь не имеет прав сотрудника,
    то переход на главную страницу.
    :param request: Запрос.
    :param user: Текущий пользователь.
    :return: Страница добавления магазина или переход на другую страницу.
    """
    info = {'request': request, 'title': 'Добавление магазина'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/main')
    else:
        info['display'] = 'Ok'
        return templates.TemplateResponse('add_shop_page.html', info)


@shop_router.post('/create')
async def create_shop_post(request: Request, user: Annotated[user_pydantic | None, Depends(get_current_user)],
                           shop: Shop = Form()):
    """
    Добавление нового магазина. Добавление данных о магазине в базу данных и переход к списку магазинов.
    Если пользователь не определён, то переход к странице входа в систему. Если пользователь не имеет прав сотрудника,
    то переход на главную страницу.
    :param request: Запрос.
    :param shop: Данные по магазину: название и расположение.
    :param user: Текущий пользователь.
    :return: Переход на страницу.
    """
    info = {'request': request, 'title': 'Добавление магазина'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/main')
    else:
        info['display'] = 'Ok'
        await Shops.create(name=shop.name, location=shop.location)
        return RedirectResponse('/shop/list', status_code=status.HTTP_303_SEE_OTHER)


@shop_router.get('/update/{shop_id}')
async def update_shop_get(request: Request, user: Annotated[user_pydantic | None, Depends(get_current_user)],
                          shop_id: int = -1):
    """
    Изменение данных магазина. Отображение страницы с формой изменения данных магазина, если пользователь - сотрудник.
    Если пользователь не определён, то переход к странице входа в систему. Если пользователь не имеет прав сотрудника,
    то переход на главную страницу.
    :param request: Запрос.
    :param shop_id: Идентификатор магазина.
    :param user: Текущий пользователь.
    :return: Страница изменения данных магазина или переход на другую страницу.
    """
    info = {'request': request, 'title': 'Изменение данных магазина'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/main')
    else:
        info['display'] = 'Ok'
        shop = await Shops.filter(id=shop_id).first()
        if shop is None:
            return RedirectResponse('/shop/list')
        info['shop'] = shop
        return templates.TemplateResponse('update_shop_page.html', info)


@shop_router.post('/update/{shop_id}')
async def update_shop_post(request: Request, user: Annotated[user_pydantic | None, Depends(get_current_user)],
                           shop: Shop = Form(), shop_id: int = -1):
    """
    Изменение данных магазина. Внесение изменений в базу данных и переход к списку магазинов,
    если пользователь - сотрудник.
    Если пользователь не определён, то переход к странице входа в систему. Если пользователь не имеет прав сотрудника,
    то переход на главную страницу.
    :param request: Запрос.
    :param shop: Новые данные по магазину: расположение.
    :param shop_id: Идентификатор магазина.
    :param user: Текущий пользователь.
    :return: Переход на другую страницу
    """
    info = {'request': request, 'title': 'Изменение данных магазина'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/main')
    else:
        info['display'] = 'Ok'
        await Shops.filter(id=shop_id).update(name=shop.name, location=shop.location)
        return RedirectResponse('/shop/list', status_code=status.HTTP_303_SEE_OTHER)


@shop_router.get('/delete/{shop_id}')
async def delete_shop_get(request: Request, user: Annotated[user_pydantic | None, Depends(get_current_user)],
                          shop_id: int = -1):
    """
    Удаление магазина. Отображение формы с подтверждением удаления если пользователь сотрудник.
    Если пользователь не определён, то переход к странице входа в систему. Если пользователь не имеет прав сотрудника,
    то переход на главную страницу.
    :param request: Запрос.
    :param shop_id: Идентификатор магазина.
    :param user: Текущий пользователь.
    :return: Отображение страницы удаления или переадресация на другие страницы.
    """
    info = {'request': request, 'title': 'Удаление данных о магазине'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/main')
    else:
        info['display'] = 'Ok'
        shop = await Shops.filter(id=shop_id).first()
        if shop is None:
            return RedirectResponse('/shop/list')
        info['shop'] = shop
        return templates.TemplateResponse('delete_shop_page.html', info)


@shop_router.post('/delete/{shop_id}')
async def delete_shop_post(request: Request, user: Annotated[user_pydantic | None, Depends(get_current_user)],
                           shop_id: int = -1):
    """
     Удаление магазина. Удаление магазина из базы данных и переадресация на список магазинов
     если пользователь сотрудник. Если пользователь не определён, то переход к странице входа в систему.
     Если пользователь не имеет прав сотрудника, то переход на главную страницу.
    :param request: Запрос.
    :param shop_id: Идентификатор магазина.
    :param user: Текущий пользователь.
    :return: Переадресация на другие страницы
    """
    info = {'request': request, 'title': 'Удаление данных о магазине'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/main')
    else:
        info['display'] = 'Ok'
        await Shops.filter(id=shop_id).update(is_active=False)
        return RedirectResponse('/shop/list', status_code=status.HTTP_303_SEE_OTHER)


@shop_router.get('/list')
async def select_shop_list_get(request: Request, user: Annotated[user_pydantic | None, Depends(get_current_user)]):
    """
    Отображение страницы со списком магазинов.
    :param request: Запрос.
    :param user: Текущий пользователь.
    :return: Страница со списком магазинов.
    """
    info = {'request': request, 'title': 'Список магазинов'}
    shops = await Shops.filter(is_active=True).all()
    if user is None:
        pass
    elif user.is_staff:
        info['display'] = 'Ok'
    info['shops'] = shops
    return templates.TemplateResponse('shop_list_page.html', info)


@shop_router.get('/{shop_id}')
async def select_shop_get(request: Request, user: Annotated[user_pydantic | None, Depends(get_current_user)],
                          shop_id: int = -1):
    """
    Отображение страницы с данными по магазину.
    :param request: Запрос.
    :param shop_id: Идентификатор магазина.
    :param user: Текущий пользователь.
    :return: Страница магазина.
    """
    info = {'request': request, 'title': 'Данные магазина'}
    if user is None:
        pass
    elif user.is_staff:
        info['display'] = 'Ok'
    shop = await Shops.filter(id=shop_id).first()
    if shop is None:
        return RedirectResponse('/shop/list', status_code=status.HTTP_303_SEE_OTHER)
    info['shop'] = shop
    return templates.TemplateResponse('shop_page.html', info)
