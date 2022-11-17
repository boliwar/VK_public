import urllib.parse
import requests
import os
from pathlib import Path
from dotenv import load_dotenv
import random
import collections


def download_comic(picture_urls, directory, payload=None):
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
    comic_struct = collections.namedtuple('comic_struct', ['img', 'alt', 'num'])
    return  comic_struct(img=comic["img"], alt=comic["alt"], num=comic['num'])


def get_upload_struct(vk_token, version_api, vk_group_id, picture_filepath):
    payload = {"access_token": vk_token,
               "v": version_api,
               "group_id": vk_group_id}

    response = requests.get(f'https://api.vk.com/method/photos.getWallUploadServer', params=payload)
    response.raise_for_status()

    photo_upload_response = response.json()["response"]
    upload_url = photo_upload_response['upload_url']

    payload = {"access_token": vk_token,
               "v": version_api}

    with open(picture_filepath, 'rb') as pict_file:
        file_load = {'photo': pict_file}
        response = requests.post(upload_url, params=payload, files=file_load)

    response.raise_for_status()

    return response.json()


def save_wall_photo(vk_token, version_api, vk_group_id, response_photo, response_server, response_hash):
    payload = {"access_token": vk_token,
               "v": version_api,
               "group_id": vk_group_id,
               "photo": response_photo,
               "server": response_server,
               "hash": response_hash,
               }
    response = requests.post(f'https://api.vk.com/method/photos.saveWallPhoto', params=payload)
    response.raise_for_status()

    return response.json()['response'][0]


def post_on_wall(vk_token, version_api, vk_group_id, id_owner, id_user, comment):
    from_group = 1
    payload = {"access_token": vk_token,
               "v": version_api,
               "owner_id": -int(vk_group_id),
               "from_group": from_group,
               "attachments": f"photo{id_owner}_{id_user}",
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

    comic_struct = get_xkcd_comic("/".join([base_url, url_path]))

    comic_number = str(random.randint(1, comic_struct.num))

    comic_struct = get_xkcd_comic("/".join([base_url, comic_number, url_path]))

    try:
        picture_filepath = download_comic(comic_struct.img, directory, payload=None)

        photo_upload_struct = get_upload_struct(vk_token, version_api, vk_group_id, picture_filepath)

        response_photo = photo_upload_struct['photo']
        response_server = photo_upload_struct['server']
        response_hash = photo_upload_struct['hash']
        save_wall_response = save_wall_photo(vk_token, version_api, vk_group_id, response_photo, response_server, response_hash)

        owner_id = save_wall_response['owner_id']
        user_id = save_wall_response['id']
        post_on_wall(vk_token, version_api, vk_group_id, owner_id, user_id, comic_struct.alt)

    finally:
        os.remove(picture_filepath)


if __name__ == "__main__":
    main()
