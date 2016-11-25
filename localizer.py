import json

lcl = {'Sender': 'Отправитель',
       'Time': 'Время',
       'Date': 'Дата',
       'Message text:': 'Текст сообщения',
       'Back': 'Назад',
       'The selected file should be a PNG or a JPG image': 'Выбранный файл должен быть PNG или JPG картинкой',
       'Please, select a file': 'Пожалуйста, выберите файл',
       'Select': 'Выбрать',
       'Cancel': 'Закрыть',
       'Select a picture file': 'Выберите картинку',
       'Status:': 'Статус:',
       'Email:': 'Эл. почта:',
       'Birthday:': 'День рождения:',
       'About:': 'О себе:',
       'Edit': 'Изменить',
       'Delete': 'Удалить',
       'January': 'Января',
       'February': 'Февраля',
       'March': 'Марта',
       'April': 'Апреля',
       'May': 'Мая',
       'June': 'Июня',
       'July': 'Июля',
       'August': 'Августа',
       'September': 'Сентября',
       'October': 'Октября',
       'November': 'Ноября',
       'December': 'Декабря',
       'Show password': 'Показать пароль',
       'Hide password': 'Спрятать пароль',
       'Register': 'Регистрация',
       'Login': 'Вход',
       'Username': 'Ник',
       'Password': 'Пароль',
       'Confirm': 'Еще раз',
       'Next': 'Дальше',
       'Back': 'Назад',
       'Error': 'Ошибка',
       'Add': 'Добавить',
       'Yes': 'Да',
       'No': 'Нет',
       'Log out': 'Выйти',
       'Do you want to log out?': 'Вы точно хотите выйти?',
       'Delete profile':
       'Удалить профиль',
       'Are you sure you want\nto delete your profile?\n'
       'This action can\'t be undone': 'Вы уверены, что хотите\n удалить свой профиль?\n'
       'Это действие необратимо',
       'Menu': 'Меню',
       'Profile': 'Профиль',
       'Log out': 'Выйти',
       'Settings': 'Настройки',
       'Help': 'Справка',
       'favorites': 'избранные',
       'add requests':
       'запросы в друзья',
       'online': 'онлайн',
       'offline': 'оффлайн',
       'request sent':
       'запрос отправлен',
       'blacklisted': 'заблокированные',
       'Profile': 'Профиль',
       'Remove from favorites': 'Убрать из избранного',
       'Remove from friends': 'Убрать из друзей',
       'Add to blacklist': 'Заблокировать',
       'Add to favorites':
       'В избранные',
       'Request message': 'Сообщение запроса',
       'Accept': 'Принять',
       'Decline': 'Отклонить',
       'Take back': 'Отменить',
       'Remove from blacklist': 'Разблокировать',
       'Send add request': 'Отправить запрос в друзья',
       'Select a language': 'Выберите язык',
       'Blue (default)': 'Синяя (стандартная)',
       'Select a theme':
       'Выберите тему оформления',
       'Back': 'Назад',
       'Settings': 'Настройки',
       'Language': 'Язык',
       'UI Theme': 'Тема оформления',
       'Custom smiles:': 'Пользовательские смайлы',
       'Add a user': 'Добавить пользователя в друзья',
       'Enter a username...': 'Введите ник...',
       'Message (optional)': 'Сообщение (необязательно)',
       'OK': 'ОК',
       'Message Info': 'Информация о сообщении',
       'Options': 'Опции',
       ' Load older messages':
       ' Еще сообщения',
       'Search for messages': 'Найти сообщения',
       'Delete dialog': 'Удалить диалог',
       'The beginning time exceeds the end': 'Начальное время превосходит конечное',
       'From: ': 'От: ',
       'To: ': 'Кому: ',
       'Search': 'Поиск',
       'Text to search...':
       'Фраза для поиска...',
       'Your message here...': 'Введите Ваше сообщение...',
       'The username you entered is incorrect. '
       'It should only consist of letters and spaces, '
       'it cannot consist of spaces only and must be '
       '2 to 15 characters long': 'Введен недопустимый логин. Он не может состоять из пробелов и должен быть от 2 до 15 символов в длину',
       'There is already a user with the username you entered. '
       'Try something different': 'Этот логин уже занят. Попробуйте другой',
       'You entered a wrong password for this username. '
       'Try again':
       'Вы ввели неверный пароль. Попробуйте еще раз',
       'Logged in as\n':
       'Вы вошли как\n',
       'Help': 'Справка',
       'Name': 'Имя',
       'Size': 'Размер'}

with open('local_ru.json', 'w') as f:
    json.dump(lcl, f, ensure_ascii = False, sort_keys = True, indent = 2)