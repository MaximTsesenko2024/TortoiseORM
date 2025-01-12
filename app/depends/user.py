from fastapi import Request, Depends
from jose import jwt, JWTError
from datetime import datetime, timezone
from ..routers.auth import SECRET_KEY, ALGORITHM
from ..models.users import User
from ..shemas import user_pydantic


async def find_user_by_id(user_id: int = -1) -> user_pydantic | None:
    """
    Поиск пользователя по идентификационному номеру.
    :param user_id: Идентификационный номер пользователя.
    :return: Объект user если пользователь в базе данных найден, None - в противном случае
    """
    user = await user_pydantic.from_queryset_single(User.get_or_none(id=user_id))
    return user


def get_token(request: Request) -> str | None:
    """
    Получение значения токена из запроса
    :param request: Запрос
    :return: Токен если он имеется и None в противном случае.
    """
    token = request.cookies.get('users_access_token')
    if not token:
        return None
    return token


async def get_current_user(token: str | None = Depends(get_token)) -> user_pydantic | None:
    """
    Получение пользователя по токену.
    :param token: Токен пользователя или None
    :return: Пользователь - в случае наличия токена и наличия идентификатора пользователя в базе данных, или
             None - в противном случае.
    """
    if token is None:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

    expire = payload.get('exp')
    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if (not expire) or (expire_time < datetime.now(timezone.utc)):
        return None

    user_id = payload.get('sub')
    if not user_id:
        return None

    user = await find_user_by_id(user_id=int(user_id))
    if not user:
        return None
    return user


async def get_user_model(user_id: int) -> User | None:
    """
    Получение модели пользователя по идентификатору.
    :param user_id: Идентификатор пользователя
    :return: Модель пользователя или None
    """
    user = await User.get_or_none(id=user_id)
    return user
