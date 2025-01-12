from ..models.category import Categories
from ..shemas import category_pydantic


def get_categories_subgroups(list_categories, id_category) -> list[category_pydantic]:
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


def get_category(list_categories, id_category) -> category_pydantic | None:
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


async def get_category_model(id_category) -> Categories | None:
    """
    Получение объекта категория по идентификатору
    :param id_category: Идентификатор категории
    :return: Объект категория или None
    """
    return await Categories.get_or_none(id=id_category)


def find_category(categories, id_category) -> str:
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


async def get_categories():
    """
    Получение списка категорий введённых в базу
    :return: Список категорий
    """
    categories = await category_pydantic.from_queryset(Categories.all())
    if not categories:
        return None
    return categories
