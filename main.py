import urllib.parse
import requests
import os
from pathlib import Path
from dotenv import load_dotenv
import random


def get_picture(url, filename, payload=None):
    response = requests.get(url, params=payload)
    response.raise_for_status()

    with open(filename, 'wb') as file:
        file.write(response.content)


def download_pictures(picture_urls, directory, payload=None):
    for url in picture_urls:
        url_components = urllib.parse.urlparse(url)
        file_path, file_name = os.path.split(url_components.path)
        get_picture(url, Path(directory, file_name), payload)
        return Path(directory, file_name)

def get_xkcd_comics(comics_number=None):
    header_url = f'https://xkcd.com'
    end_url = f'info.0.json'
    if comics_number:
        json_url = "/".join([header_url, comics_number, end_url])
    else:
        json_url = "/".join([header_url, end_url])

    response = requests.get(json_url, timeout=30)
    response.raise_for_status()

    return response.json()


def main():
    load_dotenv()
    vk_token = os.environ['VK_ACCESS_TOKEN']
    vk_group_id = os.environ['VK_GROUP_ID']

    directory = os.getcwd()
    version_api = "5.131"
    
    comics = get_xkcd_comics()
    last_number = int(comics['num'])

    comics_number = str(random.randint(1, last_number))

    comics = get_xkcd_comics(comics_number)

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
