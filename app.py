import datetime
import requests
import time
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VERSION = '5.110'
GROUP_LIST = []
BAD_SYMBOL = ['/', '|']
POST_COUNT = 70

with open("base/token.txt") as f:
    ACCESS_TOKEN = f.read().strip()


def get_group_list():
    group_list = []
    with open('base/group_list.txt', 'r') as file:
        for item in file:
            group_id = re.findall(r"\d+", item)
            #  проверка на дубликаты в группе
            if group_id[0] not in group_list:
                group_list.append(group_id[0])
            else:
                continue

    return group_list


def get_group_name(group_id):
    try:
        response = requests.get('https://api.vk.com/method/groups.getById',
                                params={
                                    'access_token': ACCESS_TOKEN,
                                    'v': VERSION,
                                    'group_id': group_id,
                                })

        name = response.json()['response'][0]['name']
        for item in BAD_SYMBOL:
            if item in name:
                name = name.replace(item, '-')
    except:
        name = 'group {} error'.format(group_id)

    return name


def get_all_posts(group_id):
    posts = []
    finally_list = []
    try:
        response = requests.get('https://api.vk.com/method/wall.get',
                                params={
                                    'access_token': ACCESS_TOKEN,
                                    'v': VERSION,
                                    'owner_id': '-' + group_id,
                                    'count': POST_COUNT,
                                })

        data = response.json()['response']['items']
        posts.extend(data)
        for post in posts:
            date = datetime.datetime.fromtimestamp(post['date'])
            # получение постов за предыдущие сутки
            today = datetime.datetime.now().day
            if today - 1 == int(date.strftime('%d')):
                finally_list.append(post)


    except:
        finally_list = 'No DATA'

    return finally_list


def get_post_data(post, group_id, file):
    try:
        url = 'https://vk.com/wall-' + group_id + '_' + str(post['id'])
        date = datetime.datetime.fromtimestamp(post['date'])

        file.write(url + '\n')
        file.write(date.strftime('%d-%m-%Y %H:%M') + '\n')

        if post['text'] == '':
            post['text'] = 'В этом посте изображение'
            file.write(post['text'] + '\n\n')
        else:
            file.write(post['text'] + '\n\n')
    except:
        file.write('в сообщении присутствует недопустимый символ либо другая ошибка \n\n')


def get_comments(post, group_id, group_name, file):
    url = 'https://vk.com/wall-' + str(group_id) + '_' + str(post['id']) + '\n\n'
    file.write(url)
    comments = []

    response = requests.get('https://api.vk.com/method/wall.getComments',
                            params={
                                'access_token': ACCESS_TOKEN,
                                'v': VERSION,
                                'owner_id': '-' + group_id,
                                'count': 100,
                                'post_id': post['id'],
                                'sort': 'asc',
                                'thread_items_count': '10'
                            })

    data = response.json()['response']['items']
    comments.extend(data)  # Список всех комментариев
    time.sleep(0.5)

    for comment in comments:
        try:
            file.write(
                'https://vk.com/id' + str(comment['from_id']) + ' написал(а):\n' + comment['text'] + '\n\n')

            if comment['thread']:
                response = requests.get('https://api.vk.com/method/wall.getComments',
                                        params={
                                            'access_token': ACCESS_TOKEN,
                                            'v': VERSION,
                                            'owner_id': '-' + group_id,
                                            'post_id': post['id'],
                                            'comment_id': comment['id'],
                                            'count': 100
                                        })
                data = response.json()['response']['items']
                for item in data:
                    file.write('https://vk.com/id' + str(comment['from_id']) + ' написал(а):\n'
                               + item['text'] + '\n\n')

        except:
            file.write('комментарий удалён\n\n')
            print(f"Some error in comments in {group_name} - https://vk.com/wall-{group_id}_{post['id']}")


def main():
    GROUP_LIST.extend(get_group_list())  # получаем список групп для парсинга
    count = 0
    for group_id in GROUP_LIST:
        count += 1
        group_name = get_group_name(group_id)  # Получение названия группы
        dir_out = '{}/out/{}-{}'.format(BASE_DIR,
                                        group_name,
                                        group_id)  # путь до директории где будет лежать результат парсинга

        print(f'{count} - Начинаю сбор информации в группе {group_name}-club{group_id}')

        posts = get_all_posts(group_id)  # Получение списка постов за предыдущие сутки

        try:
            os.mkdir(dir_out)
        except:
            print(f'Директория {group_name} не может быть создана')

        for post in posts:
            with open(dir_out + '/wall-{}_{}.txt'.format(group_id, post['id']), 'w') as file:
                get_post_data(post, group_id, file)
                file.write('\nКомментарии к записи:\n\n')
                get_comments(post, group_id, group_name, file)  # Получение всех комментариев к каждому посту


if __name__ == '__main__':
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))
