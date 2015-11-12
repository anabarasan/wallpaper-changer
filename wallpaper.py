import ctypes
import ctypes.wintypes
import logging
import os
import os.path
import sys
import time
import urllib2

# third party
from bs4 import BeautifulSoup

# log config
logging.basicConfig(stream=sys.stdout,
                    # filename='smashingmagazine.log',
                    # filemode='w',
                    format='%(asctime)s : %(levelname)s : %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)

def get_user_pictures_location():
    # http://stackoverflow.com/questions/6227590/finding-the-users-my-documents-path
    buf=ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
    ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_MYPICTURES, None, SHGFP_TYPE_CURRENT, buf)
    return buf.value

# required date values in required formats
WALLPAPER_MONTH = time.strftime('%B').lower()     # January
WALLPAPER_YEAR = time.strftime('%Y')              # 2015
CURRENT_DATE = int(time.strftime('%d'))
CURRENT_MONTH = int(time.strftime('%m'))          # 1
SUBMISSION_MONTH = 12 if CURRENT_MONTH - 1 == 0 else CURRENT_MONTH - 1
SUBMISSION_YEAR = WALLPAPER_YEAR - 1 if CURRENT_MONTH - 1 == 0 else WALLPAPER_YEAR

# get my pictures folder
# https://msdn.microsoft.com/en-us/library/windows/desktop/dd378457(v=vs.85).aspx
# http://winbatch.hpdd.de/MyWbtHelp/other/CSIDL.txt
CSIDL_PERSONAL = 5        # My Documents
CSIDL_MYPICTURES = 39     # My Pictures
SHGFP_TYPE_CURRENT = 1    # Get current, not default value
MY_PICTURES = '%s/%s/%s' % (get_user_pictures_location(), WALLPAPER_YEAR, CURRENT_MONTH)

# Base Url which lists the current months wallpapers
WALLPAPER_LIST_URL = 'http://www.smashingmagazine.com/%s/%s/desktop-wallpaper-calendars-%s-%s'
WALLPAPER_RESOLUTION = '2560x1440' #'1920x1080'

def prepareSoup(URL):
    logging.info('Preparing Soup with url : %s' % URL)
    response = urllib2.urlopen(URL)
    return BeautifulSoup(response.read(), 'html.parser')

def get_wallpaper_list_page():
    URL =  WALLPAPER_LIST_URL % (SUBMISSION_YEAR, SUBMISSION_MONTH, WALLPAPER_MONTH, WALLPAPER_YEAR)
    logging.info('List Page URL : %s' % URL)
    try:
        return prepareSoup(URL)
    except:
        logging.error('unable to fetch wallpaper list')
        raise

def get_wallpaper_list(wallpaper_list_page):
    # try to get the wallpapers for the current month from Smashing Magazine.
    article = wallpaper_list_page.find('article')
    wallpaper_titles = article.find_all('h3')
    for wallpaper_title in wallpaper_titles:
        logging.debug(wallpaper_title.contents[0])
        wallpaper_link_lists = wallpaper_title.find_next_sibling('ul')
        if 'Join In Next Month!' not in wallpaper_title.contents[0].string.strip():
            for wallpaper_link_list in wallpaper_link_lists.find_all('li'):
                if 'with calendar' in wallpaper_link_list.contents[0].string.strip():
                    for link in wallpaper_link_list.find_all('a'):
                        if WALLPAPER_RESOLUTION in link.get('href'):
                            download(link.get('href'))
                            break
                    else:
                        logging.debug('Required RESOLUTION not available')

def download(URL):
    # check if the save location exists, if not create it
    if not os.path.exists(MY_PICTURES):
        logging.info('Creating save location : %s' % MY_PICTURES)
        os.makedirs(MY_PICTURES)
    file_name = '%s/%s' % (MY_PICTURES, URL.split('/')[-1])
    
    # progress bar implementation copied from
    # http://stackoverflow.com/questions/22676/how-do-i-download-a-file-over-http-using-python
    if not os.path.isfile(file_name):
        logging.info('Downloading from %s' % URL)
        logging.info('Downloading to %s' % file_name)
        response = urllib2.urlopen(URL)
        f = open(file_name, 'wb')
        meta = response.info()
        file_size = int(meta.getheaders("Content-Length")[0])
        print "Downloading: %s Bytes: %s" % (file_name, file_size)

        file_size_dl = 0
        block_sz = 8192
        while True:
            buffer = response.read(block_sz)
            if not buffer:
                break

            file_size_dl += len(buffer)
            f.write(buffer)
            status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
            status = status + chr(8)*(len(status)+1)
            print status,

        f.close()

def select_wallpaper():
    wallpaper_list = os.listdir(MY_PICTURES)
    selected_wallpaper = wallpaper_list[CURRENT_DATE % len(wallpaper_list)]
    logging.info('selected wallpaper : %s' % selected_wallpaper)
    return os.path.join(MY_PICTURES, selected_wallpaper)

def set_wallpaper(URI):
    #http://stackoverflow.com/questions/1977694/change-desktop-background
    try:
        URI = URI.replace('\\', '/')
        logging.info('setting wallpaper %s' % URI)
        # SystemParametersInfoA() doesn't work with file names with Unicode chars
        # so using SystemParametersInfoW() which works with Unicode chars
        ret = ctypes.windll.user32.SystemParametersInfoW(20, 0, URI, 3)
        logging.debug(ret)
    except:
        logging.error('unable to set wallpaper')
        logging.error(ctypes.FormatError())

if __name__ == '__main__':
    if not os.path.exists(MY_PICTURES):
        wallpaper_list_page = get_wallpaper_list_page()
        get_wallpaper_list(wallpaper_list_page)
    wallpaper = select_wallpaper()
    set_wallpaper(wallpaper)
