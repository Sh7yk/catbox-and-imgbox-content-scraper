import os
import sys
import yaml
import time
import random
import string
import asyncio
import aiohttp
import aiofiles
import threading
import requests
from bs4 import BeautifulSoup

URL = 'https://imgbox.com/'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

os.system('')
sys.stdout.write('\033[?25l')

urls_scanned = 0
valid_found = 0
start_time = time.time()
status_board_running = True

print_lock = asyncio.Semaphore()
file_lock = asyncio.Lock()

def clear_screen():
    if sys.platform == 'linux' or sys.platform == 'linux2':
        os.system('clear')
    elif sys.platform == 'win32':
        os.system('cls')

def random_string(length=8):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))

def format_elapsed_time(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

async def download_image(session, url, filename):
    async with session.get(url, timeout=5) as image_data:
        if image_data.status == 200:
            content = await image_data.read()
            if content:
                async with aiofiles.open(os.path.join('content', filename), mode='wb') as f:
                    await f.write(content)

async def save_valid_url(url):
    async with aiofiles.open('content/valids.txt', "a") as file:
        await file.write(url + "\n")

def parser(url):
    response = requests.get(url, headers=UA, allow_redirects=False)
    soup = BeautifulSoup(response.content, 'lxml')
    img_tag = soup.find('img', id='img')
    if img_tag and img_tag.get('src'):
        img_data = requests.get(img_tag['src']).content
        with open(f'content/{img_tag["src"].split("/")[-1]}', 'wb') as handler:
            handler.write(img_data)
        print(f'Saved image: content/{img_tag["src"].split("/")[-1]}')
        return img_tag['src']
    return None

async def check_url(_):
    global urls_scanned, valid_found
    async with aiohttp.ClientSession() as session:
        while True:
            filename = random_string()
            random_url = URL + filename
            try:
                async with session.get(random_url, timeout=5) as response:
                    urls_scanned += 1

                    if len(await response.read()) != 5545:
                        direct_image_url = parser(random_url)
                        if direct_image_url:
                            valid_found += 1
                            await download_image(session, direct_image_url, img_tag.split("/")[-1])
                            await save_valid_url(direct_image_url)

            except asyncio.exceptions.TimeoutError:
                continue
            except ConnectionResetError:
                continue
            except aiohttp.ClientConnectorError:
                continue
            except Exception as e:
                print(f"Exception {type(e).__name__}: {e}")

def status_board(update_rate):
    global urls_scanned, valid_found, start_time, status_board_running

    while status_board_running:
        if urls_scanned > 0:
            elapsed_time = time.time() - start_time
            formatted_elapsed_time = format_elapsed_time(elapsed_time)

            sys.stdout.write('\033[5;1H[-----------------------]\n')
            sys.stdout.write(f'\033[7;1H TIME ELAPSED : {formatted_elapsed_time}\n')
            sys.stdout.write(f'\033[8;1H CHECKS       : {urls_scanned:,}\n')
            sys.stdout.write(f'\033[9;1H HITS         : {valid_found:,}\n')
            sys.stdout.write(f'\033[6;1H PER SECOND   : {int(urls_scanned / elapsed_time):,}\n')
            sys.stdout.write('\033[10;1H[-----------------------]\n')
            sys.stdout.flush()
        time.sleep(update_rate)

if __name__ == "__main__":
    clear_screen()
    print(" IMAGEBOX SCRAPER")
    print("[==============]")
    print("    BY DOOT\n")
    print(' STARTING...')
    threading.Thread(target=status_board, args=(1,), daemon=True).start()  # Передаем update_rate в status_board

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    threads = 10  # Задайте количество потоков

    tasks = [check_url(i) for i in range(threads)]
    try:
        loop.run_until_complete(asyncio.gather(*tasks))
    except KeyboardInterrupt:
        status_board_running = False
        sys.exit("Stopped!")