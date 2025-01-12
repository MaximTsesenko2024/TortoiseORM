tortoise_orm = {
    "connections": {"default": 'sqlite://shop_db.db'},
    "apps": {
        "models": {
            "models": ["app.models.users", "app.models.product", "app.models.category",
                       "app.models.buy", "app.models.shop", "aerich.models"],
            "default_connection": "default",
        },
    },
}

