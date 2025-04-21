import time
import json

from selenium.webdriver.common.by import By
from selenium.webdriver import Keys
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException, NoSuchElementException, TimeoutException
from bs4 import BeautifulSoup


class Parsing:
    # Инициализируем переменные и драйвер для работы
    def __init__(self, links_list: list):
        self.links_list = links_list
        self.link_products = []
        self.options = uc.ChromeOptions()

        self.options.add_argument('--blink-settings=imagesEnabled=false')

        self.driver = uc.Chrome(options=self.options, headless=False)

        self.ignored_exceptions = (NoSuchElementException, StaleElementReferenceException)

    # Осуществляем парсинг товаров с категории нижнего уровня
    def category_products(self):
        try:
            #  Получаем список уже спарщеных ранее программой категорий
            with open('products.json', 'r') as file:
                products_dict: dict = json.load(file)

            #  Проходимся по всем категориям
            for link in self.links_list:
                #  Для оптимизации парсинга сразу проверяем есть ли данные категории в уже спарщеных
                if self.links_list == products_dict.keys():
                    print(f'Данные категории {link} уже были спарсены!')
                    break

                #  Для оптимизации парсинга сразу убираем уже ранее спарщеные категории
                if link in products_dict.keys():
                    continue

                #  Открываем ссылку с категорией в браузере через драйвер
                self.driver.get(link)

                #  Загружаем cookie для установления города и убираем всплывающие меню
                with open('cookies.json', 'r') as file:
                    cookies = json.load(file)
                    for cookie in cookies:
                        self.driver.add_cookie(cookie_dict=cookie)

                #  Обновляем страницу
                self.driver.refresh()

                #  Спускаемся в самый низ страницы, чтобы прогрузить все данные
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)

                # Уменьшаем прогрузку сайта устанавливая таймер на элемент на сайте
                wait = WebDriverWait(self.driver, 20, ignored_exceptions=self.ignored_exceptions)
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "viewed-products-slider")))

                #  Получаем html данные со страницы
                response = self.driver.page_source
                soup = BeautifulSoup(response, "lxml")

                #  Получаем последнюю страницу в категории, чтобы взять все товары
                widget_pages = soup.find('ul', class_='pagination-widget__pages')
                max_page_link = widget_pages.find_all('li', class_='pagination-widget__page')[-1].find('a')['href']
                max_page = int(max_page_link.split('=')[-1])

                #  Отправляемся на первую страницу товара
                self.driver.get('https://www.dns-shop.ru' + max_page_link.split('=')[0] + '=1')
                #  Спускаемся в самый низ страницы, чтобы прогрузить все данные
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)

                #  Проходимся по всем товарам на страницах
                while int(self.driver.current_url.split('=')[-1]) < max_page:
                    #  Поднимаемся выше для нажатия кнопки "Показать ещё"
                    self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_UP)
                    #  Ждём пока появится кнопка
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "pagination-widget__show-more-btn")))

                    time.sleep(0.1)

                    #  Нажимаем на кнопку показать ещё
                    try:
                        self.driver.find_element(By.CLASS_NAME, 'pagination-widget__show-more-btn').click()

                    #  Обрабатываем возможные ошибки при прогрузке сайта
                    except (ElementClickInterceptedException, StaleElementReferenceException):
                        time.sleep(2)
                        self.driver.find_element(By.CLASS_NAME, 'pagination-widget__show-more-btn').click()

                    #  Спускаемся в самый низ страницы, чтобы прогрузить все данные
                    self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)

                #  Получаем html данные со страницы
                response = self.driver.page_source
                soup = BeautifulSoup(response, "lxml")

                # Устанавливаем список для ссылок на товары
                products_links = []

                #  Получаем все ссылки на товары со страницы
                dns_products = soup.find_all('div', class_="catalog-product ui-button-widget")
                for product in dns_products:
                    product_link = 'https://www.dns-shop.ru' + \
                                   product.find('a', class_='catalog-product__name ui-link ui-link_black')['href']
                    #  Добавляем ссылку в список
                    products_links.append(product_link)

                #  Добавляем ссылку в словарь для дальнейшего добавления в products.json
                products_dict[link] = products_links
                print(f'Ссылка {link} была успешно спарщена')

        finally:
            #  Записываем изменения в products.json
            with open('products.json', 'w', encoding='utf-8') as file:
                json.dump(products_dict, file, indent=4)

            # Отключаем драйвер
            self.driver.quit()

    def products(self):
        self.options = uc.ChromeOptions()

        self.options.add_argument('--blink-settings=imagesEnabled=false')

        self.driver = uc.Chrome(options=self.options, headless=False)
        #  Получаем данные с категорий
        with open('products.json', 'r') as file:
            products_dict: dict = json.load(file)

        #  Получаем данные уже спарщеных товаров
        with open('products_about.json', 'r') as file:
            products_about_dict: dict = json.load(file)
        try:
            for link in self.links_list:
                #  Берём первые 30 товаров с категории
                link_products = products_dict[link][:30]

                self.link_products.append(link_products)

                for product in link_products:
                    #  Проверяем есть ли уже в спарщеных товарах данный товар
                    if product in products_about_dict.keys():
                        continue
                    self.driver.get(product)

                    #  Загружаем cookie для установления города и убираем всплывающие меню
                    with open('cookies.json', 'r') as file:
                        cookies = json.load(file)
                        for cookie in cookies:
                            self.driver.add_cookie(cookie_dict=cookie)

                    #  Перезагружаем страницу
                    self.driver.refresh()

                    time.sleep(2)

                    #  Спускаемся постепенно вниз для прогрузки всей страницы
                    self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
                    self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
                    self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
                    self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)

                    #  Возвращаемся вверх, чтобы догрузить оставшееся
                    self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.HOME)

                    wait = WebDriverWait(self.driver, 15, ignored_exceptions=self.ignored_exceptions)

                    #  Устанавливаем таймер на загрузку страницы на нужные там текста
                    try:
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,
                                                                   "div.product-card-description__main > div.product-card-description-text")))

                        time.sleep(1)

                    #  Перезагружаем и снова ждём если не прогрузило страницу
                    except TimeoutException:
                        self.driver.refresh()
                        time.sleep(2)

                        #  Спускаемся постепенно вниз для прогрузки всей страницы
                        self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
                        self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
                        self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
                        self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)

                        #  Возвращаемся вверх, чтобы догрузить оставшееся
                        self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.HOME)

                    #  Нажимаем кнопку "Развернуть" в описании товара
                    try:
                        button = self.driver.find_element(By.CSS_SELECTOR,
                                                     'div.product-card-description__main > div.product-card-description-text > div > button')
                        time.sleep(2)
                        button.click()

                    #  Если таковой кнопки нету, то описание маленькое
                    except NoSuchElementException:
                        pass

                    try:
                        #  Нажимаем кнопку "Развернуть" для характеристик товара
                        button = self.driver.find_element(By.CLASS_NAME, 'product-characteristics__footer').find_element(By.CSS_SELECTOR,
                                                                                                           'div.product-characteristics__footer > button')
                        time.sleep(3)

                        button.click()

                    except NoSuchElementException:
                        pass

                    time.sleep(1)
                    #  Получаем html данные со страницы
                    response = self.driver.page_source.encode('utf-8')
                    soup = BeautifulSoup(response, "lxml")

                    #  Берём текст с характеристик товара
                    characteristics = soup.find('div', class_='product-card-description-specs')
                    characteristics = [text for text in characteristics.stripped_strings]

                    #  Берём все заголовки в характеристиках
                    group_names = soup.find_all('div', class_='product-characteristics__group-title')

                    group_names = [text.text for text in group_names]
                    group_names.append('Характеристики')
                    group_names.append('Свернуть')

                    #  Убираем ненужные нам заголовки с текста характеристик
                    result_list = [i for i in characteristics if i not in group_names]

                    #  Форматируем текст характеристик для нормального отображения
                    characteristics_text = ''
                    for i in range(0, len(result_list) - 1, 2):
                        characteristics_text += result_list[i] + ' - ' + result_list[i + 1] + '\n'

                    characteristics_text.replace('/ ', '/ ')

                    #  Получаем название категории нижнего уровня у товара
                    category_name = soup.find_all('li', class_='breadcrumb-list__item initial-breadcrumb')[-1].text

                    #  Получаем настоящую цену товара
                    price = soup.find('div', class_='product-buy__price').text.replace(' ', ' ').split('₽')[0] + '₽'

                    #  Получаем описание товара
                    about = soup.find('div', class_='product-card-description-text')
                    if about:
                        about = about.text.replace('\nСвернуть','').replace("\t","").replace('\n\n', '')
                    else:
                        about = ''

                    #  Получаем название товара
                    product_name = soup.find('div', class_='product-card-top__name').text.replace('\"', ' ')

                    #  Получаем наличие товара
                    in_available = soup.find('span', class_='available')
                    available = in_available.text + soup.find('a',
                                                              class_='order-avail-wrap__link ui-link ui-link_blue').text \
                        if in_available \
                        else soup.find('span',
                                       class_='product-card-top__avails avails-container avails-container_tile').text.replace(
                        "\t", "").replace('\n', '')

                    #  Получаем главное фото товара
                    main_product_photo = soup.find('img', class_='product-images-slider__img')['src']

                    #  Получаем максимальное кол-во фоток у товара
                    max_photos_count = int(
                        self.driver.find_element(By.CLASS_NAME, 'product-images-slider__counter').text.split('/')[-1])

                    #  Получаем номер фотки на данные момент
                    now_photos_count = int(
                        self.driver.find_element(By.CLASS_NAME, 'product-images-slider__counter').text.split('/')[0])

                    #  Проходимся по всем фоткам
                    while now_photos_count != max_photos_count:
                        self.driver.find_element(By.CSS_SELECTOR, 'div.tns-controls > button:nth-child(2)').click()

                        time.sleep(0.1)

                        now_photos_count = int(
                            self.driver.find_element(By.CLASS_NAME, 'product-images-slider__counter').text.split('/')[0])

                    #  Получаем html данные со страницы
                    response = self.driver.page_source.encode('utf-8')
                    soup = BeautifulSoup(response, "lxml")

                    #  Получаем все фото товара
                    photos = soup.find_all('img', class_='product-images-slider__img')

                    # Добавляем к фоткам главную фотку товара
                    photos_links = main_product_photo + '\n'

                    #  Проходимся по всем другим фото товара
                    for photo in photos[1:]:
                        photos_links += photo['data-src'] + '\n'

                    #  Собираем все данные для добавления их в products_about.json
                    product_dict = {
                        'Категория': category_name,
                        'Наименование': product_name,
                        'Цена': price,
                        'Доступность': available,
                        'Ссылка на товар': product,
                        'Ссылка на главное изображение': main_product_photo,
                        'Ссылки на все изображения': photos_links,
                        'Характеристики': characteristics_text,
                        'Описание': about
                    }

                    #  Добавляем товар в словарь
                    products_about_dict[product] = product_dict

                    print(f'Товар {product} был успешно спарщен!')


        except KeyboardInterrupt:
            #  Записываем изменения в словаре в json
            with open('products_about.json', 'w', encoding='utf-8') as file:
                json.dump(products_about_dict, file, indent=4, ensure_ascii=False)

            # Отключаем драйвер
            self.driver.quit()

        finally:
            #  Записываем изменения в словаре в json
            with open('products_about.json', 'w', encoding='utf-8') as file:
                json.dump(products_about_dict, file, indent=4, ensure_ascii=False)

            # Отключаем драйвер
            self.driver.quit()