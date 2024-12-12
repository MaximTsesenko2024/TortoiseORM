from tortoise import Tortoise, fields, models


class ProductModel(models.Model):
    id = fields.IntField(primary_key=True)
    # наименование товара
    name = fields.CharField(max_length=256, index=True)
    # Описание товара
    description = fields.TextField()
    # артикул товара
    item_number = fields.CharField(max_length=256)
    # стоимость товара
    price = fields.FloatField()
    # доступное количество товара
    count = fields.IntField()
    # признак наличия товара
    is_active = fields.BooleanField(default=True)
    # участие в акции
    action = fields.BooleanField(default=False)
    # картинка товара
    img = fields.TextField()
    # категория товаров
    category = fields.ForeignKeyField(
        model_name="models.Categories",
        on_delete=fields.CASCADE,
    )

    class Meta:
        table = "products"


class BuyerProd(models.Model):
    id = fields.IntField(primary_key=True)
    id_operation = fields.IntField(nullable=False)
    user = fields.ForeignKeyField(
        model_name="models.User",
        on_delete=fields.CASCADE,
    )
    product = fields.ForeignKeyField(
        model_name="models.ProductModel",
        on_delete=fields.CASCADE,
    )

    id_shop = fields.ForeignKeyField(
        model_name="models.Shops",
        on_delete=fields.CASCADE,
    )

    class Meta:
        table = 'buyer'


class Categories(models.Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255, unique=True)
    parent = fields.IntField(default=-1)

    class Meta:
        table = 'categories'


class Shops(models.Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255, unique=True)
    location = fields.TextField()

    class Meta:
        table = 'shops'
