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
from app.shemas import Product, Category, Car, Shop, Category_pydantic, Product_pydantic, Shop_pydantic
from app.routers.users import get_current_user
import base64
import os
from PIL import Image

product_router = APIRouter(prefix='/product', tags=['product'])
templates = Jinja2Templates(directory='templates/product/')

# корзины для покупки
cars = {}


def pagination(list_product: list, page: int, size: int):
    offset_min = page * size
    offset_max = (page + 1) * size
    result = list_product[offset_min:offset_max], {
        "page": page,
        "size": size,
        "total": math.ceil(len(list_product) / size) - 1,
    }
    return result


def image_to_str(product: Product, key: str):
    if key == 'list':
        file_path = os.path.join("./templates/product/image/" + product.name, 'small_' + product.img)
    else:
        file_path = os.path.join("./templates/product/image/" + product.name, product.img)
    #print(os.path.exists(file_path), file_path)
    try:
        with open(file_path, "rb") as image_file:
            contents = image_file.read()
        base64_encoded_image = base64.b64encode(contents).decode("utf-8")
        _, format_file = os.path.splitext(file_path)
    except Exception:
        base64_encoded_image = ''
    format_file = 'jpeg'
    #print(base64_encoded_image)
    return base64_encoded_image, format_file


def get_categories_subgroups(list_categories, id_category):
    result = []
    for category in list_categories:
        if category.parent == id_category:
            result.append(category)
    return result


def get_category(list_categories, id_category):
    for category in list_categories:
        if category.id == id_category:
            return category
    return None


def find_category(categories, id_category):
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
                              curent_user: Annotated[User, Depends(get_current_user)]):
    info = {'request': request, 'title': 'Список категорий'}
    if curent_user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not curent_user.is_staff:
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
    info = {'request': request, 'title': 'Создание категории'}
    print('create', name, parent)
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
    info = {'request': request, 'title': 'Удаление категории'}
    if curent_user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not curent_user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        info['id_category'] = id_category
        categories = await Categories.all()
        category = get_category(categories,id_category)
        info['name'] = category.name
        children = get_categories_subgroups(categories,id_category)
        if len(children) > 0:
            info['message'] = 'Удаление запрещено. Имеются связанные категории'
            info['children'] = children
        else:
            info['delete'] = 1
    return templates.TemplateResponse('category_delete.html', info)


@product_router.post('/category/delete/{id_category}')
async def delete_category_post(request: Request,
                               curent_user: Annotated[User, Depends(get_current_user)], id_category: int):
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
async def category_get(request: Request, id_category: int):
    info = {'request': request, 'title': 'Описание категории'}
    categories = await Categories.all()
    category = await Categories.filter(id=id_category).first()
    if isinstance(category, _NoneAwaitable):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Категория не найдена')
    if isinstance(category.parent, _NoneAwaitable):
        pass
    else:
        info['parent'] = get_category(categories, category.parent)
    info['category'] = category
    info['categories'] = categories
    return templates.TemplateResponse('category.html', info)


# Обработка таблицы Product
@product_router.get('/list')
async def select_products_list_get(request: Request,
                                   user: Annotated[User, Depends(get_current_user)], category: str = '', q: str = '',
                                   page: str = ''):
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
        print('Только имя', q)
        querty = Q(name__icontains = q)
        querty = querty | Q(description__icontains = q)
        print(querty)
        products = await ProductModel.filter(querty).all()
    elif category != '':
        products = await ProductModel.filter(category=int(category)).all()
    else:
        products = await ProductModel.all()
    if products is not None:
        product_list = []
        for product in products:
            print(product.name)
            image_str, format_file = image_to_str(product, 'list')
            #print(product.name, image_str)
            product_list.append({'name': product.name, 'price': product.price, 'id': product.id, 'image_str': image_str,
                                 'format_file': format_file})
        info['products'], service = pagination(product_list, page, 4)
        print(service)
        pages = [x for x in range(service['total'] + 1)]
        info['service'] = {'page': service['page'], 'size': service['size'], 'pages': pages}
        print(info['service'])
    return templates.TemplateResponse('product_list_page.html', info)


# Создание нового продукты
@product_router.post('/create')
async def create_product_post(request: Request,
                              user: Annotated[User, Depends(get_current_user)], name: str = Form(...),
                              item_number: str = Form(...), description: str = Form(...), price: float = Form(...),
                              count: int = Form(...), category: str = Form(...), file: UploadFile = File(...)):
    info = {'request': request, 'title': 'Добавление товара'}
    print(name, item_number, description, price, count, category, file.filename)

    if user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        if name == '':
            info['message'] = 'Поле имя не может быть пустым'
        try:
            if not os.path.exists("./templates/product/image/" + name):
                os.mkdir("./templates/product/image/" + name)

            contents = file.file.read()
            file_name = file.filename
            with open("./templates/product/image/" + name + '/' + file_name, "wb") as f:
                f.write(contents)
        except Exception:
            raise HTTPException(status_code=500, detail='Something went wrong')
        finally:
            file.file.close()
        image = Image.open("./templates/product/image/" + name + '/' + file_name)
        image.thumbnail(size=(100, 100))
        image.save("./templates/product/image/" + name + '/small_' + file_name)
        if count > 0:
            bl = True
        else:
            bl = False
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
async def update_product_post(request: Request, id_product: int = -1,
                              user=Depends(get_current_user),
                              item_number: str = Form(...), description: str = Form(...), price: float = Form(...),
                              count: int = Form(...), category: str = Form(...)):
    if user is not None and user.is_staff:
        cat = await Categories.get(id=int(category))
        await ProductModel.filter(id=id_product).update(description=description, price=price, count=count,
                                                        is_active=count > 0, category=cat, item_number=item_number)
        return RedirectResponse(f'/product/{id_product}', status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(f'/product/{id_product}')


@product_router.get('/update_product/{id_product}')
async def update_product_get(request: Request, id_product: int = -1,
                             user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Изменение описания товара'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/product/list')
    else:
        product = await ProductModel.get(id=id_product)
        info['categories'] = list(await Category_pydantic.from_queryset(Categories.all()))
        info['product'] = product
        info['display'] = 'Ok'
        info['image_str'], info['format_file'] = image_to_str(product, 'page')
        return templates.TemplateResponse('update_product_page.html', info)


@product_router.post('/update_image_product/{id_product}')
async def update_product_post(request: Request, id_product: int = -1,
                              user=Depends(get_current_user), file: UploadFile = Form(...)):
    info = {'request': request, 'title': 'Изменение описания товара'}
    if user is not None and user.is_staff:
        product = await ProductModel.get(id=id_product)
        print(product.name)
        try:
            if not os.path.exists("./templates/product/image/" + product.name):
                os.mkdir("./templates/product/image/" + product.name)

            contents = file.file.read()
            file_name = file.filename
            with open("./templates/product/image/" + product.name + '/' + file_name, "wb") as f:
                f.write(contents)
        except Exception:
            raise HTTPException(status_code=500, detail='Something went wrong')
        finally:
            file.file.close()
        image = Image.open("./templates/product/image/" + product.name + '/' + file_name)
        image.thumbnail(size=(100, 100))
        image.save("./templates/product/image/" + product.name + '/small_' + file_name)
        await ProductModel.filter(id=id_product).update(img=file_name)
        return RedirectResponse(f'/product/{id_product}', status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(f'/product/{id_product}')


@product_router.get('/update_image_product/{id_product}')
async def update_product_get(request: Request, id_product: int = -1,
                             user=Depends(get_current_user)):
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
async def delete_product_post(request: Request, id_product: int = -1,
                              user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Удаление товара'}
    if user is not None and user.is_staff:
        product_use = await BuyerProd.filter(
            product=id_product).all()  #db.scalars(select(BuyerProd).where(BuyerProd.product == id_product)).all()
        product = await ProductModel.filter(
            id=id_product).first()  #db.scalar(select(ProductModel).where(ProductModel.id == id_product))
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
async def delete_product_get(request: Request, id_product: int = -1,
                             user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Удаление товара'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/product/list')
    else:
        product = await ProductModel.filter(id=id_product).first()
        categories = list(await Category_pydantic.from_queryset(Categories.all()))
        info['category'] = find_category(categories, product.category)
        info['product'] = product
        info['display'] = 'Ok'
        info['image_str'], info['format_file'] = image_to_str(product, 'page')
        return templates.TemplateResponse('delete_product_page.html', info)


@product_router.get('/{id_product}')
async def select_product_get(request: Request, id_product: int = -1,
                             user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Описание товара'}
    product = await ProductModel.filter(id=id_product).first()
    if product is not None:
        categories = await product.category.first()
        info['product_category'] = categories.name
        info['product'] = product
        info['image_str'], info['format_file'] = image_to_str(product, 'page')
        if user is not None:
            info['is_staff'] = user.is_staff
    else:
        return HTTPException(status.HTTP_404_NOT_FOUND, detail='Товар отсутствует')
    return templates.TemplateResponse('product_page.html', info)


@product_router.post('/car/{id_product}')
async def car_post(request: Request, id_product: int = -1,
                   car_user: Car = Form(), user=Depends(get_current_user)):
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
            info['message'] = 'Не достаточно товара'
            info['count'] = product.count
        else:
            await ProductModel.filter(id=id_product).update(count=new_count)
            product = await ProductModel.filter(id=id_product).first()
        info['product'] = product
        if user.id in cars.keys():
            cars[user.id].append((product.id, product.name, product.price, car_user.count))
        else:
            cars[user.id] = [(product.id, product.name, product.price, car_user.count), ]
        return templates.TemplateResponse('car.html', info)
    return RedirectResponse('/product')


@product_router.get('/car/{id_product}')
async def car_get(request: Request, id_product: int = -1,
                  user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Корзина'}
    if user is None:
        return RedirectResponse(f'/product/{id_product}', status_code=status.HTTP_303_SEE_OTHER)
    product = await ProductModel.filter(id=id_product).first()
    if product is None:
        return HTTPException(status.HTTP_404_NOT_FOUND, 'Товар не найден')
    info['product'] = product
    info['user'] = user
    info['count'] = 1
    return templates.TemplateResponse('car.html', info)


@product_router.get('/buy/{user_id}')
async def buy_get(request: Request, user_id: int = -1, delet: int = -1,
                  shop: str = '', user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Оплата товара'}
    cost = 0
    if delet > -1:
        for i in range(len(cars[user_id])):
            if cars[user_id][i][0] == delet:
                product = await ProductModel.filter(id=delet).first()
                await ProductModel.filter(id=delet).update(count=product.count + cars[user_id][i][3], is_active=True)
                cars[user_id].pop(i)
    if user_id not in cars.keys():
        return RedirectResponse('/product/list', status_code=status.HTTP_303_SEE_OTHER)
    car = cars[user_id]
    info['car'] = car
    info['user'] = user
    info['shops'] = await Shops.all()
    for item in car:
        cost += item[2] * item[3]
    info['cost'] = cost
    return templates.TemplateResponse('buy.html', info)


@product_router.post('/buy/{user_id}')
async def buy_post(request: Request, user_id: int = -1,
                   user=Depends(get_current_user), shop: str = Form(...)):
    info = {'request': request, 'title': 'Оплата товара'}
    cost = 0
    car = cars[user_id]
    info['car'] = car
    info['user'] = user
    for item in car:
        cost += item[2] * item[3]
    info['cost'] = cost
    print(shop)
    if shop == '':
        info['message'] = 'Выберите магазин'
        return templates.TemplateResponse('buy.html', info)

    return RedirectResponse(f'/product/payment/{user_id}?shop={shop}', status_code=status.HTTP_303_SEE_OTHER)


@product_router.get('/payment/{user_id}')
async def payment_get(request: Request, user_id: int = -1, shop: str = '',
                      user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Оплата товара'}
    cost = 0
    car = cars[user_id]
    info['car'] = car
    info['user'] = user
    for item in car:
        cost += item[2] * item[3]
    info['cost'] = cost
    shop = await Shops.get(id = int(shop))
    info['shop'] = shop
    return templates.TemplateResponse('payment.html', info)


@product_router.post('/payment/{user_id}')
async def payment_post(request: Request, user_id: int = -1,
                       user=Depends(get_current_user), shop: str = ''):
    max_operation = (await BuyerProd.annotate(max_operation=Max("id_operation")).values_list("max_operation", flat=True))[0]
    #max_operation = Max(BuyerProd.all().fields('id_operation'))
    if max_operation is None:
        max_operation = 1
    else:
        max_operation = max_operation + 1
    shop_sel = await Shops.get(id = int(shop))
    for item in cars[user_id]:
        prod = await ProductModel.get(id=item[0])
        await BuyerProd.create(user=user, product=prod, id_operation=max_operation, id_shop=shop_sel)
    cars.pop(user_id)
    return HTMLResponse('Спасибо за покупку')


@product_router.get('/shop/create')
async def create_shop_get(request: Request,
                          user=Depends(get_current_user)):
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
async def update_shop_get(request: Request, shop_id: int = -1,
                          user=Depends(get_current_user)):
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
async def update_shop_post(request: Request, shop: Shop = Form(),
                           shop_id: int = -1, user=Depends(get_current_user)):
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
async def delete_shop_get(request: Request, shop_id: int = -1,
                          user=Depends(get_current_user)):
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
async def delete_shop_post(request: Request,
                           shop_id: int = -1, user=Depends(get_current_user)):
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
async def select_shop_get(request: Request,
                          user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Список магазинов'}
    shops = await Shops.all()
    if user is None:
        pass
    elif user.is_staff:
        info['display'] = 'Ok'
    info['shops'] = shops
    return templates.TemplateResponse('shop_list_page.html', info)


@product_router.get('/shop/{shop_id}')
async def select_shop_get(request: Request, shop_id: int = -1,
                          user=Depends(get_current_user)):
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
