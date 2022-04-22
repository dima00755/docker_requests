import functools
import json

import requests
import datetime

image_list = []


@functools.lru_cache()
def get_from_dockerhub(url):
    r = requests.get(url)
    info = r.json()
    return info


def get_official_base_image_info(url):
    current_url = url
    while True:
        info = get_from_dockerhub(current_url)
        for image in info['results']:
            yield {
                'name': image['name'],
                'description': image['description'],
                'pull_count': image['pull_count'],
                'last_updated': image['last_updated']
            }
        if info['next'] is not None:
            current_url = info['next']
        else:
            break
    return


def browse_tags(url):
    current_url = url
    while True:
        info = get_from_dockerhub(current_url)
        for tag in info['results']:
            yield tag
        if info['next'] is not None:
            current_url = info['next']
        else:
            break
    return


def check_if_new(tag):
    try:
        tag_time = tag['tag_last_pushed'][:10].split('-')
        tag_time = datetime.date(int(tag_time[0]), int(tag_time[1]), int(tag_time[2]))
        different = datetime.datetime.now().date() - tag_time
        if different.days <= 365:
            return True
    except Exception:
        return False


def count_tags(url):
    new_tags = filter(check_if_new, browse_tags(url))
    count = functools.reduce(lambda acc, y: acc + 1, new_tags, 0)
    return count


def get_latest_tag_size(url):
    for tag in browse_tags(url):
        if tag['name'] == 'latest':
            return tag['full_size']


def get_official_tag_image_info(url, _image):
    size = get_latest_tag_size(url)
    count = count_tags(url)
    _image['latest_tag_size'] = size
    _image['tags_count'] = count
    return _image


if __name__ == '__main__':
    start_image_url = 'https://hub.docker.com/v2/repositories/library'
    image_list = [x for x in get_official_base_image_info(start_image_url)]
    with open('offic_image_docker.json', 'w') as f:
        json.dump([], f)
    for num, image in enumerate(image_list):
        start_tag_url = f'https://hub.docker.com/v2/repositories/library/{image["name"]}/tags'
        inf = get_official_tag_image_info(start_tag_url, image)
        print(num, end='')
        with open('offic_image_docker.json', 'r') as f:
            data = json.load(f)
        data.append(inf)
        with open('offic_image_docker.json', 'w') as f:
            json.dump(data, f)

