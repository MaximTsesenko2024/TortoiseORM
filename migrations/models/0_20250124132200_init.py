from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "users" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "username" VARCHAR(255) NOT NULL UNIQUE,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "day_birth" DATE NOT NULL,
    "password" TEXT NOT NULL,
    "is_active" INT NOT NULL  DEFAULT 1,
    "is_staff" INT NOT NULL  DEFAULT 0,
    "admin" INT NOT NULL  DEFAULT 0,
    "created_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP
) /* Класс - описание пользователя в системе */;
CREATE INDEX IF NOT EXISTS "idx_users_usernam_266d85" ON "users" ("username");
CREATE INDEX IF NOT EXISTS "idx_users_email_133a6f" ON "users" ("email");
CREATE TABLE IF NOT EXISTS "categories" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(255) NOT NULL UNIQUE,
    "parent" INT NOT NULL  DEFAULT -1
) /* Класс - описание категории товара */;
CREATE TABLE IF NOT EXISTS "products" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(256) NOT NULL,
    "description" TEXT NOT NULL,
    "item_number" VARCHAR(256) NOT NULL,
    "price" REAL NOT NULL,
    "count" INT NOT NULL,
    "is_active" INT NOT NULL  DEFAULT 1,
    "action" INT NOT NULL  DEFAULT 0,
    "img" TEXT NOT NULL,
    "category_id" INT NOT NULL REFERENCES "categories" ("id") ON DELETE CASCADE
) /* Класс описания товара в системе */;
CREATE INDEX IF NOT EXISTS "idx_products_name_625ba0" ON "products" ("name");
CREATE TABLE IF NOT EXISTS "shops" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(255) NOT NULL UNIQUE,
    "location" TEXT NOT NULL,
    "is_active" INT NOT NULL  DEFAULT 1
) /* Класс - описание магазина */;
CREATE TABLE IF NOT EXISTS "buyer" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "id_operation" INT NOT NULL,
    "is_used" INT NOT NULL  DEFAULT 0,
    "count" INT NOT NULL,
    "product_id" INT NOT NULL REFERENCES "products" ("id") ON DELETE CASCADE,
    "shop_id" INT NOT NULL REFERENCES "shops" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
) /* Класс - описание покупки товара пользователем */;
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
