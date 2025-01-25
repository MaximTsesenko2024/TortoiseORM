from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException, Request
from fastapi.responses import RedirectResponse
from tortoise.fields.relational import _NoneAwaitable
from ..models.category import Categories
from fastapi.templating import Jinja2Templates
from ..depends import get_categories_subgroups, get_category, get_current_user, check_use_category
from ..shemas import category_pydantic, user_pydantic

category_router = APIRouter(prefix='/category', tags=['category'])
templates = Jinja2Templates(directory='app/templates/category/')


# Обработка таблицы Categories
# просмотр списка категорий
@category_router.get('/list')
async def list_categories_get(request: Request, user: Annotated[user_pydantic | None, Depends(get_current_user)]):
    """
    Отображение списка категорий в системе.
    :param request: Запрос.
    :param user: Текущий пользователь.
    :return: Отображение страницы со списком категорий
    """
    info = {'request': request, 'title': 'Список категорий'}
    if user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        categories = await Categories.all()
        if categories is not None:
            info['categories'] = categories
    return templates.TemplateResponse('categories_list.html', info)


# отображение формы для изменения категории
@category_router.get('/update/{id_category}')
async def update_category_get(request: Request, user: Annotated[user_pydantic | None, Depends(get_current_user)],
                              id_category: int, parent: str = ''):
    """
    Изменение данных выбранной категории. Для изменения доступно только поле родительская категория.
    :param request: Запрос.
    :param id_category: Идентификатор выбранной категории.
    :param user: Текущий пользователь
    :param parent: Идентификатор родительской категории
    :return: Страница с данными по выбранной категории
    """
    info = {'request': request, 'title': 'Обновление категории'}
    if user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not user.is_staff:
        info['message'] = 'У вас нет прав'
    elif parent == '':
        info['display'] = 'Ok'
        categories = await category_pydantic.from_queryset(Categories.all())
        category = get_category(categories, id_category)
        if category is None:
            return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Категория не найдена')
        info['category'] = category
        info['id_category'] = category.id
        info['categories'] = categories
    else:
        info['display'] = 'Ok'
        await Categories.filter(id=id_category).update(parent=int(parent))
        info['message'] = 'Обновлено'
        return RedirectResponse(f'/category/{id_category}',
                                status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse('category_update.html', info)


# создание новой категории
@category_router.get('/create')
async def add_category_get(request: Request, user: Annotated[user_pydantic | None, Depends(get_current_user)],
                           name: str = '', parent: str = ''):
    """
    Создание новой категории. При наличии прав сотрудника отображается форма для ввода данных новой категории,
    а если данные уже введены то список категорий.
    :param request: Запрос.
    :param user: Текущий пользователь.
    :param name: Название новой категории или ''
    :param parent: Номер родительской категории или ''
    :return: Страница создания категории или переход к списку категорий
    """
    info = {'request': request, 'title': 'Создание категории'}
    if user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        if name == '' and parent == '':
            categories = await category_pydantic.from_queryset(Categories.all())
            if categories is not None:
                info['categories'] = categories
        elif name == '':
            info['message'] = 'Поле название не может быть пустым'
        elif parent == '':
            info['message'] = 'Поле родительская категория не может быть пустым'
        else:
            await Categories.create(name=name, parent=int(parent))
            return RedirectResponse('/category/list')
    return templates.TemplateResponse('category_create.html', info)


# удаление категории
@category_router.get('/delete/{id_category}')
async def delete_category_get(request: Request, user: Annotated[user_pydantic | None, Depends(get_current_user)],
                              id_category: int):
    """
    Запрос на удаление выбранной категории. Если текущий пользователь имеет права сотрудника, то отображаются данные
    выбранной категории с запросом на подтверждение удаления категории. Если пользователь не определён или у него нет
    прав сотрудника, то отобразится пустая страница с сообщением.
    :param request: Запрос.
    :param user: Текущий пользователь
    :param id_category: Идентификатор выбранной категории
    :return: Страница удаления категории
    """
    info = {'request': request, 'title': 'Удаление категории'}
    if user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        info['id_category'] = id_category
        categories = await Categories.all()
        category = get_category(categories, id_category)
        use_category = await check_use_category(id_category)
        info['name'] = category.name
        children = get_categories_subgroups(categories, id_category)
        if len(children) > 0:
            info['message'] = 'Удаление запрещено. Имеются связанные категории'
            info['children'] = children
        elif use_category:
            info['message'] = 'Удаление запрещено. Категория уже используется'
        else:
            info['delete'] = 1
    return templates.TemplateResponse('category_delete.html', info)


@category_router.post('/delete/{id_category}')
async def delete_category_post(request: Request, user: Annotated[user_pydantic | None, Depends(get_current_user)],
                               id_category: int):
    """
    Выполнение удаления категории из базы данных. Если текущий пользователь имеет права сотрудника, то выполниться
    удаление выбранной категории. Если пользователь не определён или у него нет прав сотрудника,
    то отобразится пустая страница с сообщением.
    :param request: Запрос.
    :param user: Текущий пользователь.
    :param id_category: Идентификатор выбранной категории
    :return: Страница со списком категорий либо страница удаления товара
    """
    info = {'request': request, 'title': 'Удаление категории'}
    if user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        await Categories.filter(id=id_category).delete()
        return RedirectResponse('/list', status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse('category_delete.html', info)


# просмотр категории
@category_router.get('/{id_category}')
async def category_get(request: Request, user: Annotated[user_pydantic | None, Depends(get_current_user)],
                       id_category: int):
    """
    Отображение данных выбранной категории. Если текущий пользователь имеет права сотрудника, то отобразятся данные
    выбранной категории. Если пользователь не определён или у него нет прав сотрудника,
    то отобразится пустая страница с сообщением.
    :param request: Запрос.
    :param user: Текущий пользователь.
    :param id_category: Идентификатор выбранной категории
    :return: Страница описания категории
    """
    info = {'request': request, 'title': 'Описание категории'}
    if user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        categories = await Categories.all()
        category = await Categories.filter(id=id_category).first()
        if isinstance(category, _NoneAwaitable):
            return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Категория не найдена')
        if isinstance(category.parent, _NoneAwaitable):
            pass
        else:
            info['parent'] = get_category(categories, category.parent)
        info['category'] = category
        info['children'] = get_categories_subgroups(categories, id_category)
        info['categories'] = categories
    return templates.TemplateResponse('category.html', info)
