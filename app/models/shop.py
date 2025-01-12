from tortoise import fields, models


class Shops(models.Model):
    """
    Класс - описание магазина
    """
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255, unique=True)
    location = fields.TextField()
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = 'shops'
