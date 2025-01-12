from tortoise.expressions import Q
from fastapi import File, UploadFile, APIRouter, Depends, status, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from typing import Annotated
from fastapi.templating import Jinja2Templates
import os
from PIL import Image
from ..models.product import ProductModel
from ..depends import check_use_product, get_categories, get_category, find_category, get_current_user, \
    get_category_model
from ..backend.service.service import pagination, image_to_str
from ..shemas import product_pydantic, user_pydantic

product_router = APIRouter(prefix='/product', tags=['product'])
templates = Jinja2Templates(directory='app/templates/product/')


# Обработка таблицы Product
@product_router.get('/list')
async def select_products_list_get(request: Request, user: Annotated[user_pydantic, Depends(get_current_user)],
                                   category: str = '', q: str = '', page: str = ''):
    """
    Просмотр списка товаров. Список товаров может быть ограничен выбранной категорией, совпадением названия или
    описания со строкой поиска.
    :param request: Запрос.
    :param user: Текущий пользователь
    :param category: Идентификатор категории
    :param q: строка поиска
    :param page: номер страницы списка товаров
    :return: Страница списка товаров.
    """
    info = {'request': request, 'title': 'Список товаров'}
    if page == '':
        page = 0
    else:
        page = int(page)
    if user is None:
        pass
    elif user.is_staff:
        info['is_staff'] = 'Ok'
    if q != '':
        querty = Q(join_type=Q.OR, name__icontains=q, description__icontains=q)
        products = await product_pydantic.from_queryset(ProductModel.filter(querty).all())
    elif category != '':
        products = await product_pydantic.from_queryset(ProductModel.filter(category=int(category)).all())
    else:
        products = await product_pydantic.from_queryset(ProductModel.filter().all())
    if len(products) > 0:
        product_list = []
        for product in products:
            image_str, format_file = image_to_str(product, 'list')
            product_list.append({'name': product.name, 'price': product.price, 'id': product.id, 'image_str': image_str,
                                 'format_file': format_file, 'is_active': product.is_active, 'count': product.count})
        info['products'], service = pagination(product_list, page, 4)
        pages = [x for x in range(service['total'] + 1)]
        info['service'] = {'page': service['page'], 'size': service['size'], 'pages': pages}
        info['categories'] = await get_categories()
    return templates.TemplateResponse('product_list_page.html', info)


# Создание нового продукты
@product_router.post('/create')
async def create_product_post(request: Request,
                              user: Annotated[user_pydantic, Depends(get_current_user)], name: str = Form(...),
                              item_number: str = Form(...), description: str = Form(...), price: float = Form(...),
                              count: int = Form(...), category: str = Form(...), file: UploadFile = File(...)):
    """
    Добавление нового товара. Выполняется проверка пользователя на наличие прав сотрудника. При подтверждении прав
    выполняется запись введённых пользователем данных о товаре.
    :param request: Запрос.
    :param user: Текущий пользователь
    :param name: Название товара
    :param item_number: Артикул товара
    :param description: Описание товара
    :param price: Цена товара
    :param count: Количество товара
    :param category: Идентификатор категории товара
    :param file: Изображение товара
    :return: Страницу списка товаров или страницу добавления товара с описанием ошибки
    """
    info = {'request': request, 'title': 'Добавление товара'}
    if user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        if name == '':
            info['message'] = 'Поле имя не может быть пустым'
        try:
            if not os.path.exists("./app/templates/product/image/" + name):
                os.mkdir("./app/templates/product/image/" + name)

            contents = file.file.read()
            file_name = file.filename
            with open("./app/templates/product/image/" + name + '/' + file_name, "wb") as f:
                f.write(contents)
        except Exception:
            raise HTTPException(status_code=500, detail='Something went wrong')
        finally:
            file.file.close()
        image = Image.open("./app/templates/product/image/" + name + '/' + file_name)
        image.thumbnail(size=(100, 100))
        image.save("./app/templates/product/image/" + name + '/small_' + file_name)
        cat = await get_category_model(int(category))
        await ProductModel.create(name=name, description=description,
                                  price=price, count=count,
                                  category=cat, item_number=item_number,
                                  img=file_name)
        return RedirectResponse('/product/list', status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse('add_product_page.html', info)


@product_router.get('/create')
async def create_product_get(request: Request,
                             user: Annotated[user_pydantic, Depends(get_current_user)]):
    """
    Добавление нового товара. Выполняется проверка пользователя на наличие прав сотрудника. 
    В случае наличия прав сотрудника отображается страница с формой для добавления товара, иначе страница с
    описанием ошибки. 
    :param request: Запрос.
    :param user: Текущий пользователь.
    :return: Страница добавления товара.
    """
    info = {'request': request, 'title': 'Добавление товара'}
    if user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        info['categories'] = await get_categories()
    return templates.TemplateResponse('/add_product_page.html', info)


@product_router.post('/update_product/{id_product}')
async def update_product_post(request: Request, user: Annotated[user_pydantic, Depends(get_current_user)],
                              id_product: int = -1, item_number: str = Form(...), description: str = Form(...),
                              price: float = Form(...),
                              count: int = Form(...), category: str = Form(...), is_active: str = ''):
    """
    Изменение данных о товаре. Запись данных о товаре, введённых пользователем при наличии у него прав.
    :param is_active: Статус доступности товара
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :param user: Текущий пользователь.
    :param item_number: Артикул товара.
    :param description: Описание товара.
    :param price: Цена товара.
    :param count: Количество товара.
    :param category: Идентификатор категории товара.
    :return: Страница с информацией о товаре.
    """
    if user is not None and user.is_staff:
        categories = await get_categories()
        cat = await get_category(categories, category)
        await ProductModel.filter(id=id_product).update(description=description, price=price, count=count,
                                                        is_active=is_active == 'Да', category=cat,
                                                        item_number=item_number)
        return RedirectResponse(f'/product/{id_product}', status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(f'/product/{id_product}')


@product_router.get('/update_product/{id_product}')
async def update_product_get(request: Request, user: Annotated[user_pydantic, Depends(get_current_user)],
                             id_product: int = -1):
    """
    Отображение страницы с формой для изменения данных о товаре
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :param user: Текущий пользователь.
    :return: Страница с формой изменения данных о товаре или переадресация на страницу входа в систему или 
    на список товара.
    """
    info = {'request': request, 'title': 'Изменение описания товара'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/product/list')
    else:
        product = await product_pydantic.from_queryset_single(ProductModel.get(id=id_product))
        info['categories'] = await get_categories()
        info['product'] = product
        info['display'] = 'Ok'
        info['image_str'], info['format_file'] = image_to_str(product, 'page')
        return templates.TemplateResponse('update_product_page.html', info)


@product_router.post('/update_image_product/{id_product}')
async def update_image_product_post(request: Request, user: Annotated[user_pydantic, Depends(get_current_user)],
                                    id_product: int = -1, file: UploadFile = Form(...)):
    """
    Изменение изображения товара. Запись нового изображения товара только при наличии прав.
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :param user: Текущий пользователь.
    :param file: Новое изображение товара.
    :return: Страница с отображением данных о товаре.
    """
    if user is not None and user.is_staff:
        product = await ProductModel.get_or_none(id=id_product)
        try:
            if not os.path.exists("./app/templates/product/image/" + product.name):
                os.mkdir("./app/templates/product/image/" + product.name)
            else:
                os.remove("./app/templates/product/image/" + product.name + '/' + product.img)
                os.remove("./app/templates/product/image/" + product.name + '/small_' + product.img)

            contents = file.file.read()
            file_name = file.filename
            with open("./app/templates/product/image/" + product.name + '/' + file_name, "wb") as f:
                f.write(contents)
        except Exception:
            raise HTTPException(status_code=500, detail='Something went wrong')
        finally:
            file.file.close()
        image = Image.open("./app/templates/product/image/" + product.name + '/' + file_name)
        image.thumbnail(size=(100, 100))
        image.save("./app/templates/product/image/" + product.name + '/small_' + file_name)
        await ProductModel.filter(id=id_product).update(img=file_name)
        return RedirectResponse(f'/product/{id_product}', status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(f'/product/{id_product}')


@product_router.get('/update_image_product/{id_product}')
async def update_image_product_get(request: Request, user: Annotated[user_pydantic, Depends(get_current_user)],
                                   id_product: int = -1):
    """
    Изменение изображения товара. Отображение страницы изменения изображения товара только при наличии прав.
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :param user: Текущий пользователь.
    :return: Страница изменения изображения о товаре или страница входа в систему или страница со списком товаров
    """
    info = {'request': request, 'title': 'Изменение описания товара'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/product/list')
    else:
        product = await ProductModel.filter(id=id_product).first()
        info['categories'] = await get_categories()
        info['product'] = product
        info['display'] = 'Ok'
        info['image_str'], info['format_file'] = image_to_str(product, 'page')
        return templates.TemplateResponse('update_image_product_page.html', info)


@product_router.post('/delete/{id_product}')
async def delete_product_post(request: Request, user: Annotated[user_pydantic, Depends(get_current_user)],
                              id_product: int = -1):
    """
    Удаление товара. Деактивация товара из базы данных. Если текущий пользователь имеет права сотрудника, то
    возможно деактивация товара.
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :param user: Текущий пользователь.
    :return: Страница со списком товаров: если удаление прошло успешно или у пользователя нет прав на удаление или
    страница удаления с сообщением об использовании.
    """
    info = {'request': request, 'title': 'Удаление товара'}
    if user is None:
        return RedirectResponse('/user/login')
    elif user.is_staff:
        await ProductModel.filter(id=id_product).update(is_active=False)
    return RedirectResponse(f'/product/list', status_code=status.HTTP_303_SEE_OTHER)


@product_router.get('/delete/{id_product}')
async def delete_product_get(request: Request, user: Annotated[user_pydantic, Depends(get_current_user)],
                             id_product: int = -1):
    """
    Удаление товара. Отображение страницы удаления товара при наличии прав сотрудника. Отображение
    страницы входа в систему если пользователь не авторизован. Отображение страницы со списком товаров если у
    пользователя нет прав на удаление.
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :param user: Текущий пользователь.
    :return: Страница удаления товара или страница входа в систему или страница со списком товаров.
    """
    info = {'request': request, 'title': 'Удаление товара'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not (user.is_staff or user.admin):
        return RedirectResponse('/product/list')
    else:
        product = await ProductModel.get_or_none(id=id_product)
        product_use = await check_use_product(id_product)
        if product_use:
            info['message'] = 'Товар уже покупали. Для удаления нужны права администратора'
        categories = await get_categories()
        info['category'] = find_category(categories, product.category)
        info['product'] = product
        info['display'] = 'Ok'
        info['image_str'], info['format_file'] = image_to_str(product, 'page')
        return templates.TemplateResponse('delete_product_page.html', info)


@product_router.get('/{id_product}')
async def select_product_get(request: Request, user: Annotated[user_pydantic, Depends(get_current_user)],
                             id_product: str = '-1'):
    """
    Отображение информации о товаре если он существует в базе или сообщение об ошибке.
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :param user: Текущий пользователь.
    :return: Страница с информацией о товаре или сообщение об ошибке.
    """
    info = {'request': request, 'title': 'Описание товара'}
    product = await ProductModel.get_or_none(id=id_product)
    if product:
        categories = await get_categories()
        info['product_category'] = find_category(categories, product.category)
        info['product'] = product
        info['image_str'], info['format_file'] = image_to_str(product, 'page')
        if user is not None:
            info['is_staff'] = user.is_staff
            info['user'] = True
    else:
        return HTTPException(status.HTTP_404_NOT_FOUND, detail='Товар отсутствует')
    return templates.TemplateResponse('product_page.html', info)
