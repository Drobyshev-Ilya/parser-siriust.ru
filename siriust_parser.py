import requests
from lxml import html
import sqlite3

def siriust():
    url = 'https://siriust.ru/'

    # Определение User-Agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 YaBrowser/23.3.3.719 Yowser/2.5 Safari/537.36'
    }

    #В переменные login и password записываются данные, введённые пользователем в консоли
    login = input("Введите логин: ")
    password = input("Введите пароль: ")

    #Создаётся словарь data, в котором содержится информация о логине и пароле пользователя
    data = {
        'user_login': login,
        'password': password,
        'dispatch[auth.login]': '' 
    }

    #Создаётся объект сессии, который используется для выполнения запросов к сайту
    session = requests.Session()
    session.headers.update(headers)

    #Посылается POST-запрос на сайт, который содержит информацию о логине и пароле пользователя
    response =  session.post(url, data=data)

    #Производится проверка правильности введённых логина и пароля
    if "Вы ввели неверный логин или пароль" in response.text:
        print("Неверный логин или пароль")
        return False
    else:
        print("Успешная авторизация")

    #Посылается GET-запрос на страницу с персональной информацией пользователя
    response_profile = session.get('https://siriust.ru/profiles-update/')

    #Извлекаем HTML-код страницы
    tree = html.fromstring(response_profile.content)

    #Из полученного html-кода извлекается персональная информация пользователя (почта, имя, фамилия, город)
    email = list(set(tree.xpath("//input[@name='user_data[email]']/@value")))[0]
    s_firstname = list(set(tree.xpath("//input[@name='user_data[s_firstname]']/@value")))[0]
    s_lastname = list(set(tree.xpath("//input[@name='user_data[s_lastname]']/@value")))[0]
    s_city = list(set(tree.xpath("//input[@name='user_data[s_city]']/@value")))[0]

    #Создаётся соединение с базой данных example.db, создаётся объект-курсор
    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()

    # Создание таблицы для персональных данных
    cursor.execute('''CREATE TABLE IF NOT EXISTS personal_data
                (email TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    city TEXT)''')

    # Создание таблицы для товаров в избранном
    cursor.execute('''CREATE TABLE IF NOT EXISTS products
                (name TEXT,
                    price1 REAL,
                    price2 REAL,
                    rating REAL,
                    reviews TEXT,
                    stores TEXT,
                    reviews_list TEXT)''')
    # Добавляем персональные данные в таблицу
    cursor.execute(f'''INSERT INTO personal_data VALUES 
                    ('{email}',
                    '{s_firstname}', 
                    '{s_lastname}', 
                    '{s_city}')''')

    # Сохранение изменений и закрытие соединения с базой данных
    conn.commit()
    conn.close()

    # Список URL-адресов всех товаров, которые находятся в избранном
    product_urls = []

    # Отправляем GET-запрос на страницу с избранными товарами
    response_wishlist = session.get('https://siriust.ru/wishlist/')

    # Извлекаем HTML-код страницы
    tree2 = html.fromstring(response_wishlist.content)

    # Ищем ссылки на товары в списке избранного
    links = tree2.xpath('//a[@class="product-title"]/@href')

    # Добавляем URL-адреса товаров в список
    for link in links:
        product_urls.append(link)

    # Проходим по всем URL-адресам товаров из списка
    for url in product_urls:
        # Отправляем GET-запрос на страницу товара
        response3 = requests.get(url)
        # Извлекаем HTML-код страницы
        tree3 = html.fromstring(response3.content)
        # Ищем название товара
        product_name = tree3.xpath('//h1[@class="ty-product-block-title"]/bdi/text()')[0]
        # Ищем цену товара
        # Розничная цена
        price1 = tree3.xpath('//span[@class="ty-price-num"]/text()')[0]
        # Оптовая цена
        price2 = tree3.xpath('//span[@class="ty-price-num"]/text()')[1]
        # Ищем рейтинг товара
        rating = tree3.xpath('count(//div [@class="ty-product-block__rating"]//i[@class="ty-stars__icon ty-icon-star"])')
        ## Ищем кол-во отзывов
        discussion_count = tree3.xpath('//a[@class="ty-discussion__review-a cm-external-click"]/text()')
        if discussion_count:
            discussion_count_f = discussion_count[0]
        else:
            discussion_count_f = "0 Отзывов"
        # Ищем кол-во магазинов, в которых есть товар
        warehouses = tree3.xpath('//div[@class="ty-product-feature__value" and not(contains(text(), "отсутствует"))]/text()')
        warehouses_len = len(warehouses)
        # Ищем отзывы
        discussion = tree3.xpath('//div[@class="ty-discussion-post__message"]/text()')
        discussion_f = ""
        if discussion:
            for dis in discussion:
                discussion_f += f"{dis}\n"

        # print(discussion)
    # Создание подключения к базе данных и курсора
        conn = sqlite3.connect('example.db')
        cursor = conn.cursor()
    # Добавляем данные по товару в таблицу
        cursor.execute(f'''INSERT INTO products VALUES 
                    ('{product_name}', 
                    '{price1}', 
                    '{price2}', 
                    '{rating}', 
                    '{discussion_count_f}', 
                    '{warehouses_len}', 
                    '{discussion_f}')''')

        # Сохранение изменений и закрытие соединения с базой данных
        conn.commit()
        conn.close()

siriust()