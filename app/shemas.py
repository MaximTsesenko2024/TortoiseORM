from pydantic import BaseModel
from datetime import date
from tortoise.contrib.pydantic import pydantic_model_creator
from app.models.category import Categories
from app.models.shop import Shops
from app.models.users import User
from app.models.product import ProductModel

user_pydantic = pydantic_model_creator(User)
product_pydantic = pydantic_model_creator(ProductModel)
category_pydantic = pydantic_model_creator(Categories)
shop_pydantic = pydantic_model_creator(Shops)


class AdminUser(BaseModel):
    # адрес электронной почты
    email: str
    # дата рождения
    day_birth: date
    # Флаг активности пользователя
    is_active: str
    # Флаг принадлежности к сотрудникам
    is_staff: str
    # Флаг принадлежности к администраторам
    admin: str


class CreateUser(BaseModel):
    username: str
    email: str
    day_birth: date
    password: str
    repeat_password: str


class SelectUser(BaseModel):
    username: str
    password: str


class UpdateUser(BaseModel):
    email: str
    day_birth: date


class RepairPassword(BaseModel):
    username: str
    email: str


class CreatePassword(BaseModel):
    password: str
    repeat_password: str


class Product(BaseModel):
    name: str
    description: str
    price: float
    count: int
    item_number: str
    category: int
    is_active: bool


class Car(BaseModel):
    count: int


class Payment(BaseModel):
    name: str
    card_number: int
    expiry_date: str
    security_code: int


class Category(BaseModel):
    id: int
    name: str
    parent: int


class Shop(BaseModel):
    name: str
    location: str
