# e-hentai downloder

This program is a folk of [`e-hentai`](https://github.com/AnnieBrighton/e-hentai) by AnnieBrighton-san.

## environment

Python3 (develop in Python3.10 environment）

## Install

You can install this script into your local Python environment by
```shell
git clone <this-repos-url>
pip install -e .
```

## Usage

### specifing urls direcotry

```shell
$ eht-dl -u https://e-hentai.org/g/2358461/4de61f3815/
```

if no error occur, the program make a zip file in the current directoryas following
(assuming no other zip file in the working directory):

```shell
$ md5sum *.zip
654f30f6a9d7683ce9261bfe74d53e10  AI Art Tests [ai stable diffusion  tool aiimag.es].zip
```

### specifying urls by a list file

```shell
$ eht-dl -l ~~some_url_list.txt~~
```
