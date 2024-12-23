import math
from tortoise.expressions import RawSQL, Q
from tortoise.fields.relational import _NoneAwaitable
from tortoise.functions import Max
from fastapi import File, UploadFile, APIRouter, Depends, status, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Annotated
from app.models.product import ProductModel, BuyerProd, Categories, Shops
from fastapi.templating import Jinja2Templates
from app.models.users import User
from app.shemas import Product, Category, Car, Shop, Category_pydantic, Product_pydantic, Shop_pydantic, Payment
from app.routers.users import get_current_user
import base64
import os
from PIL import Image

product_router = APIRouter(prefix='/product', tags=['product'])
templates = Jinja2Templates(directory='app/templates/product/')


class CarView:
    def __init__(self, number, id_prod, name, price, count):
        self.number = number
        self.id_prod = id_prod
        self.name = name
        self.price = price
        self.count = count


# корзины для покупки
cars = {}


def pagination(list_product: list, page: int, size: int):
    """
    Разделение элементов списка на страницы по заданному количеству и вывод части списка,
    соответствующего номеру переданной страницы.
    :param list_product: Список элементов, который необходимо разбить на страницы.
    :param page: Номер страницы.
    :param size: Количество элементов на странице.
    :return: Список элементов исходного списка соответствующий на указанной странице.
    """
    offset_min = page * size
    offset_max = (page + 1) * size
    if offset_min > len(list_product):
        if size > len(list_product):
            offset_min = 0
        else:
            offset_min = len(list_product) - size
    if offset_max > len(list_product):
        offset_max = len(list_product)
    print(offset_min, offset_max)

    result = list_product[offset_min:offset_max], {
        "page": page,
        "size": size,
        "total": math.ceil(len(list_product) / size) - 1,
    }
    return result


def image_to_str(product: Product_pydantic, key: str):
    """
    Преобразование изображения в строку символов.
    :param product: Модель продукта для которого выполняется преобразование картинки в строку.
    :param key: Ключ определяющий размер картинки для отображения.
    :return: Строка символов соответствующая изображению переданному продукту.
    """
    if key == 'list':
        file_path = os.path.join("./app/templates/product/image/" + product.name, 'small_' + product.img)
    else:
        file_path = os.path.join("./app/templates/product/image/" + product.name, product.img)
    try:
        with open(file_path, "rb") as image_file:
            contents = image_file.read()
        base64_encoded_image = base64.b64encode(contents).decode("utf-8")
        _, format_file = os.path.splitext(file_path)
    except Exception:
        base64_encoded_image = ''
        format_file = 'jpeg'
    return base64_encoded_image, format_file


def get_categories_subgroups(list_categories, id_category):
    """
    Получение списка подкатегорий для категории указанной идентификатором.
    :param list_categories: Список всех категорий
    :param id_category: Идентификатор категории
    :return: Список категорий для которых указанный идентификатор является родительским
    """
    result = []
    for category in list_categories:
        if category.parent == id_category:
            result.append(category)
    return result


def get_category(list_categories, id_category):
    """
    Получение объекта категория по идентификатору
    :param list_categories: Список всех категорий
    :param id_category: Идентификатор категории
    :return: Объект категория или None
    """
    for category in list_categories:
        if category.id == id_category:
            return category
    return None


def find_category(categories, id_category):
    """
    Вывод зависимости категорий для указанного идентификатора
    :param categories: Список всех категорий
    :param id_category: Идентификатор категории
    :return: строка представляющая цепочку родителей для указанной категории
    """
    if id_category is None or id_category == -1:
        return ''
    for category in categories:
        if category.id == id_category:
            if category.parent is None or category.parent == -1:
                return category.name
            else:
                return find_category(categories, category.parent) + ' / ' + category.name
    return ''


# Обработка таблицы Categories
# просмотр списка категорий
@product_router.get('/category/list')
async def list_categories_get(request: Request,
                              user: Annotated[User, Depends(get_current_user)]):
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
@product_router.get('/category/update/{id_category}')
async def update_category_get(request: Request, id_category: int,
                              curent_user: Annotated[User, Depends(get_current_user)], parent: str = ''):
    """
    Изменение данных выбранной категории. Для изменения доступно только поле родительская категория.
    :param request: Запрос.
    :param id_category: Идентификатор выбранной категории.
    :param curent_user: Текущий пользователь
    :param parent: Идентификатор родительской категории
    :return: Страница с данными по выбранной категории
    """
    info = {'request': request, 'title': 'Обновление категории'}
    if curent_user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not curent_user.is_staff:
        info['message'] = 'У вас нет прав'
    elif parent == '':
        info['display'] = 'Ok'
        categories = list(await Category_pydantic.from_queryset(Categories.all()))
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
        return RedirectResponse(f'/product/category/{id_category}',
                                status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse('category_update.html', info)


# создание новой категории
@product_router.get('/category/create')
async def add_category_get(request: Request,
                           curent_user: Annotated[User, Depends(get_current_user)],
                           name: str = '', parent: str = ''):
    """
    Создание новой категории. При наличии прав сотрудника отображается форма для ввода данных новой категории,
    а если данные уже введены то список категорий.
    :param request: Запрос.
    :param curent_user: Текущий пользователь.
    :param name: Название новой категории или ''
    :param parent: Номер родительской категории или ''
    :return: Страница создания категории или переход к списку категорий
    """
    info = {'request': request, 'title': 'Создание категории'}
    if curent_user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not curent_user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        if name == '' and parent == '':
            categories = await Category_pydantic.from_queryset(Categories.all())
            if categories is not None:
                info['categories'] = categories
        elif name == '':
            info['message'] = 'Поле название не может быть пустым'
        elif parent == '':
            info['message'] = 'Поле родительская категория не может быть пустым'
        else:
            await Categories.create(name=name, parent=int(parent))
            return RedirectResponse('/product/category/list')
    return templates.TemplateResponse('category_create.html', info)


# удаление категории
@product_router.get('/category/delete/{id_category}')
async def delete_category_get(request: Request,
                              curent_user: Annotated[User, Depends(get_current_user)], id_category: int):
    """
    Запрос на удаление выбранной категории. Если текущий пользователь имеет права сотрудника, то отображаются данные
    выбранной категории с запросом на подтверждение удаления категории. Если пользователь не определён или у него нет
    прав сотрудника, то отобразится пустая страница с сообщением.
    :param request: Запрос.
    :param curent_user: Текущий пользователь
    :param id_category: Идентификатор выбранной категории
    :return: Страница удаления категории
    """
    info = {'request': request, 'title': 'Удаление категории'}
    if curent_user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not curent_user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        info['id_category'] = id_category
        categories = await Categories.all()
        category = get_category(categories, id_category)
        products = ProductModel.objects.get_or_none(category=category)
        info['name'] = category.name
        children = get_categories_subgroups(categories, id_category)
        if len(children) > 0:
            info['message'] = 'Удаление запрещено. Имеются связанные категории'
            info['children'] = children
        elif products is not None:
            info['message'] = 'Удаление запрещено. Категория уже используется'
        else:
            info['delete'] = 1
    return templates.TemplateResponse('category_delete.html', info)


@product_router.post('/category/delete/{id_category}')
async def delete_category_post(request: Request,
                               curent_user: Annotated[User, Depends(get_current_user)], id_category: int):
    """
    Выполнение удаления категории из базы данных. Если текущий пользователь имеет права сотрудника, то выполниться
    удаление выбранной категории. Если пользователь не определён или у него нет прав сотрудника,
    то отобразится пустая страница с сообщением.
    :param request: Запрос.
    :param curent_user: Текущий пользователь.
    :param id_category: Идентификатор выбранной категории
    :return: Страница со списком категорий либо страница удаления товара
    """
    info = {'request': request, 'title': 'Удаление категории'}
    if curent_user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not curent_user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        await Categories.filter(id=id_category).delete()
        return RedirectResponse('/product/category/list', status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse('category_delete.html', info)


# просмотр категории
@product_router.get('/category/{id_category}')
async def category_get(request: Request, curent_user: Annotated[User, Depends(get_current_user)], id_category: int):
    """
    Отображение данных выбранной категории. Если текущий пользователь имеет права сотрудника, то отобразятся данные
    выбранной категории. Если пользователь не определён или у него нет прав сотрудника,
    то отобразится пустая страница с сообщением.
    :param request: Запрос.
    :param curent_user: Текущий пользователь.
    :param id_category: Идентификатор выбранной категории
    :return: Страница описания категории
    """
    info = {'request': request, 'title': 'Описание категории'}
    if curent_user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not curent_user.is_staff:
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


# Обработка таблицы Product
@product_router.get('/list')
async def select_products_list_get(request: Request,
                                   user: Annotated[User, Depends(get_current_user)], category: str = '', q: str = '',
                                   page: str = ''):
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
        querty = Q(name__icontains=q)
        querty = querty | Q(description__icontains=q)
        products = await Product_pydantic.from_queryset(ProductModel.filter(querty).all())
    elif category != '':
        products = await Product_pydantic.from_queryset(ProductModel.filter(category=int(category)).all())
        print(category, len(products))
    else:
        products = await Product_pydantic.from_queryset(ProductModel.all())
    print('список')
    if products is not None:
        product_list = []
        for product in products:
            print(product.name)
            image_str, format_file = image_to_str(product, 'list')
            product_list.append({'name': product.name, 'price': product.price, 'id': product.id, 'image_str': image_str,
                                 'format_file': format_file})
        info['products'], service = pagination(product_list, page, 4)
        pages = [x for x in range(service['total'] + 1)]
        info['service'] = {'page': service['page'], 'size': service['size'], 'pages': pages}
        print(info['service'], info['products'])
        info['categories'] = await Category_pydantic.from_queryset(Categories.all())
    return templates.TemplateResponse('product_list_page.html', info)


# Создание нового продукты
@product_router.post('/create')
async def create_product_post(request: Request,
                              user: Annotated[User, Depends(get_current_user)], name: str = Form(...),
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
        cat = await Categories.get(id=int(category))
        await ProductModel.create(name=name, description=description,
                                  price=price, count=count,
                                  is_active=count > 0, category=cat, item_number=item_number,
                                  img=file_name)
        return RedirectResponse('/product/list', status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse('add_product_page.html', info)


@product_router.get('/create')
async def create_product_get(request: Request,
                             user: Annotated[User, Depends(get_current_user)]):
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
        info['categories'] = list(await Category_pydantic.from_queryset(Categories.all()))
    return templates.TemplateResponse('/add_product_page.html', info)


@product_router.post('/update_product/{id_product}')
async def update_product_post(request: Request, id_product: int = -1, user=Depends(get_current_user),
                              item_number: str = Form(...), description: str = Form(...), price: float = Form(...),
                              count: int = Form(...), category: str = Form(...)):
    """
    Изменение данных о товаре. Запись данных о товаре, введённых пользователем при наличии у него прав.
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
        cat = await Categories.get(id=int(category))
        await ProductModel.filter(id=id_product).update(description=description, price=price, count=count,
                                                        is_active=count > 0, category=cat, item_number=item_number)
        return RedirectResponse(f'/product/{id_product}', status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(f'/product/{id_product}')


@product_router.get('/update_product/{id_product}')
async def update_product_get(request: Request, id_product: int = -1,
                             user=Depends(get_current_user)):
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
        product = await Product_pydantic.from_queryset_single(ProductModel.get(id=id_product))
        info['categories'] = list(await Category_pydantic.from_queryset(Categories.all()))
        info['product'] = product
        info['display'] = 'Ok'
        info['image_str'], info['format_file'] = image_to_str(product, 'page')
        return templates.TemplateResponse('update_product_page.html', info)


@product_router.post('/update_image_product/{id_product}')
async def update_image_product_post(request: Request, id_product: int = -1, user=Depends(get_current_user),
                                    file: UploadFile = Form(...)):
    """
    Изменение изображения товара. Запись нового изображения товара только при наличии прав.
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :param user: Текущий пользователь.
    :param file: Новое изображение товара.
    :return: Страница с отображением данных о товаре.
    """
    info = {'request': request, 'title': 'Изменение описания товара'}
    if user is not None and user.is_staff:
        product = await ProductModel.get(id=id_product)
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
async def update_image_product_get(request: Request, id_product: int = -1, user=Depends(get_current_user)):
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
        info['categories'] = list(await Category_pydantic.from_queryset(Categories.all()))
        info['product'] = product
        info['display'] = 'Ok'
        info['image_str'], info['format_file'] = image_to_str(product, 'page')
        return templates.TemplateResponse('update_image_product_page.html', info)


@product_router.post('/delete/{id_product}')
async def delete_product_post(request: Request, id_product: int = -1, user=Depends(get_current_user)):
    """
    Удаление товара. Удаление данных о товаре из базы данных. Если текущий пользователь имеет права сотрудника, то
    возможно удаление товара, который ещё никто не покупал.  Если текущий пользователь имеет права администратора, то
    при удалении товара, также удаляются данные о его покупках если его покупали.
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :param user: Текущий пользователь.
    :return: Страница со списком товаров: если удаление прошло успешно или у пользователя нет прав на удаление или
    страница удаления с сообщением об использовании.
    """
    info = {'request': request, 'title': 'Удаление товара'}
    if user is not None and user.is_staff or user.admin:
        product_use = await BuyerProd.filter(product=id_product).all()
        product = await ProductModel.filter(id=id_product).first()
        if product_use is None:
            os.remove("./templates/product/image/" + product.name)
            await ProductModel.filter(id=id_product).delete()
            return RedirectResponse(f'/product/list', status_code=status.HTTP_303_SEE_OTHER)
        elif user.admin:
            await BuyerProd.filter(product=id_product).delete()
            os.remove("./templates/product/image/" + product.name)
            await ProductModel.filter(id=id_product).delete()
        else:
            info['message'] = 'Товар уже покупали. Для удаления обратитесь к администратору'
            return templates.TemplateResponse('delete_product_page.html', info)
    return RedirectResponse(f'/product/list', status_code=status.HTTP_303_SEE_OTHER)


@product_router.get('/delete/{id_product}')
async def delete_product_get(request: Request, id_product: int = -1, user=Depends(get_current_user)):
    """
    Удаление товара. Отображение страницы удаления товара при наличии прав сотрудника или администратора. Отображение
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
        product = await ProductModel.filter(id=id_product).first()
        categories = list(await Category_pydantic.from_queryset(Categories.all()))
        info['category'] = find_category(categories, product.category)
        info['product'] = product
        info['display'] = 'Ok'
        info['image_str'], info['format_file'] = image_to_str(product, 'page')
        return templates.TemplateResponse('delete_product_page.html', info)


@product_router.get('/buy')
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
                    product = await ProductModel.filter(id=cars[user.id][i].id_prod).first()
                    await ProductModel.filter(id=cars[user.id][i].id_prod).update(count=product.count + cars[user.id][i].count, is_active=True)
                    cars[user.id].pop(i)
                    break
        info['display'] = 1
        car = cars[user.id]
        info['car'] = car
        info['user'] = user
        info['shops'] = await Shops.all()
        for item in car:
            cost += item.price * item.count
        info['cost'] = cost
    return templates.TemplateResponse('buy.html', info)


@product_router.post('/buy')
async def buy_post(request: Request, user=Depends(get_current_user), shop: str = Form(...)):
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

    return RedirectResponse(f'/product/payment?shop={shop}', status_code=status.HTTP_303_SEE_OTHER)


@product_router.get('/payment')
async def payment_get(request: Request, shop: str = '', user=Depends(get_current_user)):
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
    shop = await Shops.get(id=int(shop))
    info['shop'] = shop
    return templates.TemplateResponse('payment.html', info)


@product_router.post('/payment')
async def payment_post(request: Request, pay: Payment = Form(), user=Depends(get_current_user), shop: str = ''):
    """
    Оплата товара. Выполнение оплаты.
    :param pay: Платёжные данные покупателя.
    :param request: Запрос.
    :param user: Текущий пользователь.
    :param shop: Идентификатор магазина.
    :return: Сообщение об оплате.
    """
    max_operation = \
        (await BuyerProd.annotate(max_operation=Max("id_operation")).values_list("max_operation", flat=True))[0]
    if max_operation is None:
        max_operation = 1
    else:
        max_operation = max_operation + 1
    shop_sel = await Shops.get(id=int(shop))
    for item in cars[user.id]:
        prod = await ProductModel.get(id=item.id_prod)
        await BuyerProd.create(user=user, product=prod, id_operation=max_operation, id_shop=shop_sel)
    cars.pop(user.id)
    print(pay.name, pay.card_number)
    return HTMLResponse(f'Спасибо за покупку. Заказ номер: {max_operation}')


@product_router.get('/{id_product}')
async def select_product_get(request: Request, id_product: str = '-1', user=Depends(get_current_user)):
    """
    Отображение информации о товаре если он существует в базе или сообщение об ошибке.
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :param user: Текущий пользователь.
    :return: Страница с информацией о товаре или сообщение об ошибке.
    """
    info = {'request': request, 'title': 'Описание товара'}
    print('product select')
    product = await ProductModel.filter(id=id_product).first()
    if product is not None:
        categories = await product.category.first()
        info['product_category'] = categories.name
        info['product'] = product
        info['image_str'], info['format_file'] = image_to_str(product, 'page')
        if user is not None:
            info['is_staff'] = user.is_staff
            info['user'] = True
    else:
        return HTTPException(status.HTTP_404_NOT_FOUND, detail='Товар отсутствует')
    return templates.TemplateResponse('product_page.html', info)


@product_router.post('/car/{id_product}')
async def car_post(request: Request, id_product: int = -1, car_user: Car = Form(), user=Depends(get_current_user)):
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
    product = await ProductModel.filter(id=id_product).first()
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
            await ProductModel.filter(id=id_product).update(count=new_count)
            product = await ProductModel.filter(id=id_product).first()
        info['product'] = product
        if user.id not in cars.keys():
            cars[user.id] = []

        cars[user.id].append(CarView(len(cars[user.id]), product.id, product.name, product.price, car_user.count))

        print(cars)
    return templates.TemplateResponse('car.html', info)


@product_router.get('/car/{id_product}')
async def car_get(request: Request, id_product: int = -1, user=Depends(get_current_user)):
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
    product = await ProductModel.filter(id=id_product).first()
    if product is None:
        return HTTPException(status.HTTP_404_NOT_FOUND, 'Товар не найден')
    info['product'] = product
    info['user'] = user
    info['count'] = 1
    info['buy'] = 1
    return templates.TemplateResponse('car.html', info)


# Обработка таблицы Shops
@product_router.get('/shop/create')
async def create_shop_get(request: Request, user=Depends(get_current_user)):
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


@product_router.post('/shop/create')
async def create_shop_post(request: Request, shop: Shop = Form(),
                           user=Depends(get_current_user)):
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
        return RedirectResponse('/product/shop/list', status_code=status.HTTP_303_SEE_OTHER)


@product_router.get('/shop/update/{shop_id}')
async def update_shop_get(request: Request, shop_id: int = -1, user=Depends(get_current_user)):
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
            return RedirectResponse('/product/shop/list')
        info['shop'] = shop
        return templates.TemplateResponse('update_shop_page.html', info)


@product_router.post('/shop/update/{shop_id}')
async def update_shop_post(request: Request, shop: Shop = Form(), shop_id: int = -1, user=Depends(get_current_user)):
    """
    Изменение данных магазина. Внесение изменений в базу данных и переход к списку магазинов, если пользователь - сотрудник.
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
        return RedirectResponse('/product/shop/list', status_code=status.HTTP_303_SEE_OTHER)


@product_router.get('/shop/delete/{shop_id}')
async def delete_shop_get(request: Request, shop_id: int = -1, user=Depends(get_current_user)):
    """
    Удаление магазина. Отображение формы с подтверждением удаления если пользователь сотрудник. Если пользователь не определён, то переход к странице входа в систему. Если пользователь не имеет прав сотрудника,
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
            return RedirectResponse('/product/shop/list')
        info['shop'] = shop
        return templates.TemplateResponse('delete_shop_page.html', info)


@product_router.post('/shop/delete/{shop_id}')
async def delete_shop_post(request: Request, shop_id: int = -1, user=Depends(get_current_user)):
    """
     Удаление магазина. Удаление магазина из базы данных и переадресация на список магазинов если пользователь сотрудник. Если пользователь не определён, то переход к странице входа в систему. Если пользователь не имеет прав сотрудника,
    то переход на главную страницу.
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
        await Shops.filter(id=shop_id).delete()
        return RedirectResponse('/product/shop/list', status_code=status.HTTP_303_SEE_OTHER)


@product_router.get('/shop/list')
async def select_shop_list_get(request: Request, user=Depends(get_current_user)):
    """
    Отображение страницы со списком магазинов.
    :param request: Запрос.
    :param user: Текущий пользователь.
    :return: Страница со списком магазинов.
    """
    info = {'request': request, 'title': 'Список магазинов'}
    shops = await Shops.all()
    if user is None:
        pass
    elif user.is_staff:
        info['display'] = 'Ok'
    info['shops'] = shops
    return templates.TemplateResponse('shop_list_page.html', info)


@product_router.get('/shop/{shop_id}')
async def select_shop_get(request: Request, shop_id: int = -1, user=Depends(get_current_user)):
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
        return RedirectResponse('/product/shop/list', status_code=status.HTTP_303_SEE_OTHER)
    info['shop'] = shop
    return templates.TemplateResponse('shop_page.html', info)
