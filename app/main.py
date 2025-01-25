import uvicorn
from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from tortoise.contrib.fastapi import register_tortoise
from typing import Annotated
from .backend.db.db import tortoise_orm
from .shemas import user_pydantic
from .depends import get_current_user, get_categories
from .routers.users import user_router
from .routers.product import product_router
from .routers.shop import shop_router
from .routers.category import category_router
from .routers.buy import buy_router

templates = Jinja2Templates(directory='app/templates/product')

api = FastAPI()
api.mount("/app/static", StaticFiles(directory="app/static"), name="static")
register_tortoise(api,
                  config=tortoise_orm,
                  generate_schemas=True, add_exception_handlers=True)


@api.get('/')
async def redirect():
    """
    Переадресация на главную страницу.+
    """
    return RedirectResponse('/main')


@api.get('/main')
async def welcome(request: Request, user: Annotated[user_pydantic, Depends(get_current_user)], category: int = -1,
                  q: str = ''):
    """
    Главная страница, обеспечение маршрутизации задач по управлению пользователями и управлению товарами
    :param request: запрос от пользователя к системе
    :param user: текущий пользователь
    :param category: выбранная категория товара
    :param q: строка для поиска товара по названию или описанию
    :return: страница html - для общения с пользователем
    """
    info = {'request': request, 'title': 'Главная страница'}
    if user is not None:
        info['name'] = user.username
        info['is_staff'] = user.is_staff
        info['user_id'] = user.id
        info['admin'] = user.admin
    else:
        info['name'] = 'Вход не выполнен'
    categories = await get_categories()
    if categories is not None:
        info['categories'] = categories
    if category > -1 and q != '':
        return RedirectResponse(f"/product/list?category={category}&q={q}")
    elif category > -1:
        return RedirectResponse(f"/product/list?category={category}")
    elif q != '':
        return RedirectResponse(f"/product/list?q={q}")
    return templates.TemplateResponse("main.html", info)


api.include_router(user_router)  # подключение маршрутов управления пользователями
api.include_router(product_router)  # подключение маршрутов управления товарами
api.include_router(shop_router)  # подключение маршрутов управления магазинами
api.include_router(category_router)  # подключение маршрутов управления категорий
api.include_router(buy_router)  # подключение маршрутов покупки товаров


if __name__ == "__main__":
    uvicorn.run(api, host="127.0.0.1", port=8000, log_level="info")
