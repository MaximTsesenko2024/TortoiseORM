from tortoise import fields, models


class ProductModel(models.Model):
    """
    Класс описания товара в системе
    """
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
