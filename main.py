import urllib.parse
import requests
import os
from pathlib import Path
from dotenv import load_dotenv
import random


def download_random_comic(picture_urls, directory, payload=None):
    url_components = urllib.parse.urlparse(picture_urls)
    file_path, file_name = os.path.split(url_components.path)

    response = requests.get(picture_urls, params=payload)
    response.raise_for_status()

    with open(Path(directory, file_name), 'wb') as file:
        file.write(response.content)
    return Path(directory, file_name)


def get_xkcd_comic(comic_url):
    response = requests.get(comic_url, timeout=30)
    response.raise_for_status()
    comic = response.json()
    return comic['num'], comic["img"], comic["alt"]


def get_wall_upload(vk_token, version_api, vk_group_id, picture_filepath):
    payload = {"access_token": vk_token,
               "v": version_api,
               "group_id": vk_group_id}

    response = requests.get(f'https://api.vk.com/method/photos.getWallUploadServer', params=payload)
    response.raise_for_status()

    photo_upload_address = response.json()["response"]
    upload_url = photo_upload_address['upload_url']

    payload = {"access_token": vk_token,
               "v": version_api}

    with open(picture_filepath, 'rb') as pict_file:
        file_load = {'photo': pict_file}
        response = requests.post(upload_url, params=payload, files=file_load)

    response.raise_for_status()

    return response.json()


def save_wall_photo(vk_token, version_api, vk_group_id, photo_upload_struct):
    payload = {"access_token": vk_token,
               "v": version_api,
               "group_id": vk_group_id,
               "photo": photo_upload_struct['photo'],
               "server": photo_upload_struct['server'],
               "hash": photo_upload_struct['hash'],
               }
    response = requests.post(f'https://api.vk.com/method/photos.saveWallPhoto', params=payload)
    response.raise_for_status()

    return response.json()['response'][0]


def posting_wall_post(vk_token, version_api, vk_group_id, from_save_wall, comment):
    payload = {"access_token": vk_token,
               "v": version_api,
               "group_id": vk_group_id,
               "attachments": f"photo{from_save_wall['owner_id']}_{from_save_wall['id']}",
               "message": comment,
               }

    response = requests.post(f'https://api.vk.com/method/wall.post', params=payload)
    response.raise_for_status()


def main():
    load_dotenv()
    vk_token = os.environ['VK_ACCESS_TOKEN']
    vk_group_id = os.environ['VK_GROUP_ID']

    directory = os.getcwd()
    version_api = "5.131"
    base_url = f'https://xkcd.com'
    url_path = f'info.0.json'

    last_number, picture_url, comment = get_xkcd_comic("/".join([base_url, url_path]))

    comic_number = str(random.randint(1, last_number))

    last_number, picture_url, comment = get_xkcd_comic("/".join([base_url, comic_number, url_path]))

    try:
        picture_filepath = download_random_comic(picture_url, directory, payload=None)

        photo_upload_struct = get_wall_upload(vk_token, version_api, vk_group_id, picture_filepath)

        answer_save_wall = save_wall_photo(vk_token, version_api, vk_group_id, photo_upload_struct)

        posting_wall_post(vk_token, version_api, vk_group_id, answer_save_wall, comment)

    finally:
        os.remove(picture_filepath)


if __name__ == "__main__":
    main()
