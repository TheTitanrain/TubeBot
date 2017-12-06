# -*- coding: utf-8 -*-
import config
import telebot
from telebot import types
import botan
# from telebot import apihelper
# from os.path import join, getsize
import os
# import fnmatch
# import eventlet
# import requests
import logging
from configparser import ConfigParser
from moviepy.editor import *
from pytube import YouTube
from time import sleep
# import time
# from transliterate import translit, get_available_language_codes
import shutil
from threading import Thread
from threading import Lock
# import string
import sys

bot = telebot.TeleBot(config.token)
thread_lock = Lock()

path_home = os.path.dirname(sys.argv[0]) + '/'

usettings_ = ConfigParser()
usettings_filename_ = 'users_settings.conf'
# download_info_filename_ = 'info.inf'
path_usettings_ = path_home + usettings_filename_


def correct_link(link):
    if link.find(u'youtube.com') != -1 or link.find(u'youtu.be') != -1:
        return True
    else:
        return False


def close_clip(clip):
    try:
        clip.reader.close()
        del clip.reader
        if clip.audio != None:
            clip.audio.reader.close_proc()
            del clip.audio
        del clip
    except Exception as e:
        print(e)
        #sys.exc_clear()


class ProgressBar(Thread):
    def __init__(self, name, message, file_size, file_handle):
        Thread.__init__(self)
        self.name = name
        self.message = message
        self.file_size = file_size
        self.file_handle = file_handle
    def run(self):
        show_progress(self.message, self.file_size, self.file_handle)
        msg = "%s is running" % self.name
        print(msg)


def show_progress(message, file_size, file_handle):
    timeout = 100
    while (not os.path.exists(file_handle)) and (timeout > 0):
        sleep(0.2)
        timeout -= 1
    bytes_received = os.path.getsize(file_handle)
    file_size_mb = file_size/1024/1024
    while bytes_received < file_size:
        percent = int(100 * bytes_received / file_size)
        try:
            bot.edit_message_text(text=(('Загружаю видео на сервер %dМб, ждите ' % file_size_mb) + str(percent)+'%'),
                                  chat_id=message.chat.id,
                                  message_id=message.message_id)
            bot.send_chat_action(message.chat.id, 'record_video')
        except Exception as e:
            print (e)
        sleep(0.5)
        bytes_received = os.path.getsize(file_handle)
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
    # timeout = 100
    # while (not os.path.exists(file_handle)) and (timeout > 0):
    #     sleep(0.2)
    #     timeout -= 1
    # bytes_received = os.path.getsize(file_handle)
    # file_size_mb = file_size/1024/1024

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


class processMessage(Thread):
    def __init__(self, name, message):
        Thread.__init__(self)
        self.name = name
        self.message = message
    def run(self):
        send_podcast(self.message)
        msg = "%s is running" % self.name
        print(msg)
class ProcessCall(Thread):
    def __init__(self, name, call):
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
        if call.message:
            data = call.data
            if data[:len('bitrate=')] == 'bitrate=':
                bitrate = data[len('bitrate='):len('bitrate=') + len('123k')]
                thread_lock.acquire()
                usettings_.read(path_usettings_)
                if not usettings_.has_section(str(chat_id)):
                    usettings_.add_section(str(chat_id))
                if bitrate == '320k':
                    usettings_.set(str(chat_id), 'bitrate', '320k')
                    # bot.send_message(chat_id=chat_id, text="Качество звука: 320Кбит/с - *наилучшее*",parse_mode='Markdown')
                    bot.answer_callback_query(call.id,
                                              text="Качество звука: 320Кбит/с - наилучшее\nДлина файла: 20мин",
                                              show_alert=True)
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                elif bitrate == '192k':
                    usettings_.set(str(chat_id), 'bitrate', '192k')
                    # bot.send_message(chat_id=chat_id, text="Качество звука: 192Кбит/с - *хорошее*",parse_mode='Markdown')
                    bot.answer_callback_query(call.id,
                                              text="Качество звука: 192Кбит/с - хорошее\nДлина файла: 30мин",
                                              show_alert=True)
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                elif bitrate == '128k':
                    usettings_.set(str(chat_id), 'bitrate', '128k')
                    # bot.send_message(chat_id=chat_id, text="Качество звука: 128Кбит/с - *приемлимое*",parse_mode='Markdown')
                    bot.answer_callback_query(call.id,
                                              text="Качество звука: 128Кбит/с - приемлимое\nДлина файла: 40мин",
                                              show_alert=True)
                    bot.delete_message(call.message.chat.id, call.message.message_id)
                elif bitrate == '096k':
                    usettings_.set(str(chat_id), 'bitrate', '96k')
                    # bot.send_message(chat_id=chat_id, text="Качество звука: 96Кбит/с - *низкое*",parse_mode='Markdown')
                    bot.answer_callback_query(call.id,
                                              text="Качество звука: 96Кбит/с - низкое\nДлина файла: 50мин",
                                              show_alert=True)
                    bot.delete_message(call.message.chat.id, call.message.message_id)
               # bot.answer_callback_query(call.id,text = "Качество звука: 96Кбит/с - *низкое*")
                usf = open(str(path_home + usettings_filename_), 'w')
                usettings_.write(usf)
                usf.close()
                thread_lock.release()
            elif data[:len('c_type=')] == 'c_type=':
                c_type = data[len('c_type='):]
                thread_lock.acquire()
                usettings_.read(path_usettings_)
                usettings_.set(str(chat_id), 'c_type', c_type)
                usf = open(str(path_home + usettings_filename_), 'w')
                usettings_.write(usf)
                usf.close()
                thread_lock.release()
                bot.delete_message(call.message.chat.id, call.message.message_id)
                bot.answer_callback_query(call.id)
            elif data[:len('get_video=')] == 'get_video=':
                new_status = data[len('get_video='):]
                thread_lock.acquire()
                usettings_.read(path_usettings_)
                usettings_.set(str(chat_id), 'get_video', str(new_status))
                usf = open(str(path_home + usettings_filename_), 'w')
                usettings_.write(usf)
                usf.close()
                thread_lock.release()
                bot.delete_message(call.message.chat.id, call.message.message_id)
                if new_status == 'True':
                    bot.answer_callback_query(call.id, text="Загрузка видео + аудио",show_alert=True)
                else:
                    bot.answer_callback_query(call.id, text="Загрузка только аудио", show_alert=True)
            # elif data[:len('download_video=')] == 'download_video=':
            #     link = data[len('download_video='):]
            #     video_title = YouTube(link).streams.get_by_itag(18).player_config['args']['title']
            #     if link.find(u'youtu.be') != -1:
            #         tmpdir = link[link.find('be') + 3:]
            #     elif link.find('v=') != -1:
            #         tmpdir = link[link.find('v=') + 2:]
            #     elif link.find('embed') != -1:
            #         tmpdir = link[link.find('embed') + 6:]
            #     for c in ['&', '?', '=']:
            #         if tmpdir.find(c) != -1:
            #             tmpdir = tmpdir[:tmpdir.find(c)]
            #     asciiFileName = tmpdir + ".mp4"
            #     tmpdir = 'd' + tmpdir + str(call.message.chat.id) + str(call.message.message_id)
            #     path_file = path_home + tmpdir + '/' + asciiFileName
            #     if not os.path.exists(tmpdir):
            #         os.mkdir(tmpdir)
            #     YouTube(link).streams.get_by_itag(18).download(output_path=str(path_home + tmpdir),filename=(asciiFileName[:-4]))
            #     fv = open(str(path_file),'rb')
            #     msg = bot.send_video(call.message.chat.id, fv,caption = video_title)
            #     fv.close()
            #     bot.delete_message(call.message.chat.id, call.message.message_id)
            #     bot.answer_callback_query(call.id)
            #     if os.path.exists(tmpdir):
            #         shutil.rmtree(tmpdir)
    except Exception as e:
        logging.error(str('callback_button:') + str(e))
        thread_lock.release()


@bot.message_handler(commands=['video'])
def set_video_download_flag(message):
    try:
        chat_id = message.chat.id
        thread_lock.acquire()
        usettings_.read(path_home + usettings_filename_)
        if not usettings_.has_section(str(chat_id)):
            usettings_.add_section(str(chat_id))
            usettings_.set(str(chat_id),'bitrate','192k')
            usettings_.set(str(chat_id), 'get_video', 'False')
            usf = open(str(path_home + usettings_filename_), 'w')
            usettings_.write(usf)
            usf.close()
        if not usettings_.has_option(str(chat_id), 'get_video'):
            usettings_.set(str(chat_id), 'get_video', 'False')
        thread_lock.release()
        us_get_video = usettings_.get(str(chat_id),'get_video')
        keyboard = types.InlineKeyboardMarkup()
        if us_get_video == 'True':
            get_video_button = types.InlineKeyboardButton(text="Отключить", callback_data=('get_video=False'))
            text_get_video = u'Загрузка видео (до 50Мб): *Включена*'
        else:
            get_video_button = types.InlineKeyboardButton(text="Включить", callback_data=('get_video=True'))
            text_get_video = u'Загрузка видео (до 50Мб): *Отключена*'
        keyboard.add(get_video_button)
        bot.send_message(message.chat.id,parse_mode='Markdown',text = text_get_video ,reply_markup=keyboard)
    except Exception as e:
        logging.error(str('set_video_download_flag:') + str(e))
        thread_lock.release()


@bot.message_handler(commands=['bitrate'])
def set_sound_quality(message):
    try:
        chat_id = message.chat.id
        if not config.DEBUG_:
            botan.track(config.botan_key, message.chat.id, message, 'bitrate')
        thread_lock.acquire()
        usettings_.read(path_home + usettings_filename_)
        if not usettings_.has_section(str(chat_id)):
            usettings_.add_section(str(chat_id))
            usettings_.set(str(chat_id),'bitrate','192k')
            usf = open(str(path_home + usettings_filename_), 'w')
            usettings_.write(usf)
            usf.close()
        thread_lock.release()
        us_bitrate = usettings_.get(str(chat_id),'bitrate')
        keyboard = types.InlineKeyboardMarkup()
        button_320k = types.InlineKeyboardButton(text="320Кбит/с",callback_data=('bitrate=320k'))
        button_192k = types.InlineKeyboardButton(text="192Кбит/с",callback_data=('bitrate=192k'),)
        button_128k = types.InlineKeyboardButton(text="128Кбит/с", callback_data=('bitrate=128k'))
        button_096k = types.InlineKeyboardButton(text="96Кбит/с", callback_data=('bitrate=096k'))
        keyboard.add(button_096k,button_128k,button_192k,button_320k)
        if us_bitrate == '320k':
            text_bitrate = u'*320Кбит/с*'
        elif us_bitrate == '192k':
            text_bitrate = u'*192Кбит/с*'
        elif us_bitrate == '128k':
            text_bitrate = u'*128Кбит/с*'
        elif us_bitrate == '96k':
            text_bitrate = u'*96Кбит/с*'
        bot.send_message(message.chat.id,parse_mode='Markdown',text = (u'Битрейт аудио по умолчанию: ' + text_bitrate) ,reply_markup=keyboard)
    except Exception as e:
        logging.error(str('set_sound_quality:') + str(e))
        thread_lock.release()


@bot.message_handler(commands=['start'])
def send_startup_message(message):
    try:
        chat_id = message.chat.id
        thread_lock.acquire()
        usettings_.read(path_home + usettings_filename_)
        if not usettings_.has_section(str(chat_id)):
            usettings_.add_section(str(chat_id))
            usettings_.set(str(chat_id), 'bitrate', '192k')

            usf = open(str(path_home + usettings_filename_), 'w')
            usettings_.write(usf)
            usf.close()
        thread_lock.release()
        bot.send_message(chat_id,
                         text='Привет! Отправь мне ссылку на ролик YouTube,\nнапример эту https://youtu.be/9bZkp7q19f0 ',
                         parse_mode='Markdown',
                         disable_web_page_preview=True)
    except Exception as e:
        logging.error(str('send_startup_message:') + str(e))
        thread_lock.release()
# @bot.message_handler(commands=['playlist'])
# def move_to_playlist(message):
#     keyboard = types.InlineKeyboardMarkup()
#     button_donat = types.InlineKeyboardButton(text="Музыка",url='https://t.me/joinchat/AAAAAE8-5q17REFmmfVBcQ')
#     keyboard.add(button_donat)
#     bot.send_message(message.chat.id, text = 'Ваши плейлисты:',reply_markup=keyboard,parse_mode='Markdown', disable_web_page_preview=True)


@bot.message_handler(content_types=["text"])
def create_threads(message):
    name = "Thread #%s" % (message.message_id)
    my_thread = processMessage(name,message)
    my_thread.start()


def send_podcast(message):  # Название функции не играет никакой роли, в принципе
    link = message.text
    logging.info('{!s}'.format(str(message.chat.id) + ' ' + link))
    chat_id = message.chat.id
    #read settings
    try:
        thread_lock.acquire()
        usettings_.read(path_home + usettings_filename_)
        if not usettings_.has_section(str(chat_id)):
            usettings_.add_section(str(chat_id))
            usettings_.set(str(chat_id), 'bitrate', '192k')
            usettings_.set(str(chat_id), 'get_video', 'False')
            usf = open(str(path_home + usettings_filename_), 'w')
            usettings_.write(usf)
            usf.close()
        if not usettings_.has_option(str(chat_id), 'get_video'):
            usettings_.set(str(chat_id), 'get_video', 'False')
        if not usettings_.has_option(str(chat_id), 'bitrate'):
            usettings_.set(str(chat_id), 'bitrate', '192k')
        thread_lock.release()
    except Exception as e:
        logging.error(str('send_podcast:') + str(e))
        thread_lock.release()
    us_bitrate = usettings_.get(str(chat_id), 'bitrate')
    us_get_video = usettings_.get(str(chat_id), 'get_video')
    #read settings end
    if not config.DEBUG_:
        botan.track(config.botan_key, message.chat.id, message, 'convert')
    if correct_link(link):
        if link.find(u'youtu.be') != -1:
            tmpdir = link[link.find('be') + 3:]
        elif link.find('v=') != -1:
            tmpdir = link[link.find('v=') + 2:]
        elif link.find('embed') != -1:
            tmpdir = link[link.find('embed') + 6:]
        if tmpdir.find('?t=') != -1:
            cut_start = tmpdir[tmpdir.find('?t=') + 3:]
            cut_start = cut_start[:cut_start.find('s')]
            cut_start = int(cut_start)
        elif tmpdir.find('&t=') != -1:
            cut_start = tmpdir[tmpdir.find('&t=') + 3:]
            cut_start = cut_start[:cut_start.find('s')]
            cut_start = int(cut_start)
        else:
            cut_start = 0
        for c in ['&', '?', '=']:
            if tmpdir.find(c) != -1:
                tmpdir = tmpdir[:tmpdir.find(c)]

        tmpdir = tmpdir + str(message.chat.id) + str(message.message_id)

        if not os.path.exists(tmpdir):
            os.mkdir(tmpdir)
            #os.chdir(tmpdir)
        try:
            msg_wait = bot.send_message(chat_id,
                                        "Получаю информацию о видео...",
                                        reply_to_message_id=message.message_id)
            yt = YouTube(link)
            video_title = yt.streams.get_by_itag(18).player_config['args']['title']
            video_filesize = yt.streams.get_by_itag(18).filesize
            #logging.info('{!s}'.format(video_title))
            # keyboard = types.InlineKeyboardMarkup()
            # button_360p = types.InlineKeyboardButton(text="Загрузить видео", callback_data=("download_video=" + link))
            # button_720p = types.InlineKeyboardButton(text="720p", callback_data=(link + "720p"))
            # keyboard.add(button_360p)
            # bot.send_message(chat_id, text=link,reply_markup=keyboard,disable_web_page_preview = True)
            #msg_donat = bot.send_message(chat_id, "Нравится бот? Поддержи разработку: http://yasobe.ru/na/teslamodelsx")
            msg_wait = bot.edit_message_text(chat_id=chat_id,
                                             message_id=msg_wait.message_id,
                                             text="Загружаю видео на сервер, ждите...")
            # download_info = SafeConfigParser()
            # download_info.add_section('Main')
            # download_info.set('Main', 'chat_id', str(msg_wait.chat.id))
            # download_info.set('Main', 'message_id', str(msg_wait.message_id))
            # millis = int(round(time.time() * 1000))
            # download_info.set('Main', 'time', str(millis))
            # fvi = open(str(path_home + tmpdir + '/' + asciiFileName[:-4] + '.inf'), 'w')
            # download_info.write(fvi)
            # fvi.close()
            asciiFileName = tmpdir + '.mp4'
            path_file = path_home + tmpdir + '/' + asciiFileName
            download_progress = ProgressBar(tmpdir, msg_wait, video_filesize, path_file)
            download_progress.start()
            #YouTube(link).streams.first().download(output_path = str(path_home + tmpdir),filename = asciiFileName[:-4])

            yt.streams.get_by_itag(18).download(output_path=str(path_home + tmpdir), filename=asciiFileName)

            if us_get_video == 'True' and (video_filesize/1024/1024 <= 50):

                fv = open(str(path_file), 'rb')
                msg = bot.send_document(chat_id, fv, caption=video_title)
                fv.close()
            elif video_filesize/1024/1024 > 50:
                bot.send_message(chat_id=chat_id, text="Размер файла превышает 50МБ разрешенные для ботов...")
            # YouTube(link,on_progress_callback = on_download_progress).streams.get_by_itag(18).download(output_path = str(path_home + tmpdir),filename = asciiFileName[:-4])
            #YouTube(link).streams.get_by_itag(140).download(output_path = str(path_home + tmpdir),filename = asciiFileName[:-4])
        except Exception as e:
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=msg_wait.message_id,
                                  text="Не удалось получить информацию о видео из-за ошибки:" + str(e))
            logging.error(e)
            os.chdir(path_home)
            if os.path.exists(tmpdir):
                shutil.rmtree(tmpdir)
            return

        clip = VideoFileClip(path_file)
        audio = clip.audio
        duration = int(clip.duration)
        if cut_start < duration:
            audio = audio.subclip(cut_start, duration)
            duration = audio.duration
            bot.send_chat_action(chat_id, 'record_audio')
            #approx for 96kb
            sec_per_mb = 100
            if us_bitrate == '320k':
                max_pduration = 1200
                bot.edit_message_text(chat_id=chat_id, message_id=msg_wait.message_id, text='Конвертирую аудио 320Кбит/с, ждите...')
            elif us_bitrate == '192k':
                max_pduration = 1800
                bot.edit_message_text(chat_id=chat_id, message_id=msg_wait.message_id,text='Конвертирую аудио 192Кбит/с, ждите...')
            elif us_bitrate == '128k':
                max_pduration = 2400
                bot.edit_message_text(chat_id=chat_id, message_id=msg_wait.message_id,text='Конвертирую аудио 128Кбит/с, ждите...')
            elif us_bitrate == '96k':
                max_pduration = 3000
                bot.edit_message_text(chat_id=chat_id, message_id=msg_wait.message_id,text='Конвертирую аудио 96Кбит/с, ждите...')
            else:
                max_pduration = 1800
            sec_per_mb = max_pduration / 30
            parts = 1 + int(duration/max_pduration)
            path_file_mp3 = path_file[:-4] + '.mp3'
            print(duration, parts)
            for pn in range(parts):
                if ((pn + 1)* max_pduration > duration):
                    pduration = duration - pn * max_pduration
                    piece = audio.subclip(pn * max_pduration, duration)
                else:
                    piece = audio.subclip(pn * max_pduration, (pn + 1)* max_pduration)
                    pduration = max_pduration
                if (parts > 1):
                    piece.write_audiofile(path_file[:-4]+'_'+str(pn+1) + '_of_' + str(parts) +'.mp3',
                                          bitrate=us_bitrate)
                    f = open(str(path_file[:-4]+'_'+str(pn+1)+ '_of_' + str(parts) +'.mp3'), 'rb')
                    msg = bot.send_audio(message.chat.id,
                                         f,
                                         title=video_title + '_' +str(pn+1) + '/' + str(parts),
                                         duration=pduration)
                else:
                    encode_progress = ProgressAudio(tmpdir, msg_wait, int(pduration / sec_per_mb), path_file_mp3)
                    encode_progress.start()
                    piece.write_audiofile(path_file_mp3, bitrate=us_bitrate)
                    encode_progress.enable = False
                    f = open(path_file_mp3, 'rb')
                    msg = bot.send_audio(message.chat.id,
                                         f,
                                         title=video_title,
                                         duration = pduration)

                f.close()
            #fv = open(str(path_file),'rb')
            #msg = bot.send_video(message.chat.id, fv,duration = pduration,caption = video_title)
            #fv.close()
            try:
                thread_lock.acquire()
                usettings_.read(path_usettings_)
                if not usettings_.has_section(str(chat_id)):
                    usettings_.add_section(str(chat_id))
                if not usettings_.has_option(str(chat_id), 'c_type'):
                    usettings_.set(str(chat_id), 'c_type', 'None')
                if not usettings_.has_option(str(chat_id), 'ad_flag'):
                    usettings_.set(str(chat_id), 'ad_flag', 'False')
                if not usettings_.has_option(str(chat_id), 'get_video'):
                    usettings_.set(str(chat_id), 'get_video', 'False')
                if usettings_.get(str(chat_id), 'ad_flag') != 'True':
                    usettings_.set(str(chat_id), 'ad_flag', 'True')
                    keyboard = types.InlineKeyboardMarkup()
                    button_donat = types.InlineKeyboardButton(text="Разработчику на пиво",
                                                              url='https://money.yandex.ru/to/410013085648958')
                    keyboard.add(button_donat)
                    ad_str = u'#Нововведение\n'
                    ad_str += u'Теперь Вы можете сохранять небольшие видео!\n\n'
                    ad_str += u'*Вкл/выкл* - команда /video\n\n'
                    ad_str += u'Пример использования - видео на личном канале разработчика:\n'
                    ad_str += u't.me/junkie\_story/89\n\n'
                    ad_str += u'Пишите свои идеи и вопросы - нам нужна обратная связь:\n'
                    ad_str += u't.me/joinchat/AtybDREscMNUJE36ffYGoA  '
                    bot.send_message(msg_wait.chat.id,
                                     text=ad_str,
                                     reply_markup=keyboard,
                                     parse_mode='Markdown',
                                     disable_web_page_preview=True)
                elif usettings_.get(str(chat_id), 'c_type') == 'None':
                    keyboard = types.InlineKeyboardMarkup()
                    button_music = types.InlineKeyboardButton(text="Музыка",
                                                              callback_data='c_type=Music')
                    button_podcast = types.InlineKeyboardButton(text="Речь: Новости, Интервью...",
                                                                callback_data='c_type=Podcast')
                    keyboard.add(button_music, button_podcast)
                    bot.send_message(msg_wait.chat.id,
                                     text="Что в основном качаете? Ваш ответ важен.",
                                     reply_markup=keyboard,
                                     parse_mode='Markdown',
                                     disable_web_page_preview=True)
                usf = open(str(path_home + usettings_filename_), 'w')
                usettings_.write(usf)
                usf.close()
                thread_lock.release()
            except Exception as e:
                logging.error(str('send_podcast:') + str(e))
                thread_lock.release()
            # message = bot.send_message(chat_id, text=link,reply_markup=keyboard,disable_web_page_preview = True)
            bot.delete_message(msg_wait.chat.id, msg_wait.message_id)

            # bot.delete_message(msg_donat.chat.id, msg_donat.message_id)
        else:
            bot.edit_message_text(chat_id=chat_id,
                                  message_id=msg_wait.message_id,
                                  text='Таймкод начала превышает длительность видео')
        os.chdir(path_home)
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)
        close_clip(clip)


if __name__ == '__main__':
    # Избавляемся от спама в логах от библиотеки requests
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    # Настраиваем наш логгер
    logging.basicConfig(format='[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s',
                        level=logging.INFO,
                        filename='bot_log.log',
                        datefmt='%d.%m.%Y %H:%M:%S')
    bot.polling(none_stop=True)
