from tortoise import fields, models


class Categories(models.Model):
    """
    Класс - описание категории товара
    """
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255, unique=True)
    parent = fields.IntField(default=-1)

    class Meta:
        table = 'categories'
