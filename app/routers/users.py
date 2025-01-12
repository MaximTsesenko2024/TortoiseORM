from fastapi import APIRouter, Depends, status, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Annotated
from app.models.users import User
from fastapi.templating import Jinja2Templates
from app.shemas import CreateUser, SelectUser, UpdateUser, AdminUser, RepairPassword, CreatePassword, user_pydantic
from datetime import datetime
from .auth import get_password_hash, create_access_token, verify_password
from ..depends import get_current_user, find_user_by_id
from ..routers.buy import cars

user_router = APIRouter(prefix='/user', tags=['user'])
templates = Jinja2Templates(directory='app/templates/users')


async def check_user(name: str, password: str, ):
    """
    Проверка данных введённых пользователем на соответствие введённым в базу данных.
    :param name: Имя пользователя
    :param password: Пароль
    :return: Описание статуса операции, статус операции и объект user или None.
        Статус 'Ok' - пользователь прошёл проверку, введённые пользователем данные соответствуют базе данных.
        Описание - Авторизованы.
        Статус 'error' - пользователь не прошёл проверку, либо пользователя с таким именем не существует,
        либо пароль неверный. В описании указанно причина провала проверки
    """
    if name == '':
        return 'Имя пользователя не может быть пустым!', 'error', None
    user = await User.get_or_none(username=name)
    if user is None:
        return 'Пользователь не найден.', 'error', user
    elif not user.is_active:
        return 'Пользователь удалён из системы. Для восстановления обратитесь к администратору.', 'error', user
    elif not verify_password(plain_password=password, hashed_password=user.password):
        return 'Пароль не верен!', 'error', user
    return 'Авторизованы', 'Ok', user


def check_uniq(users: list, username, email):
    """
    Проверка имени пользователя и адреса электронной почты на уникальность.
    :param users: Список всех пользователей.
    :param username: Имя пользователя.
    :param email: Адрес электронной почты.
    :return: Статус проверки по каждому критерию
    """
    result = {'username': True, 'email': True}
    for user in users:
        if user.username == username:
            result['username'] = False
        if user.email == email:
            result['email'] = False
    return result


@user_router.post('/registration')
async def add_user_post(request: Request, create_user: CreateUser = Form()):
    """
    Обработка полученных от пользователя регистрационных данных.
    :param request: Запрос.
    :param create_user: Регистрационные данные пользователя.
    :return: Переход на страницу пользователя при успешной регистрации или
    отображение регистрационной страницы с указанием допущенной ошибки при регистрации.
    """
    info = {'request': request, 'title': 'Регистрация'}
    username = create_user.username
    # адрес электронной почты
    email = create_user.email
    # дата рождения пользователя
    day_birth = create_user.day_birth
    password = create_user.password
    repeat_password = create_user.repeat_password
    users = await user_pydantic.from_queryset(User.all())
    check = check_uniq(list(users), username, email)
    if not check['username']:
        info['message'] = f'Пользователь {username} уже существует!'
    elif password != repeat_password:
        info['message'] = f'Пароли не совпадают!'
    elif not check['email']:
        info['message'] = f'Пользователь c email: {email} уже существует!'
    else:
        password = get_password_hash(password)
        print('запись')
        user = await User.create(username=username, day_birth=day_birth, email=email, password=password,
                                 created_at=datetime.now(), updated_at=datetime.now())

        info['message'] = 'Зарегистрированы'
        access_token = create_access_token({"sub": str(user.id)})
        response = RedirectResponse(f'/user', status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="users_access_token", value=access_token, httponly=True)
        return response
    return templates.TemplateResponse("registration.html", info)


@user_router.get('/registration')
async def add_user_get(request: Request):
    """
    Отображение страницы ввода данных для регистрации.
    :param request: Запрос.
    :return: Страница с полями для ввода регистрационных данных
    """
    info = {'request': request, 'title': 'Регистрация'}
    return templates.TemplateResponse("registration.html", info)


@user_router.get('/login')
async def enter_user_get(request: Request):
    """
    Отображение страницы ввода данных для входа в систему.
    :param request: Запрос.
    :return: Страница с полями для ввода данных для входа в систему
    """
    info = {'request': request, 'title': 'Вход'}

    return templates.TemplateResponse("login.html", info)


@user_router.post('/login')
async def enter_user_post(request: Request,
                          select_user: SelectUser = Form()):
    """
    Обработка полученных от пользователя данных для авторизации.
    :param request: Запрос.
    :param select_user: Введённые пользователем данные для авторизации
    :return: Переход на страницу пользователя при успешной авторизации или
    отображение страницы входа с указанием допущенной ошибки при авторизации.
    """
    info = {'request': request, 'title': 'Вход'}
    username = select_user.username
    password = select_user.password

    info['message'], stat, user = await check_user(username, password)
    if stat == 'Ok':
        access_token = create_access_token({"sub": str(user.id)})
        response = RedirectResponse(f'/user', status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    else:
        response = templates.TemplateResponse("login.html", info)
    return response


@user_router.get('/logout')
async def exit_user_get(request: Request,
                        user: Annotated[User, Depends(get_current_user)]):
    """
    Отображение страницы выход из системы
    :param request: Запрос.
    :param user: Текущий пользователь.
    :return: Страница выхода из системы.
    """
    info = {'request': request, 'title': 'Выход'}
    if user is not None:
        info['login'] = True
    return templates.TemplateResponse('logout.html', info)


@user_router.post('/logout')
async def exit_user_post(request: Request,
                         user: Annotated[User, Depends(get_current_user)]):
    """
    Выполнение выхода пользователя из системы, удаление временного ключа пользователя
    :param request: Запрос.
    :param user: Текущий пользователь.
    :return: Переход на страницу данные пользователя
    """
    info = {'request': request, 'title': 'Выход'}
    if user is not None:
        info['message'] = f'Пользователь: {user.username} вышел из системы'
        response = RedirectResponse(f'/user', status_code=status.HTTP_303_SEE_OTHER)
        response.delete_cookie(key="users_access_token")
        info['login'] = True
    else:
        response = RedirectResponse(f'/user', status_code=status.HTTP_303_SEE_OTHER)
    return response


@user_router.post('/update/{user_id}', response_class=HTMLResponse)
async def update_user_post(request: Request,
                           user: Annotated[User, Depends(get_current_user)], user_id: int = -1,
                           update_user: UpdateUser = Form()):
    """
    Изменение данных пользователя.
    :param request: Запрос.
    :param user: Текущий пользователь
    :param user_id: Идентификационный номер пользователя
    :param update_user: Изменённые данные пользователя
    :return: Страница с изменёнными данными пользователя
    """
    info = {'request': request, 'title': 'Изменение данных пользователя'}
    if user is None:
        RedirectResponse('/user/login', status_code=status.HTTP_401_UNAUTHORIZED)
    elif user_id != user.id:
        return HTTPException(status.HTTP_401_UNAUTHORIZED, detail='Нет доступа')
    # адрес электронной почты
    email = update_user.email
    # возраст пользователя
    day_birth = update_user.day_birth
    await User.filter(id=user_id).update(email=email, day_birth=day_birth, updated_at=datetime.now())
    info['message'] = 'Обновлено'
    user = await User.get(id=user_id)
    info['user'] = user
    return RedirectResponse(f'/user', status_code=status.HTTP_303_SEE_OTHER)


@user_router.get('/update/{user_id}')
async def update_user_get(request: Request,
                          user: Annotated[User, Depends(get_current_user)], user_id: int = -1):
    """
    Отображение страницы изменения данных пользователя
    :param request: Запрос.
    :param user: Текущий пользователь
    :param user_id: Идентификационный номер пользователя
    :return: Страница с полями для изменения данных пользователя
    """
    info = {'request': request, 'title': 'Изменение данных пользователя'}
    if user is None:
        RedirectResponse('/user/login', status_code=status.HTTP_401_UNAUTHORIZED)
    elif user_id != user.id:
        return HTTPException(status.HTTP_401_UNAUTHORIZED, detail='Нет доступа')
    else:
        info['user'] = user
    return templates.TemplateResponse("update_user.html", info)


@user_router.get('/delete')
async def delete_user_self(request: Request,
                           user: Annotated[User, Depends(get_current_user)]):
    """
    Деактивация пользователя в системе
    :param request: Запрос
    :param user: Текущий пользователь
    :return: переход на главную страницу
    """
    info = {'request': request, 'title': 'Удаление пользователя'}
    if user is None:
        return RedirectResponse('/main', status_code=303)
    if user.id in cars.keys():
        cars.pop(user.id)
    await User.filter(id=user.id).update(is_active=False, updated_at=datetime.now())
    response = RedirectResponse(f'/main', status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="users_access_token")
    return response


@user_router.get('/')
async def select_user_get(request: Request,
                          user: Annotated[User, Depends(get_current_user)]):
    """
    Отображение страницы текущего пользователя и маршрутизации его задач
    :param request: Запрос
    :param user: Текущий пользователь
    :return: Страница с данными текущего пользователя и его допустимыми действиями
    """
    info = {'request': request, 'title': 'Данные пользователя'}
    if user is not None:
        info['user'] = user
    return templates.TemplateResponse("user_page.html", info)


@user_router.get('/repair')
async def repair_password_get(request: Request):
    """
    Запрос на восстановление пароля.
    :param request: Запрос.
    :return: Страница с формой для восстановления пароля.
    """
    info = {'request': request, 'title': 'Восстановление пароля'}
    return templates.TemplateResponse("repair.html", info)


@user_router.post('/repair')
async def repair_password_post(request: Request, repair: RepairPassword = Form()):
    """
    Проверка пользовательских данных для восстановления пароля. В случае совпадения имени пользователя и
    адреса электронной почты выполняется переадресация на страницу ввода нового пароля, иначе отображение страницы
    с запросом данных.
    :param request: Запрос.
    :param repair : Данные пользователя для восстановления пароля
    :return: Переадресация на страницу ввода нового пароля или страница с формой для восстановления пароля и
    сообщения об ошибке.
    """
    info = {'request': request, 'title': 'Восстановление пароля'}
    user = await user_pydantic.from_queryset(User.filter(username=repair.username))
    if user is None or user.email != repair.email:
        info['message'] = 'Пользователь не найден'
        return templates.TemplateResponse("repair.html", info)
    return RedirectResponse(f'/user/create_password/{user.id}', status_code=status.HTTP_303_SEE_OTHER)


@user_router.get('/create_password/{user_id}')
async def create_password_get(request: Request, user_id: int = -1):
    """
    Отображение страницы ввода нового пароля.
    :param request: Запрос.
    :param user_id: Идентификатор пользователя, запросившего изменение пароля.
    :return: Страница с формой ввода нового пароля
    """
    info = {'request': request, 'title': 'Создание нового пароля'}
    user = await User.get_or_none(id=user_id)
    if user is None:
        info['message'] = 'Пользователь не найден'
        return RedirectResponse('/user', status_code=status.HTTP_303_SEE_OTHER)
    info['name'] = user.username
    info['user_id'] = user_id
    return templates.TemplateResponse("create_new_password.html", info)


@user_router.post('/create_password/{user_id}')
async def create_password_post(request: Request,
                               create_password: CreatePassword = Form(), user_id: int = -1):
    """
    Запись в базу данных hash - строки нового пароля пользователя при условии наличия пользователя и
    соответствия пароля его подтверждению или отображение страницы ввода нового пароля.
    :param request: Запрос.
    :param create_password: Новый пароль и его подтверждение.
    :param user_id: Идентификатор пользователя, запросившего изменение пароля.
    :return: Переход к странице пользователя или отображение страницы ввода нового пароля
    """
    info = {'request': request, 'title': 'Создание нового пароля'}
    user = await User.get_or_none(id=user_id)
    if user is None:
        info['message'] = 'Пользователь не найден'
        return RedirectResponse('/user', status_code=status.HTTP_303_SEE_OTHER)
    password = create_password.password
    repeat_password = create_password.repeat_password
    if password != repeat_password:
        info['message'] = 'Пароли не соответствуют'
        info['name'] = user.username
        info['user_id'] = user_id
        return templates.TemplateResponse("create_new_password.html", info)
    password = get_password_hash(password)
    await User.filter(id=user.id).update(password=password, updated_at=datetime.now())
    info['message'] = 'Пароль изменён'
    access_token = create_access_token({"sub": str(user.id)})
    response = RedirectResponse(f'/user', status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    return response


#  Обработка действий администратора
@user_router.get('/list/delete/{id_user}')
async def delete_user_admin_get(request: Request,
                                user: Annotated[User, Depends(get_current_user)], id_user: int):
    """
    Запрос на удаление пользователя администратором. При выполнении осуществляется проверка наличия
    у текущего пользователя прав администратора и существование пользователя с указанным идентификатором.
    В результате страница выбранного пользователя если текущий пользователь имеет права администратора и
    выбранный пользователь существует, ошибка при не выполнении любого из условий.
    :param request: Запрос.
    :param user: Текущий пользователь.
    :param id_user: Идентификатор выбранного пользователя.
    :return: Страница выбранного пользователя или ошибка.
    """
    info = {'request': request, 'title': 'Администратор. Удаление пользователя'}
    if user is None:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail='Вы не авторизованны или у вас отсутствуют права')
    elif not user.admin:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail='Вы не авторизованны или у вас отсутствуют права')

    user = await find_user_by_id(id_user)
    if user is None:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пользователь не найден')
    else:
        info['user'] = user
        info['is_staff'] = user.admin
    return templates.TemplateResponse("delete_user_page.html", info)


@user_router.post('/list/delete/{id_user}')
async def delete_user_admin_post(request: Request,
                                 user: Annotated[User, Depends(get_current_user)], id_user: int):
    """
    Выполнение удаления пользователя из базы данных, в том числе и историю его покупок.
    :param request: Запрос.
    :param user: Текущий пользователь.
    :param id_user: Идентификатор выбранного пользователя.
    :return: Переход к списку пользователей в случае удаления пользователя, или сообщение об ошибке.
    """
    info = {'request': request, 'title': 'Администратор. Удаление пользователя'}
    if user is None:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail='Вы не авторизованны или у вас отсутствуют права')
    elif not user.admin:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail='Вы не авторизованны или у вас отсутствуют права')

    user = await find_user_by_id(id_user)
    if user is None:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пользователь не найден')
    else:
        if user.id in cars.keys():
            cars.pop(user.id)
        await User.filter(id=user.id).delete()
        return RedirectResponse('user/list', status_code=status.HTTP_303_SEE_OTHER)


@user_router.post('/list/update/{id_user}')
async def update_user_admin_post(request: Request,
                                 user: Annotated[User, Depends(get_current_user)], user_update: AdminUser = Form(),
                                 id_user: int = -1):
    """
    Запись в базу данных изменённых данных выбранного пользователя. Запись осуществляется при условии существования
    выбранного пользователя и наличия у текущего пользователя прав администратора.
    :param request: Запрос.
    :param user: Текущий пользователь.
    :param user_update: Обновлённые данные выбранного пользователя.
    :param id_user: Идентификатор выбранного пользователя.
    :return: Переход на страницу выбранного пользователя
    """
    info = {'request': request, 'title': 'Администратор. Изменение данных пользователя'}
    if user is None:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail='Вы не авторизованны или у вас отсутствуют права')
    elif not user.admin:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail='Вы не авторизованны или у вас отсутствуют права')

    user = await find_user_by_id(id_user)
    if user is None:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пользователь не найден')
    else:
        bis_active, bis_staff, badmin = user_update.is_active == 'Да', user_update.is_staff == 'Да', user_update.admin == 'Да'
        await User.filter(id=id_user).update(email=user_update.email,
                                             day_birth=user_update.day_birth,
                                             is_active=bis_active,
                                             is_staff=bis_staff, admin=badmin,
                                             updated_at=datetime.now())
    return RedirectResponse(f'/user/list/{id_user}', status_code=status.HTTP_303_SEE_OTHER)


@user_router.get('/list/update/{id_user}')
async def update_user_admin_get(request: Request,
                                user: Annotated[User, Depends(get_current_user)], id_user: int):
    """
    Отображение страницы изменения данных выбранного пользователя при условии существования выбранного пользователя и
    наличия у текущего пользователя прав администратора.
    :param request: Запрос.
    :param user: Текущий пользователь.
    :param id_user: Идентификатор выбранного пользователя.
    :return: Страница с формой изменения данных пользователя или сообщение об ошибке.
    """
    info = {'request': request, 'title': 'Администратор. Изменение данных пользователя'}
    if user is None:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail='Вы не авторизованны или у вас отсутствуют права')
    elif not user.admin:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail='Вы не авторизованны или у вас отсутствуют права')

    user = await find_user_by_id(id_user)
    if user is None:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пользователь не найден')
    else:
        info['user'] = user
    return templates.TemplateResponse("update_admin_user.html", info)


@user_router.get('/list/{id_user}')
async def select_user_admin_get(request: Request,
                                user: Annotated[User, Depends(get_current_user)], id_user: int):
    """
    Отображение страницы выбранного пользователя при условии существования выбранного пользователя и
    наличия у текущего пользователя прав администратора.
    :param request: Запрос.
    :param user: Текущий пользователь.
    :param id_user: Идентификатор выбранного пользователя.
    :return: Страница текущего пользователя или сообщение об ошибке.
    """
    info = {'request': request, 'title': 'Администратор. Данные пользователя'}
    if user is None:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail='Вы не авторизованны или у вас отсутствуют права')
    elif user.admin is False:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail='У вас отсутствуют права')

    car_user = await find_user_by_id(id_user)
    if car_user is None:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пользователь не найден')
    else:
        info['user'] = car_user
    return templates.TemplateResponse("update_admin_user.html", info)


@user_router.get('/list')
async def select_list_user_get(request: Request,
                               user: Annotated[User, Depends(get_current_user)]):
    """
    Отображение списка пользователей при условии наличия у текущего пользователя прав администратора.
    :param request: Запрос.
    :param user: Текущий пользователь.
    :return: Список пользователей или сообщение об ошибке.
    """
    info = {'request': request, 'title': 'Список пользователей'}
    if user is None:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail='Вы не авторизованны или у вас отсутствуют права')
    elif user.admin is False:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail='У вас отсутствуют права')
    users = await User.all()
    info['users'] = users
    return templates.TemplateResponse("users_list.html", info)