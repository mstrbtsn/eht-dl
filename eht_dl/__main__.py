#!/usr/bin/env python3

import requests
import lxml.etree
import time
import os
import sys
import shutil
import zipfile
from argparse import ArgumentParser, FileType
from tempfile import TemporaryDirectory
from pathlib import Path
import logging
import eht_dl.config as config

TMPDIR = None
logger = None

HTTP_CLIENT_CHUNK_SIZE=10240

req = requests.session()
req.headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
}


def downloadImageFile(workdir, imgurl):
    filename = workdir / imgurl.split('/')[-1]
    logger.info(f"Downloadin an image file...: {filename}")

    for retry in range(1, 10):
        try:
            r = req.get(imgurl, stream=True, timeout=(10.0, 10.0))

            length = int(r.headers['Content-Length'])

            if (os.path.exists(filename)) and (os.stat(filename).st_size == length):
                logger.info(f'Use existing file: {filename}')
            else:
                # ファイルが存在しない、または、ファイルサイズとダウンロードサイズが異なる。
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=4096):
                        if chunk: # filter out keep-alive new chunks
                            f.write(chunk)
                            f.flush()
                    f.close()

            info = os.stat(filename)
            if info.st_size == length:
                return filename
            else:
                st_size = info.st_size
                logger.warn('Download size mismatch file size: {st_size}'
                            'Content-Length: {length}')
                continue

        except requests.exceptions.ConnectionError:
            logger.warn('ConnectionError:' + imgurl)
            continue
        except requests.exceptions.Timeout:
            logger.warn('Timeout:' + imgurl)
            continue
        except requests.exceptions.ReadTimeout:
            logger.warn('Timeout:' + imgurl)
            continue
    raise Exception('retry count reach 10')



def zip_dir(dirname,zipfilename):
    filelist = []
    if os.path.isfile(dirname):
        filelist.append(dirname)
    else:
        for root, dirs, files in os.walk(dirname):
            for name in files:
                filelist.append(os.path.join(root, name))
    zf = zipfile.ZipFile(zipfilename, "w", zipfile.zlib.DEFLATED)
    for tar in filelist:
        arcname = tar[len(dirname.name):]
        zf.write(tar,arcname)
    zf.close()


def normalize_url(url):
    if url.endswith('/'):
        url = url[:-1]
    return url


def download_gallery(url):
    global TMPDIR
    global logger

    url = normalize_url(url) 

    tmpdir_parent = '/dev/shm' if Path('/dev/shm').is_dir() else None
    scriptname_wo_ext = Path(__file__).name.replace('.py', '')
    url_pieces = url.split('/')
    signature = '_'.join(url_pieces[-2:])
    workdir = TemporaryDirectory(dir=tmpdir_parent, prefix=scriptname_wo_ext + signature)

    index = lxml.etree.HTML(req.get(url).text)

    title_xpath_candidates = (
            '//h1[@id="gj"]/text()',
            '//h1[@id="gn"]/text()',
            '//title/text()',
            '//h1[0]/text()',
    )
    title = None
    for title_xpath_cand in title_xpath_candidates:
        title = index.xpath(title_xpath_cand)
        if title:
            break

    title = title[0]
    basename = title_to_basename(title)
    logger.info(f'title: {title}')
    workdir_g = Path(workdir.name) / basename
    logger.info(f'images once downloaded into: {workdir_g}')
    Path(workdir_g).mkdir()

    all_subURL = index.xpath('//div[@class="gdtm"]/div/a')
    nexturl = all_subURL[0].attrib['href']
    picurl = None
    logger.info(('nexturl:' + nexturl))

    while True:
        picurl = nexturl

        for retry in range(0, 10):
            try:
                text = req.get(picurl).text
                break
            except requests.exceptions.ConnectionError:
                logger.warn(f'ConnectionError: {picurl}')

        if retry == 10:
            raise Exception(f'Retry count reach 10: {picurl}')

        page = lxml.etree.HTML(text)
        img = page.xpath('//*[@id="img"]')[0]
        nextpic = page.xpath('//div[@id="i3"]/a')[0]
        nl = page.xpath('//a[@id="loadfail"]')[0]

        imgurl = img.attrib['src']
        nexturl = nextpic.attrib['href']
        nlid = nl.attrib['onclick'].split("'")[1]

        if '/g/509.gif' in imgurl:
            logger.warn(f'509 BRNDWIDTH EXCEEDED: {url}')
            time.sleep(config.bandwidth_exceeded_wait)
            nexturl = picurl
            continue

        if 'keystamp=' in imgurl:
            if not 'nl=' in picurl:
                nexturl = picurl + '?nl=' + nlid
        else:
            time.sleep(config.reget_wait_sec)
            downloadImageFile(workdir_g, imgurl)
            if picurl.split('?')[0] == nexturl:
                logger.info(f'{picurl} is successfully downloaded')
                break

    zip_dir(workdir_g, basename+'.zip')

    shutil.rmtree(workdir.name)


def title_to_basename(title):
    basename = title.strip()\
                    .replace('|', '')\
                    .replace(':', '')\
                    .replace('/', '')
    return basename


def download_galleries(urls):
    for url in urls:
        download_gallery(url)


parser = ArgumentParser()
list_or_file = parser.add_mutually_exclusive_group()
list_or_file.add_argument('--urls', '-u', nargs='*', type=str,
                          default=None, required=False,
                          help="specify urls directory")
list_or_file.add_argument('--list', '-l', nargs='?',
                          type=FileType('r'),
                          default=None, required=False,
                          help="a file include url list")
def main():
    global logger
    global parser
    argv = parser.parse_args()
    Log_Format = "%(levelname)s %(asctime)s - %(message)s"
    logging.basicConfig(
                    stream = sys.stdout,
                    filemode = "w",
                    format = Log_Format,
                    level = logging.INFO
                    )
    logger = logging.getLogger(__name__)

    if argv.list:
        urls = argv.list.read().strip().split('\n')
    elif argv.urls:
        urls = argv.urls
    else:
        raise Exception(
                "at least one of urls or list must be specified.")
    download_galleries(urls)


if __name__ == '__main__':
    main()
