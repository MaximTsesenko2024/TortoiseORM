import datetime
from typing import Optional
from pydantic import BaseModel, Field
from datetime import date
from tortoise.contrib.pydantic import pydantic_model_creator
from models.users import User
from models.product import ProductModel, Categories, Shops, BuyerProd

User_pydantic = pydantic_model_creator(User)
Product_pydantic = pydantic_model_creator(ProductModel)
Category_pydantic = pydantic_model_creator(Categories)
Shop_pydantic = pydantic_model_creator(Shops)



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


class Car(BaseModel):
    count: int


class Buyer(BaseModel):
    user: int
    product: int
    shop: str


class Category(BaseModel):
    id: int
    name: str
    parent: int


class Shop(BaseModel):
    name: str
    location: str
