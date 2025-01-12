from tortoise import fields, models


class BuyerProd(models.Model):
    """
    Класс - описание покупки товара пользователем
    """
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

    is_used = fields.BooleanField(default=False)
    count = fields.IntField(nullable=False)

    class Meta:
        table = 'buyer'
