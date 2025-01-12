from app.models.buy import BuyerProd


async def check_use_product(product: int):
    """
    Проверка наличия покупки выбранного товара
    :param product: Идентификатор товара
    :return: True - есть товар покупали, False - нет
    """
    count = await BuyerProd.filter(product=int(product)).count()
    if count > 0:
        return True
    else:
        return False
