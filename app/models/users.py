from tortoise import Tortoise, fields, models


class User(models.Model):
    """
    Класс - описание пользователя в системе
    """
    id = fields.IntField(primary_key=True)
    # имя пользователя в системе
    username = fields.CharField(max_length=255, index=True, unique=True)
    # адрес электронной почты
    email = fields.CharField(max_length=255, index=True, unique=True)
    # дата рождения
    day_birth = fields.DateField()
    password = fields.TextField()
    # Флаг активности пользователя
    is_active = fields.BooleanField(default=True)
    # Флаг принадлежности к сотрудникам
    is_staff = fields.BooleanField(default=False)
    # Флаг принадлежности к администраторам
    admin = fields.BooleanField(default=False)
    # Временная метка создания объекта.
    created_at = fields.DatetimeField(auto_now_add=True)
    # Временная метка показывающая время последнего обновления объекта.
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = 'users'


