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

    return response.json()


def main():
    load_dotenv()
    vk_token = os.environ['VK_ACCESS_TOKEN']
    vk_group_id = os.environ['VK_GROUP_ID']

    directory = os.getcwd()
    version_api = "5.131"
    base_url = f'https://xkcd.com'
    path_url = f'info.0.json'

    comic = get_xkcd_comic("/".join([base_url, path_url]))
    last_number = int(comic['num'])

    comic_number = str(random.randint(1, last_number))

    comic = get_xkcd_comic("/".join([base_url, comic_number, path_url]))

    picture_url = [comic["img"]]
    comment = comic["alt"]
    picture_file = download_random_comic(picture_url, directory, payload=None)

    payload = {"access_token": vk_token,
               "v": version_api,
               "group_id" : vk_group_id}

    response = requests.get(f'https://api.vk.com/method/photos.getWallUploadServer', params=payload)
    response.raise_for_status()

    from_wall_upload = response.json()["response"]
    upload_url = from_wall_upload['upload_url']

    payload = {"access_token": vk_token,
               "v": version_api}


    with open(picture_file, 'rb') as pict_file:
        file_load= {'photo': pict_file}
        response = requests.post(upload_url, params=payload, files=file_load)
        response.raise_for_status()

    picture_confirm =response.json()

    payload = {"access_token": vk_token,
               "v": version_api,
               "group_id": vk_group_id,
               "photo": picture_confirm['photo'],
               "server": picture_confirm['server'],
               "hash": picture_confirm['hash'],
              }
    response = requests.post(f'https://api.vk.com/method/photos.saveWallPhoto', params=payload)
    response.raise_for_status()

    from_save_wall=response.json()['response'][0]

    payload = {"access_token": vk_token,
               "v": version_api,
               "group_id": vk_group_id,
               "attachments": f"photo{from_save_wall['owner_id']}_{from_save_wall['id']}",
               "message": comment,
               }

    response = requests.post(f'https://api.vk.com/method/wall.post', params=payload )
    response.raise_for_status()

    os.remove(picture_file)

if __name__ == "__main__":
    main()
