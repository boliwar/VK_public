import urllib.parse
import requests
import os
from pathlib import Path
from dotenv import load_dotenv
import random



def download_pictures(picture_urls, directory, payload=None):
    url_components = urllib.parse.urlparse(picture_urls)
    file_path, file_name = os.path.split(url_components.path)

    response = requests.get(picture_urls, params=payload)
    response.raise_for_status()

    with open(Path(directory, file_name), 'wb') as file:
        file.write(response.content)
    return Path(directory, file_name)

def get_xkcd_comics(comics_url):
    response = requests.get(comics_url, timeout=30)
    response.raise_for_status()

    return response.json()


def main():
    load_dotenv()
    vk_token = os.environ['VK_ACCESS_TOKEN']
    vk_group_id = os.environ['VK_GROUP_ID']

    directory = os.getcwd()
    version_api = "5.131"
    header_url = f'https://xkcd.com'
    end_url = f'info.0.json'

    comics = get_xkcd_comics("/".join([header_url, end_url]))
    last_number = int(comics['num'])

    comics_number = str(random.randint(1, last_number))

    comics = get_xkcd_comics("/".join([header_url, comics_number, end_url]))

    picture_urls = [comics["img"]]
    comment = comics["alt"]
    picture_file = download_pictures(picture_urls, directory, payload=None)

    payload = {"access_token": vk_token,
               "v": version_api,
               "group_id" : vk_group_id}

    response = requests.get(f'https://api.vk.com/method/photos.getWallUploadServer', params=payload)
    response.raise_for_status()

    preload = response.json()["response"]
    upload_url = preload['upload_url']

    payload = {"access_token": vk_token,
               "v": version_api}


    with open(picture_file, 'rb') as pict_file:
        pictload= {'photo': pict_file}
        response = requests.post(upload_url, params=payload, files=pictload)
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

    picture_push=response.json()['response'][0]

    payload = {"access_token": vk_token,
               "v": version_api,
               "group_id": vk_group_id,
               "attachments": f"photo{picture_push['owner_id']}_{picture_push['id']}",
               "message": comment,
               }

    response = requests.post(f'https://api.vk.com/method/wall.post', params=payload )
    response.raise_for_status()

    os.remove(picture_file)

if __name__ == "__main__":
    main()
