import datetime
import time
from parsing import Parsing
from excel_result import save_data


def main():
    try:
        print('Парсинг будет осуществляться по городу Москва. Нужно иметь стабильный интернет и терпение)!')

        time.sleep(2)

        link_list = str(
            input("Введите ссылки нижних категорий ЧЕРЕЗ ПРОБЕЛ на сайте (dns-shop.ru) для парсинга: ")).split()

        # link_list = [
        #     'https://www.dns-shop.ru/catalog/17a899cd16404e77/processory/',
        #     'https://www.dns-shop.ru/catalog/1f8bef2670f05456/marshrutizatory/',
        #     'https://www.dns-shop.ru/catalog/17a9de8616404e77/igry-dlya-pk/',
        #     'https://www.dns-shop.ru/catalog/17a892f816404e77/noutbuki/',
        #     'https://www.dns-shop.ru/catalog/17a8b87a16404e77/sistemy-videonablyudeniya/'
        # ]

        print('Ваш список ссылок:', link_list)
        print('Парсер успешно начинает свою работу.')

        #  Инициализируем класс парсинга
        parser = Parsing(link_list)

        #  Парсинг всех товаров с категории
        parser.category_products()
        print('Категории товаров были успешно спарщены!')

        #  Парсинг товаров
        parser.products()

        #  Возвращаем ссылки на товары для добавления их в таблицу
        print(parser.link_products)
        return parser.link_products

    except KeyboardInterrupt:
        if link_products:
            print(link_products)
        print('Выполнение программы было завершено. Вы можете вновь запустить парсер и данные будут продолжать собираться.')


if __name__ == '__main__':
    try:
        link_products = main()
        filename = datetime.datetime.now().strftime('%Y-%m-%d %H %M') + '.xlsx'

        print('Записываем изменения в файл', filename)
        save_data(filename, link_products)

        print('Выполнение программы было успешно завершено.')

    except Exception as e:
        if e != 'KeyboardInterrupt':
            #  Пробуем запустить снова если вылезла ошибка
            link_products = main()
