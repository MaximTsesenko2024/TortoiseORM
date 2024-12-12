from tortoise import Tortoise
from app.models import users, product


async def get_user():
    user = await users.User.create()
    try:
        yield user
    finally:
        await Tortoise.close_connections()


async def get_product():
    prod = await product.ProductModel.create()
    try:
        yield prod
    finally:
        await Tortoise.close_connections()


async def get_category():
    category = await product.Categories.create()
    try:
        yield category
    finally:
        await Tortoise.close_connections()


async def get_shop():
    shop = await product.Shops.create()
    try:
        yield shop
    finally:
        await Tortoise.close_connections()


async def get_buer_prod():
    buer_prod = await product.BuyerProd.create()
    try:
        yield buer_prod
    finally:
        await Tortoise.close_connections()


TORTOISE_ORM = {
    "connections": {"default": 'sqlite://shop_db.db'},
    "apps": {
        "models": {
            "models": ["app.models.users", "app.models.product"],
            "default_connection": "default",
        },
    },
}


# async def connectToDatabase():
#     await Tortoise.init(config=TORTOISE_ORM)
#     print(Tortoise.get_connection("default"))
