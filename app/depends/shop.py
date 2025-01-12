from ..models.shop import Shops
from ..shemas import shop_pydantic


async def get_shop(shop_id: int) -> shop_pydantic | None:
    """
    Получение объекта магазин по его идентификатору
    :param shop_id: Идентификатор объекта магазин
    :return: объект магазин или None
    """
    return await shop_pydantic.from_queryset_single(Shops.filter(is_active=True, id=shop_id).first())


async def get_shop_model(shop_id: int) -> Shops | None:
    """
    Получение объекта магазин по его идентификатору
    :param shop_id: Идентификатор объекта магазин
    :return: объект магазин или None
    """
    return await Shops.get_or_none(id=shop_id)


async def get_shop_list() -> list[shop_pydantic]:
    """
    Получение списка доступных магазинов
    :return: Список магазинов
    """
    shop_list = await shop_pydantic.from_queryset(Shops.filter(is_active=True).all())
    if shop_list is not None:
        shop_list = list(shop_list)
    return shop_list
