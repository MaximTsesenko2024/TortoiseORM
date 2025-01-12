from ..models.product import ProductModel
from ..shemas import product_pydantic


async def check_use_category(category: int):
    """
    Проверка наличия товара выбранной категории
    :param category: Идентификатор категории
    :return: True - есть товар указанной категории, False - нет товара
    """
    count = await ProductModel.filter(category=int(category)).count()
    if count > 0:
        return True
    else:
        return False


async def get_product(product_id: int) -> product_pydantic | None:
    """
    Получение объекта продукт по идентификатору
    :param product_id: идентификатор объекта продукт
    :return: объекта продукт или None
    """
    return await product_pydantic.from_queryset_single(ProductModel.get_or_none(id=product_id))


async def get_product_model(product_id: int) -> ProductModel | None:
    """
    Получение объекта продукт по идентификатору
    :param product_id: идентификатор объекта продукт
    :return: объекта продукт или None
    """
    return await ProductModel.get_or_none(id=product_id)


async def update_count_product(product_id: int, update_count: int) -> bool:
    """
    Изменение количества товара
    :param product_id: Идентификатор товара.
    :param update_count: Изменение количества + увеличение, - уменьшение.
    :return статус операции
    """
    product = await ProductModel.filter(id=product_id).first()
    await ProductModel.filter(id=product_id).update(count=product.count+update_count)
    return True
