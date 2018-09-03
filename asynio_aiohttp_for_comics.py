from bs4 import BeautifulSoup
import os
import aiohttp
import asyncio
import logging
from colorlog import ColoredFormatter
from aiofile import AIOFile, Reader, Writer

logger = logging.getLogger()  # 创建一个logger对象
logger.setLevel('INFO')
BASIC_FORMAT = '%(asctime)s  %(filename)s : %(levelname)s  %(message)s'
DATE_FORMAT = '%Y-%m-%d %A %H:%M:%S'
formatter = logging.Formatter(BASIC_FORMAT, DATE_FORMAT)
color_formatter = ColoredFormatter('%(log_color)s[%(module)-15s][%(funcName)-20s][%(levelname)-8s] %(message)s')
chlr = logging.StreamHandler() # 输出到控制台的handler
chlr.setFormatter(color_formatter)
chlr.setLevel('INFO')  # 也可以不设置，不设置就默认用logger的level
fhlr = logging.FileHandler('logger.log') # 输出到文件的handler
fhlr.setFormatter(color_formatter)
logger.addHandler(chlr)
logger.addHandler(fhlr)


headers = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
dirname = 'python antigravity comics'
if not os.path.exists(dirname):
    os.makedirs(dirname)
res_list = []


@asyncio.coroutine
async def getPage(url, res_list):
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            if resp.status==200:
                res_list.append(await resp.text())
                logging.info('page url get over')


@asyncio.coroutine
async def downImage(url):
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                filename=url[url.rfind('/')+1:]
                async with AIOFile(os.path.join(dirname,filename), 'wb') as afp:
                    writer=Writer(afp)
                    await writer(await resp.content.read())
                    await afp.fsync()
                    logging.info(('image\t'+filename + '\tis  over '))



class parseListPage():
    def __init__(self, page_str):
        self.page_str = page_str

    def __enter__(self):
        page_str = self.page_str
        res = BeautifulSoup(page_str, 'lxml')
        try:
            title = res.select('#ctitle')[0].string
            img = res.select('img[alt="' + title + '"]')[0]['src']
        except Exception as e:
            logging.error('get image error')
            return
        return 'https:' + img

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

import time
start=time.time()
page_url_base = "https://xkcd.com/"
page_urls = [page_url_base + str(i) for i in range(2041)]
loop = asyncio.get_event_loop()
tasks = [getPage(host, res_list) for host in page_urls]
logging.info(('tasks1 is  over '))
loop.run_until_complete(asyncio.wait(tasks))
image_urls = []
for res in res_list:
    with parseListPage(res) as tmp:
        image_urls.append(tmp)
res_list = []
tasks = [downImage(url) for url in image_urls if isinstance(url,str)]
logging.info(('tasks2 is  over '))
loop.run_until_complete(asyncio.wait(tasks))
loop.close()
logging.info('cost time '+str(time.time()- start))
