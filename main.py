# -*- coding: utf-8 -*-
import config
import telebot
# import vimeo_dl as vimeo
import io
# import sqlite3
#from telebot import apihelper
#from os.path import join, getsize
import os
import re
import functions
# import unicodedata
# import codecs
# import fnmatch
# #import eventlet
# import requests
import logging
from configparser import ConfigParser
from telebot import types
from moviepy.editor import *
from pytube import YouTube
from time import sleep
# import time
#from transliterate import translit, get_available_language_codes
import shutil
from threading import Thread
from threading import Lock
import youtube_dl
# import sys
import time

download_users_counter = 0
download_users_lock = Lock()
bot = telebot.TeleBot(config.token)
settings_lock = Lock()
def close_clip(clip):
    try:
        clip.reader.close()
        del clip.reader
        if clip.audio != None:
            clip.audio.reader.close_proc()
            del clip.audio
        del clip
    except Exception as e:
        print (e)
        logging.error(str(e))
        #sys.exc_clear()


class ProgressBar(Thread):
    def __init__(self, name,message,file_size,file_handle,caption):
        Thread.__init__(self)
        self.name = name
        self.message = message
        self.file_size = file_size
        self.file_handle = file_handle
        self.caption = caption
    def run(self):
        show_progress(self.message, self.file_size, self.file_handle, self.caption)
        msg = "%s is running" % self.name
        print(msg)


def show_progress(message,file_size,file_handle,caption):
    timeout = 200
    while (not os.path.exists(file_handle)) and (timeout > 0):
        sleep(0.5)
        timeout -= 1
    bytes_received = os.path.getsize(file_handle)
    file_size_mb = file_size/1024/1024
    while bytes_received < file_size:
        percent = int(100 * bytes_received / file_size)
        try:
            bot.edit_message_text(text=((caption + (u' %dМб, ждите ' % file_size_mb)) + str(percent)+'%'),
                                  chat_id=message.chat.id,
                                  message_id=message.message_id)
            bot.send_chat_action(message.chat.id, 'record_video')
        except Exception as e:
            print (e)
        sleep(0.5)
        bytes_received = os.path.getsize(file_handle)
    try:
        bot.edit_message_text(text=(('%s %dМб, ждите ' % (caption, file_size_mb)) + '100%'),
                              chat_id=message.chat.id,
                              message_id=message.message_id)
        bot.send_chat_action(message.chat.id, 'record_video')
        sleep(0.2)
    except Exception as e:
        print(e)

    return


class ProgressAudio(Thread):
    def __init__(self, name, message, file_size, file_handle):
        Thread.__init__(self)
        self.name = name
        self.message = message
        self.file_size = file_size
        self.file_handle = file_handle
        self.enable = True

    def run(self):
        while self.enable:
            try:
                bot.send_chat_action(self.message.chat.id, 'record_audio')
                sleep(0.5)
            except Exception as e:
                logging.error(e)
        # show_progress_audio(self.message,self.file_size,self.file_handle)


def show_progress_audio(message,file_size,file_handle):
    while True:
        try:
            # percent = int(100 * bytes_received / file_size)
            # bot.edit_message_text(text=(('Конвертирую аудио, ждите ') + str(percent) + '%'),chat_id=message.chat.id, message_id=message.message_id)
            bot.send_chat_action(message.chat.id, 'record_audio')
            sleep(0.5)
            # bytes_received = os.path.getsize(file_handle)
        except Exception as e:
            logging.error(e)
    return


class ProcessMessage(Thread):
    def __init__(self, name,message):
        Thread.__init__(self)
        self.name = name
        self.message = message
    def run(self):
        process_message(self.message)
        msg = "%s is running" % self.name
        print(msg)


class ProcessCall(Thread):
    def __init__(self, name,call):
        Thread.__init__(self)
        self.name = name
        self.call = call
    def run(self):
        callback_button(self.call)
        msg = "%s is running" % self.name
        print(msg)

@bot.callback_query_handler(func=lambda call: True)
def create_callback_thread(call):
    name = "Thread #%s" % (call.message.message_id)
    call_thread = ProcessCall(name,call)
    call_thread.start()


def callback_button(call):
    try:
        chat_id = call.message.chat.id
        user_settings = functions.init_user_settings(chat_id)
        if call.message:
            data = call.data
            if data[:len('cancel')] == 'cancel':
                bot.answer_callback_query(call.id)
                bot.delete_message(call.message.chat.id, call.message.message_id)
            elif data[:len('bitrate=')] == 'bitrate=':
                bitrate = data[len('bitrate='):len('bitrate=') + len('123k')]
                if bitrate == '320k':
                    functions.set_user_settings(chat_id, 'bitrate', '320')
                    bot.answer_callback_query(call.id,
                                              text="Audio quality: 320Кбит/с - best\nAudio length: 20мин",
                                              show_alert=True)
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                elif bitrate == '192k':
                    functions.set_user_settings(chat_id, 'bitrate', '192')
                    bot.answer_callback_query(call.id,
                                              text="Audio quality: 192Кбит/с - good\nAudio length: 30мин",
                                              show_alert=True)
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                elif bitrate == '128k':
                    functions.set_user_settings(chat_id, 'bitrate', '128')
                    bot.answer_callback_query(call.id,
                                              text="Audio quality: 128Кбит/с - acceptable\nAudio length: 40мин",
                                              show_alert=True)
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                elif bitrate == '096k':
                    functions.set_user_settings(chat_id, 'bitrate', '96')
                    bot.answer_callback_query(call.id,
                                              text="Audio quality: 96Кбит/с - worst\nAudio length: 50мин",
                                              show_alert=True)
                    bot.delete_message(call.message.chat.id, call.message.message_id)
            # elif data[:len('get_video=')] == 'get_video=':
            #     new_status = data[len('get_video='):]
            #     functions.set_user_settings(chat_id, 'get_video', str(new_status))
            #     bot.delete_message(call.message.chat.id, call.message.message_id)
            #     if new_status == 'True':
            #         bot.answer_callback_query(call.id, text="Загрузка видео + аудио", show_alert=True)
            #     else:
            #         bot.answer_callback_query(call.id, text="Загрузка только аудио", show_alert=True)
            elif data[:len('audio_codec=')] == 'audio_codec=':
                new_status = data[len('audio_codec='):]
                functions.set_user_settings(chat_id, 'audio_codec', str(new_status))
                bot.delete_message(call.message.chat.id, call.message.message_id)
                bot.answer_callback_query(call.id, text=(u'Audio codec: ' + new_status), show_alert=True)
    except Exception as e:
        logging.error(str('callback_button:') + str(e))


@bot.message_handler(commands=['reset_request_n'])
def reset_request_n(message):
    try:
        user_id = message.from_user.id
        bot_settings = ConfigParser()
        bot_settings.read(config.PATH_SETTINGS_FILE)
        user_settings = ConfigParser()
        if functions.check_is_admin(bot_settings, user_id):
            for d, dirs, files in os.walk(config.PATH_SETTINGS_DIR):
                for f in files:
                    path_settings_file = os.path.join(config.PATH_SETTINGS_DIR, f)
                    user_settings.read(path_settings_file)
                    user_settings.set(f[2:-5], 'request_n', '0')
                    settings_fp = open(path_settings_file, 'w')
                    user_settings.write(settings_fp)
                    settings_fp.close()

    except Exception as e:
        logging.error(e)


@bot.message_handler(commands=['notify_all'])
def send_notification(message):
    try:
        # chat_id = message.chat.id
        user_id = message.from_user.id
        bot_settings = ConfigParser()
        bot_settings.read(config.PATH_SETTINGS_FILE)
        if functions.check_is_admin(bot_settings,
                                    user_id):
            id_list = functions.get_chat_id_list()
            message_fp = io.open(config.PATH_MESSAGES_UPDATE_FILE,
                                 encoding='utf8',
                                 mode='r')
            message_to_send = message_fp.read()
            message_fp.close()
            for id in id_list:
                if id > 0:
                    try:
                        bot.send_message(id,
                                         parse_mode='Markdown',
                                         text=message_to_send)
                    except Exception as e:
                        logging.error(e)
    except Exception as e:
        logging.error(e)


@bot.message_handler(commands=['donate'])
def show_donate_message(message):
    try:
        chat_id = message.chat.id
        message_fp = io.open(config.PATH_MESSAGES_DONATE_FILE,encoding='utf8', mode='r')
        message_to_send = message_fp.read()
        message_fp.close()
        bot.send_message(chat_id,
                         parse_mode='Markdown',
                         text=message_to_send,
                         disable_notification=True)
    except Exception as e:
        logging.error(str('show_faq:') + str(e))


@bot.message_handler(commands=['donate_eth'])
def show_donate_eth_message(message):
    try:
        chat_id = message.chat.id
        message_fp = io.open(config.PATH_MESSAGES_DONATE_ETH_FILE,encoding='utf8', mode='r')
        message_to_send = message_fp.read()
        message_fp.close()
        bot.send_message(chat_id,
                         parse_mode='Markdown',
                         text=message_to_send,
                         disable_notification=True)
    except Exception as e:
        logging.error(str('show_faq:') + str(e))


@bot.message_handler(commands=['donate_paypal'])
def show_donate_paypal_message(message):
    try:
        chat_id = message.chat.id
        message_fp = io.open(config.PATH_MESSAGES_DONATE_PAYPAL_FILE,encoding='utf8', mode='r')
        message_to_send = message_fp.read()
        message_fp.close()
        bot.send_message(chat_id,
                         parse_mode='Markdown',
                         text=message_to_send,
                         disable_notification=True)
    except Exception as e:
        logging.error(str('show_faq:') + str(e))


@bot.message_handler(commands=['donate_card'])
def show_donate_card_message(message):
    try:
        chat_id = message.chat.id
        message_fp = io.open(config.PATH_MESSAGES_DONATE_CARD_FILE,
                             encoding='utf8',
                             mode='r')
        message_to_send = message_fp.read()
        message_fp.close()
        bot.send_message(chat_id, parse_mode='Markdown',
                         text=message_to_send,
                         disable_notification=True)
    except Exception as e:
        logging.error(str('show_faq:') + str(e))


@bot.message_handler(commands=['donate_btc'])
def show_donate_btc_message(message):
    try:
        chat_id = message.chat.id
        message_fp = io.open(config.PATH_MESSAGES_DONATE_BTC_FILE,
                             encoding='utf8',
                             mode='r')
        message_to_send = message_fp.read()
        message_fp.close()
        bot.send_message(chat_id, parse_mode='Markdown',
                         text=message_to_send,
                         disable_notification=True)
    except Exception as e:
        logging.error(str('show_faq:') + str(e))


@bot.message_handler(commands=['faq'])
def show_faq_message(message):
    try:
        chat_id = message.chat.id
        message_fp = io.open(config.PATH_MESSAGES_FAQ_FILE,
                             encoding='utf8',
                             mode='r')
        message_to_send = message_fp.read()
        message_fp.close()
        bot.send_message(chat_id,
                         parse_mode='Markdown',
                         text=message_to_send,
                         disable_notification=True,
                         disable_web_page_preview=True)
    except Exception as e:
        logging.error(str('show_faq:') + str(e))


@bot.message_handler(commands=['help'])
def show_help_message(message):
    try:
        chat_id = message.chat.id
        message_fp = io.open(config.PATH_MESSAGES_HELP_FILE,
                             encoding='utf8',
                             mode='r')
        message_to_send = message_fp.read()
        message_fp.close()
        bot.send_message(chat_id,
                         parse_mode='Markdown',
                         text=message_to_send,
                         disable_notification=True)
    except Exception as e:
        logging.error(str('show_help:') + str(e))


@bot.message_handler(commands=['codec'])
def set_audio_codec(message):
    try:
        chat_id = message.chat.id
        user_settings = functions.init_user_settings(chat_id)
        us_get_audio_codec = functions.get_user_settings(chat_id, 'audio_codec')
        keyboard = types.InlineKeyboardMarkup()
        cancel_button = types.InlineKeyboardButton(text="Cancel", callback_data='cancel')
        aac_codec_button = types.InlineKeyboardButton(text='aac', callback_data='audio_codec=aac')
        ogg_codec_button = types.InlineKeyboardButton(text='ogg', callback_data='audio_codec=ogg')
        mp3_codec_button = types.InlineKeyboardButton(text='mp3', callback_data='audio_codec=mp3')
        if us_get_audio_codec == 'aac':
            keyboard.add(mp3_codec_button,ogg_codec_button)
        elif us_get_audio_codec == 'mp3':
            keyboard.add(aac_codec_button, ogg_codec_button)
        elif us_get_audio_codec == 'ogg':
            keyboard.add(aac_codec_button, mp3_codec_button)
        keyboard.add(cancel_button)
        text_audio_codec = u'Current codec: *%s*' % us_get_audio_codec
        bot.send_message(message.chat.id,
                         parse_mode='Markdown',
                         text=text_audio_codec,
                         reply_markup=keyboard)
    except Exception as e:
        logging.error(str('set_video_download_flag:') + str(e))


# @bot.message_handler(commands=['video'])
# def set_video_download_flag(message):
#     try:
#         chat_id = message.chat.id
#         settings_filename = 'id%s.conf' % str(chat_id)
#         path_settings_file = os.path.join(config.PATH_SETTINGS_DIR, settings_filename)
#         user_settings = ConfigParser()
#         # with settings_lock:
#         user_settings.read(path_settings_file)
#         if not user_settings.has_section(str(chat_id)):
#             user_settings.add_section(str(chat_id))
#             user_settings.set(str(chat_id), 'bitrate', '192')
#             user_settings.set(str(chat_id), 'get_video', 'False')
#             settings_fp = open(path_settings_file, 'w')
#             user_settings.write(settings_fp)
#             settings_fp.close()
#         if not user_settings.has_option(str(chat_id), 'get_video'):
#             user_settings.set(str(chat_id), 'get_video', 'False')
#         us_get_video = user_settings.get(str(chat_id), 'get_video')
#         keyboard = types.InlineKeyboardMarkup()
#         cancel_button = types.InlineKeyboardButton(text="Отмена", callback_data=('cancel'))
#         if us_get_video == 'True':
#             get_video_button = types.InlineKeyboardButton(text="Отключить", callback_data=('get_video=False'))
#             text_get_video = u'Загрузка видео (до 50Мб): *Включена*'
#         else:
#             get_video_button = types.InlineKeyboardButton(text="Включить", callback_data=('get_video=True'))
#             text_get_video = u'Загрузка видео (до 50Мб): *Отключена*'
#         keyboard.add(get_video_button,cancel_button)
#         bot.send_message(message.chat.id,parse_mode='Markdown',text = text_get_video ,reply_markup=keyboard)
#     except Exception as e:
#         logging.error(str('set_video_download_flag:') + str(e))


@bot.message_handler(commands=['bitrate'])
def set_sound_quality(message):
    try:
        chat_id = message.chat.id
        settings_filename = 'id%s.conf' % str(chat_id)
        path_settings_file = os.path.join(config.PATH_SETTINGS_DIR, settings_filename)
        user_settings = ConfigParser()
        # with settings_lock:
        user_settings.read(path_settings_file)
        if not user_settings.has_section(str(chat_id)):
            user_settings.add_section(str(chat_id))
            user_settings.set(str(chat_id), 'bitrate', '192k')
            settings_fp = open(path_settings_file, 'w')
            user_settings.write(settings_fp)
            settings_fp.close()
        us_bitrate = user_settings.get(str(chat_id), 'bitrate')
        keyboard = types.InlineKeyboardMarkup()
        cancel_button = types.InlineKeyboardButton(text="Cancel", callback_data='cancel')
        button_320k = types.InlineKeyboardButton(text="320 Kbit/s", callback_data='bitrate=320k')
        button_192k = types.InlineKeyboardButton(text="192 Kbit/s", callback_data='bitrate=192k',)
        button_128k = types.InlineKeyboardButton(text="128 Kbit/s", callback_data='bitrate=128k')
        button_096k = types.InlineKeyboardButton(text="96 Kbit/s", callback_data='bitrate=096k')
        keyboard.add(button_096k, button_128k, button_192k, button_320k, cancel_button)
        if us_bitrate == '320':
            text_bitrate = u'*320 Kbit/s*'
        elif us_bitrate == '192':
            text_bitrate = u'*192 Kbit/s*'
        elif us_bitrate == '128':
            text_bitrate = u'*128 Kbit/s*'
        elif us_bitrate == '96':
            text_bitrate = u'*96 Kbit/s*'
        bot.send_message(message.chat.id,
                         parse_mode='Markdown',
                         text=(u'Current bitrate: ' + text_bitrate),
                         reply_markup=keyboard)
    except Exception as e:
        logging.error(str('set_sound_quality:') + str(e))


@bot.message_handler(commands=['start'])
def send_startup_message(message):
    chat_id = message.chat.id
    # user_settings = functions.init_user_settings(chat_id)
    try:
        message_fp = io.open(config.PATH_MESSAGES_START_FILE, encoding='utf8', mode='r')
        message_to_send = message_fp.read()
        message_fp.close()
        bot.send_message(chat_id,
                         text=message_to_send,
                         parse_mode='Markdown',
                         disable_web_page_preview=True)
    except Exception as e:
        logging.error(str('send_startup_message:') + str(e))
# @bot.message_handler(commands=['playlist'])
# def move_to_playlist(message):
#     keyboard = types.InlineKeyboardMarkup()
#     button_donat = types.InlineKeyboardButton(text="Музыка",url='https://t.me/joinchat/AAAAAE8-5q17REFmmfVBcQ')
#     keyboard.add(button_donat)
#     bot.send_message(message.chat.id, text = 'Ваши плейлисты:',reply_markup=keyboard,parse_mode='Markdown', disable_web_page_preview=True)


@bot.message_handler(content_types=["text"])
def create_threads(message):
    name = "Thread #%s" % (message.message_id)
    my_thread = ProcessMessage(name, message)
    my_thread.start()


def process_message(message):
    user_id = message.from_user.id
    link = message.text
    logging.info('{!s}'.format(str(message.chat.id) + ' ' + link))
    chat_id = message.chat.id
    correct, youtube = functions.correct_link(link)
    global download_users_counter

    if correct:
        user_settings = ConfigParser()
        try:
            user_settings = functions.init_user_settings(chat_id)
            if user_settings:
                us_bitrate = user_settings.get(str(chat_id), 'bitrate')
                # us_get_video = user_settings.get(str(chat_id), 'get_video')
                us_request_n = int(user_settings.get(str(chat_id), 'request_n'))
                us_audio_codec = user_settings.get(str(chat_id), 'audio_codec')
                if us_audio_codec == 'aac':
                    audio_codec_string = 'aac'
                elif us_audio_codec == 'mp3':
                    audio_codec_string = 'libmp3lame'
                elif us_audio_codec == 'ogg':
                    audio_codec_string = 'libvorbis'
            else:
                bot.send_message(chat_id=chat_id,
                                 text=u"Getting settings error.")
                logging.error(str('Param user_settings is None.'))
                return
        except Exception as e:
            bot.send_message(chat_id=chat_id,
                             text=u"Get settings error. " + str(e))
            logging.error(str('process_message:') + str(e))
            return
        hashtag_match = re.match(r'#\w+', link, flags=re.UNICODE)
        print(user_id)
        if us_request_n == 0 or user_id == 115263918:
            try:
                # with settings_lock:
                functions.set_user_settings(chat_id, 'request_n', '1')
                tmpdir = str(chat_id)

                # if tmpdir.find('?t=') != -1:
                #     cut_range = tmpdir[tmpdir.find('?t=') + 3:]
                #     cut_start = cut_range[:cut_range.find('s')]
                #     cut_end = cut_range[cut_range.find('s') + 1:]
                #     if cut_end.find('s') != -1:
                #         cut_end = cut_end[:cut_end.find('s')]
                #         cut_end = int(cut_end)
                #     else:
                #         cut_end = None
                #     cut_start = int(cut_start)
                #     need_cut = True
                # else:
                #     cut_start = None
                #     cut_end = None
                #     need_cut = False
                # for c in ['&', '?', '=']:
                #     if tmpdir.find(c) != -1:
                #         tmpdir = tmpdir[:tmpdir.find(c)]
                #
                # if not os.path.exists(tmpdir):
                #     os.mkdir(tmpdir)

                try:
                    msg_wait = bot.send_message(chat_id,
                                                "Getting video information...",
                                                reply_to_message_id=message.message_id)

                    # if link.find(u'vimeo.com') != -1:
                    #     vm_video = vimeo.new(link)
                    #     vm_best = vm_video.getbest()
                    #     video_title = vm_best.title
                    #     # video_filesize = 100500
                    #     msg_wait = bot.edit_message_text(chat_id=chat_id,
                    #                                      message_id=msg_wait.message_id,
                    #                                      text="Загружаю видео на сервер, ждите... vimeo тестируется")
                    #     vm_best.download(filepath=path_file, quiet=True)
                    #
                    # else:
                    #     video_title = YouTube(link).streams.get_by_itag(18).player_config['args']['title']
                    #     video_filesize = YouTube(link).streams.get_by_itag(18).filesize
                    def convert(path_file, audio_codec_string):
                        clip = AudioFileClip(path_file)
                        audio = clip

                        duration = audio.duration
                        bot.send_chat_action(chat_id, 'record_audio')

                        bot.edit_message_text(chat_id=chat_id,
                                              message_id=msg_wait.message_id,
                                              text='Converting audio {0} Kbit/s, wait...'.format(us_bitrate))
                        bitrate_duration = {'320': 1200,
                                            '192': 1800,
                                            '128': 2400,
                                            '96': 3000}
                        max_pduration = bitrate_duration[us_bitrate]
                        # if us_bitrate == '320':
                        #     max_pduration = 1200
                        # elif us_bitrate == '192':
                        #     max_pduration = 1800
                        # elif us_bitrate == '128':
                        #     max_pduration = 2400
                        # elif us_bitrate == '96':
                        #     max_pduration = 3000
                        # else:
                        #     max_pduration = 1800

                        sec_per_mb = max_pduration / 30
                        parts = 1 + int(duration/max_pduration)
                        path_file_mp3 = '{0}.{1}'.format(os.path.splitext(path_file)[0], us_audio_codec)
                        print(duration, parts)
                        for pn in range(parts):
                            if (pn + 1) * max_pduration > duration:
                                pduration = duration - pn * max_pduration
                                piece = audio.subclip(pn * max_pduration, duration)
                            else:
                                piece = audio.subclip(pn * max_pduration, (pn + 1) * max_pduration)
                                pduration = max_pduration
                            if parts > 1:
                                file_name = '{0}_{1}_of_{2}.{3}'.format(os.path.splitext(path_file)[0],
                                                                        str(pn+1),
                                                                        str(parts),
                                                                        us_audio_codec)
                                piece.write_audiofile(file_name,
                                                      bitrate=str(us_bitrate) + 'k',
                                                      codec=audio_codec_string)
                                f = open(file_name,
                                         'rb')
                                bot.send_audio(message.chat.id,
                                               f,
                                               title='{0}_{1}/{2}'.format(path_file_mp3, str(pn+1), str(parts)),
                                               duration=pduration)
                                f.close()
                            else:
                                encode_progress = ProgressAudio(tmpdir,
                                                                msg_wait,
                                                                int(pduration / sec_per_mb),
                                                                path_file_mp3)
                                encode_progress.start()
                                piece.write_audiofile(str(path_file_mp3),
                                                      bitrate='{0}k'.format(str(us_bitrate)),
                                                      codec=audio_codec_string)
                                encode_progress.enable = False
                                f = open(path_file_mp3, 'rb')
                                bot.send_audio(message.chat.id,
                                               f,
                                               title=path_file_mp3,
                                               duration=pduration)
                                f.close()

                    def my_hook(d):
                        if d['status'] == 'finished':
                            bot.edit_message_text(chat_id=chat_id,
                                                  message_id=msg_wait.message_id,
                                                  text='Done. Converting...')
                            path_file = d['filename']

                            convert(path_file, audio_codec_string)
                        # elif d['status'] == 'downloading':
                        #     print(d['eta'])
                        #     bot.edit_message_text(chat_id=chat_id,
                        #                           message_id=msg_wait.message_id,
                        #                           text='Downloading... %s' % str(d['eta']))
                    if youtube:
                        try:
                            def on_progress_download_video(self,chunk, file_handler, bytes_remaining):
                                global download_users_counter
                                if download_users_counter > 0:
                                    time.sleep(0.0002 * download_users_counter)
                            yt = YouTube(link)
                            streams_yt = yt.streams.all()
                            video_title = yt.streams.get_by_itag(18).player_config_args['title']
                            filename = yt.streams.get_by_itag(18).default_filename
                            print(filename)
                            video_filesize = yt.streams.get_by_itag(18).filesize
                            msg_wait = bot.edit_message_text(chat_id=chat_id,
                                                             message_id=msg_wait.message_id,
                                                             text='Downloading video to the server, wait...')
                            path_file = os.path.join(config.PATH_HOME, filename)
                            download_progress = ProgressBar(tmpdir,
                                                            msg_wait,
                                                            video_filesize,
                                                            path_file,
                                                            'Downloading video to server.')
                            download_progress.start()

                            YouTube(link,
                                    on_progress_callback=on_progress_download_video).streams.get_by_itag(18).\
                                download(output_path=config.PATH_HOME,
                                         filename=filename[:-3])
                            convert(filename, audio_codec_string)

                        except Exception as e:
                            logging.error(e)
                            bot.send_message(chat_id=chat_id, text=u"Download error. Try again later.")
                            # with settings_lock:
                            functions.set_user_settings(chat_id, 'request_n', 0)
                            os.chdir(config.PATH_HOME)
                            if os.path.exists(tmpdir):
                                shutil.rmtree(tmpdir)

                            with download_users_lock:
                                download_users_counter -= 1
                            return

                        with download_users_lock:
                            download_users_counter -= 1
                        logging.info('download_users_counter = %d' % download_users_counter)
                    else:
                        ydl_opts = {
                            'format': 'worstaudio/worst',
                            'progress_hooks': [my_hook],
                        }
                        msg_wait = bot.edit_message_text(chat_id=chat_id,
                                                         message_id=msg_wait.message_id,
                                                         text="Now downloading and converting video, wait...")

                        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                            result = ydl.extract_info(link, download=False)

                            if 'entries' in result:
                                for video in result:
                                    print(video)
                                    video_url = video['url']
                                    video_id = video['id']
                                    link = video['webpage_url']
                                    ascii_file_name = str(chat_id) + str(video_id) + '.' + us_audio_codec
                                    tmpdir = str(message.chat.id) + str(message.message_id)
                                    path_file = os.path.join(config.PATH_HOME,
                                                             tmpdir,
                                                             ascii_file_name)
                                    ydl.download([link])
                            else:
                                print(result)
                                # video_url = result['url']
                                # video_id = result['id']
                                link = result['webpage_url']
                                # ascii_file_name = str(chat_id) + str(video_id) + '.' + us_audio_codec
                                # tmpdir = str(message.chat.id) + str(message.message_id)
                                # path_file = os.path.join(config.PATH_HOME,
                                #                          tmpdir,
                                #                          ascii_file_name)
                                ydl.download([link])

                            bot.edit_message_text(chat_id=chat_id,
                                                  message_id=msg_wait.message_id,
                                                  text="Download done.")




                        #
                        #     download_progress = ProgressBar(tmpdir, msg_wait, video_filesize, \
                        #                                     path_file, u'Загружаю видео на сервер')
                        #     download_progress.start()
                        #     YouTube(link).streams.get_by_itag(18).download(output_path = os.path.join(config.PATH_HOME,tmpdir), \
                        #                                                    filename = ascii_file_name[:-4])
                            # if us_get_video == 'True' and (video_filesize/1024/1024 <= 50):
                            #     fv = open(str(path_file), 'rb')
                            #     bot.send_document(chat_id, fv, caption=video_title)
                            #     fv.close()
                            # elif us_get_video == 'True' and video_filesize/1024/1024 > 50:
                            #     bot.send_message(chat_id=chat_id,text="Размер файла превышает 50МБ разрешенные для ботов...")
                except Exception as e:
                    logging.error(e)
                    bot.send_message(chat_id=chat_id,
                                     text=u"Download or converting error. Try again. " + str(e))
                    # with settings_lock:
                    functions.set_user_settings(chat_id,
                                                'request_n',
                                                '0')
                    os.chdir(config.PATH_HOME)
                    if os.path.exists(tmpdir):
                        shutil.rmtree(tmpdir)
                    return
                #     try:
                #         # with settings_lock:
                #         counter = functions.get_user_settings(chat_id,'request_counter')
                #         counter = int(counter) + 1
                #         functions.set_user_settings(chat_id, 'request_counter', str(counter))
                #         functions.set_user_settings(chat_id,'ad_flag', 'False')
                #     except Exception as e:
                #         logging.error(str('process_message:') + str(e))
                #          # message = bot.send_message(chat_id, text=link,reply_markup=keyboard,disable_web_page_preview = True)
                #     finally:
                #         bot.delete_message(msg_wait.chat.id, msg_wait.message_id)
                # else:
                #     bot.edit_message_text(chat_id=chat_id, message_id=msg_wait.message_id,text='Таймкод начала превышает длительность видео')
            except Exception as e:
                logging.error(str('process_message:') + str(e))
                bot.send_message(chat_id=chat_id,
                                 text=u"Download error. Try again. " + str(e))
            finally:
                functions.set_user_settings(chat_id, 'request_n', '0')
                # close_clip(clip)
                # close_clip(clip_cut)
                os.chdir(config.PATH_HOME)
                # if os.path.exists(tmpdir):
                #     shutil.rmtree(tmpdir)

        elif us_request_n > 0:
            bot.send_message(chat_id=chat_id,
                             text='Only one video can be processed at a time.')
        elif hashtag_match:
            hashtag_match = re.match(r'#\w+', link, flags=re.UNICODE)
            hashtag_incoming = hashtag_match.group(0)
            message_reply = message.reply_to_message
            message_reply_audio = message_reply.audio
            if (message_reply is not None) and (message_reply_audio is not None):
                try:
                    bot.edit_message_caption(hashtag_incoming,chat_id,message_reply.message_id)
                    # user_settings = SafeConfigParser()
                    # user_settings.read(path_settings_file)
                    # if not user_settings.has_section(str(chat_id)):
                    #     user_settings.add_section(str(chat_id))
                    # if not user_settings.has_option(str(chat_id), str(hashtag_incoming)):
                    #     user_settings.set(str(chat_id), str(hashtag_incoming), str(message_reply.message_id) + '\n')
                    # else:
                    #     hashtag_msg_ids = user_settings.get(str(chat_id), str(hashtag_incoming))
                    #     hashtag_msg_ids = hashtag_msg_ids + ',' + str(message_reply.message_id)
                    #     user_settings.set(str(chat_id), str(hashtag_incoming), hashtag_msg_ids+ '\n')
                    # settings_fp = open(path_settings_file, 'w')
                    # user_settings.write(settings_fp)
                    # settings_fp.close()
                except Exception as e:
                    logging.info(e)

            # msg_id = message.message_id
            # for i in range(1,10):
            #     bot.forward_message(chat_id,chat_id,msg_id -2,disable_notification=True)
    else:
        bot.send_message(chat_id=chat_id,
                         text="Incorrect link! Give me a link to video hosting.")
        logging.info('Incorrect link! ' + link)

if __name__ == '__main__':
    # Избавляемся от спама в логах от библиотеки requests
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    # Настраиваем наш логгер
    logging.basicConfig(format='[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s',
                        level=logging.INFO,
                        filename='bot_log.log',
                        datefmt='%d.%m.%Y %H:%M:%S')
    while True:
        try:
            bot.polling()
        except Exception as e:
            print('Telegram API connection failed!')
            sleep(30)
            logging.error(e)
            return
