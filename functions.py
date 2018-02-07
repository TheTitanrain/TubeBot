# -*- coding: utf-8 -*-
import config
import os
import re
import logging
from configparser import ConfigParser
from urllib.parse import urlparse
import traceback


def correct_link(link):
    parseurl = urlparse(link)
    time_sec = 0
    if not parseurl.netloc == '':
        if parseurl.netloc == 'youtube.com' or \
                parseurl.netloc == 'youtu.be' or \
                parseurl.netloc == 'youtube.be' or \
                parseurl.netloc == 'www.youtube.com' or \
                parseurl.netloc == 'm.youtube.com':
            return True, True
        else:
            return True, False
    else:
        return False, False


def get_chat_id_list():
    tree = os.walk(config.PATH_SETTINGS_DIR)
    id_list = []
    for d, dirs, files in os.walk(config.PATH_SETTINGS_DIR):
        for f in files:
            f_str = str(f)
            f_str = f_str[2:-5]
            id_list.append(int(f_str))
    print(id_list)
    return id_list


def check_is_admin(settings, user_id):
    try:
        admin_id_str = settings.get('ADMINS', 'id')
        id_list_str = re.split(r',', admin_id_str, flags=re.UNICODE)
        for id_str in id_list_str:
            if int(id_str) == user_id:
                return True
        return False
    except Exception as e:
        logging.error(str(e))
        return False


def init_user_settings(chat_id):
    try:
        settings_filename = 'id%s.conf' % str(chat_id)
        path_settings_file = os.path.join(config.PATH_SETTINGS_DIR, settings_filename)
        user_settings = ConfigParser()
        if not os.path.exists(path_settings_file):
            settings_fp = open(path_settings_file, 'w')
            settings_fp.close()
        print(path_settings_file)
        user_settings.read(path_settings_file)
        if not user_settings.has_section(str(chat_id)):
            user_settings.add_section(str(chat_id))
        if not user_settings.has_option(str(chat_id), 'get_video'):
            user_settings.set(str(chat_id), 'get_video', 'False')
        if not user_settings.has_option(str(chat_id), 'bitrate'):
            user_settings.set(str(chat_id), 'bitrate', '192')
        if not user_settings.has_option(str(chat_id), 'audio_codec'):
            user_settings.set(str(chat_id), 'audio_codec', 'aac')
        if not user_settings.has_option(str(chat_id), 'request_n'):
            user_settings.set(str(chat_id), 'request_n', '0')
        if not user_settings.has_option(str(chat_id), 'lang'):
            user_settings.set(str(chat_id), 'lang', 'eng')
        if not user_settings.has_option(str(chat_id), 'ad_flag'):
            user_settings.set(str(chat_id), 'ad_flag', 'False')
        if not user_settings.has_option(str(chat_id), 'request_counter'):
            user_settings.set(str(chat_id), 'request_counter', '0')
        settings_fp = open(path_settings_file, 'w')
        user_settings.write(settings_fp)
        settings_fp.close()
        return user_settings
    except Exception as e:
        logging.error(str('init_user_settings:') + str(e))
        return None


def set_user_settings(chat_id, option, value):
    settings_filename = 'id%s.conf' % str(chat_id)
    path_settings_file = os.path.join(config.PATH_SETTINGS_DIR, settings_filename)
    user_settings = ConfigParser()
    user_settings.read(path_settings_file)
    user_settings.set(str(chat_id), str(option), str(value))
    settings_fp = open(path_settings_file, 'w')
    user_settings.write(settings_fp)
    settings_fp.close()


def get_user_settings(chat_id, option):
    settings_filename = 'id%s.conf' % str(chat_id)
    path_settings_file = os.path.join(config.PATH_SETTINGS_DIR, settings_filename)
    user_settings = ConfigParser()
    user_settings.read(path_settings_file)
    value = user_settings.get(str(chat_id), str(option))
    return value