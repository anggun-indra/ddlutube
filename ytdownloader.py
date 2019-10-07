from pytube import YouTube
from multi_rake import Rake
import os
import moviepy.editor as mp
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pprint
import time
import json
import os

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('mmwml-340228cf2d6b.json', scope)
client = gspread.authorize(creds)

sheet = client.open('51D4Q DAFTAR DOWNLOAD & KONVERSI CONTENT PENGAJIAN').sheet1

pp = pprint.PrettyPrinter()

ddnkcp = sheet.get_all_records(head=2)

gauth = GoogleAuth()
gauth.LocalWebserverAuth()  # Creates local webserver and auto handles authentication.

drive = GoogleDrive(gauth)

pp.pprint(ddnkcp)
i = 3


# on_progress_callback takes 4 parameters.
def progress_check(stream=None, chunk=None, file_handle=None, remaining=None):
    # Gets the percentage of the file that has been downloaded.
    percent = (100 * (file_size - remaining)) / file_size
    print("{:00.0f}% downloaded".format(percent), end="\r")


# Grabs the file path for Download
def file_path():
    home = os.path.expanduser('~')
    download_path = os.path.join(home, 'Downloads')
    return download_path


def start(y_url, gsheet, row):
    print("Your video will be saved to: {}".format(file_path()))
    # Input
    yt_url = y_url
    print(yt_url)
    print("Accessing YouTube URL...")

    # Searches for the video and sets up the callback to run the progress indicator.
    try:
        video = YouTube(yt_url, on_progress_callback=progress_check)
    except:
        print("ERROR. Check your:\n  -connection\n  -url is a YouTube url\n\nTry again.")
        redo = start()

    # Get the first video type - usually the best quality.
    video_type = video.streams.filter(progressive=True, subtype="mp4").first()

    # Gets the title of the video
    title = video_type.title
    _, vid_id = yt_url.split('?v=')
    thumbnail = 'https://i.ytimg.com/vi/' + vid_id + '/maxresdefault.jpg'
    # pp.pprint(thumbnail)

    valvid = video_type.__dict__

    # Prepares the file for download
    # pp.pprint(video.__dict__)
    print("Description: {}".format(video.description))
    print("Fetching: {}...".format(title))
    print("Thumbnail: {}".format(thumbnail))

    rake = Rake(
        min_chars=3,
        max_words=3,
        min_freq=1,
        language_code='id',  # 'en'
        stopwords=None,  # {'and', 'of'}
        lang_detect_threshold=50,
        max_words_unknown_lang=2,
        generated_stopwords_percentile=80,
        generated_stopwords_max_len=3,
        generated_stopwords_min_freq=2,
    )

    keywords = rake.apply(video.description)

    print(keywords)
    global file_size
    file_size = video_type.filesize
    # Starts the download process
    file = video_type.download(file_path())
    print(file)
    clip = mp.VideoFileClip(file)
    mp3file = file.replace('.mp4', '.mp3').replace('.MP4', '.mp3')
    clip.audio.write_audiofile(mp3file)
    clip.close()
    #

    gdrive_file_name = mp3file.replace(file_path(), '').replace('\\', '')

    file1 = drive.CreateFile({'title': gdrive_file_name, 'mimeType': 'audio/mpeg',
                              "parents": [{"kind": "drive#fileLink", "id": '17XUvYr6vgRSX_3wASGP_tEJJrPXNz3pJ'}]})

    file1.SetContentFile(mp3file)  # Set content of the file from given string.
    file1.Upload()

    file1.InsertPermission({
        'type': 'anyone',
        'value': 'anyone',
        'role': 'reader'})

    print(file1['alternateLink'])

    file12 = drive.CreateFile({'title': gdrive_file_name.replace('mp3', 'json'), 'mimeType': 'application/json',
                               "parents": [{"kind": "drive#fileLink", "id": '17XUvYr6vgRSX_3wASGP_tEJJrPXNz3pJ'}]})

    file12.SetContentString(json.dumps(keywords))  # Set content of the file from given string.
    file12.Upload()

    file12.InsertPermission({
        'type': 'anyone',
        'value': 'anyone',
        'role': 'reader'})

    print(file12['alternateLink'])

    gsheet.update_cell(row, 10, str(file1['alternateLink']))
    gsheet.update_cell(row, 11, str(file1['alternateLink']))
    # gsheet.update_cell(row, 12, gdrive_file_name)
    gsheet.update_cell(row, 12, str(file12['alternateLink']))
    gsheet.update_cell(row, 13, video.description)
    gsheet.update_cell(row, 14, title)
    # gsheet.update_cell(row, 16, thumbnail)
    gsheet.update_cell(row, 9, thumbnail)
    gsheet.update_cell(row, 7, gdrive_file_name)

    time.sleep(1)
    os.remove(file)
    # os.remove(mp3file)

    print("Ready to download another video.\n\n")
    # start(y_url, gsheet, row)


for rw in ddnkcp:
    audioUrl = rw['Lokasi Downloaded File Audio (URL)']
    dlr = rw['DL-er']
    file_size = 0
    url = str(rw['URL'])
    if dlr == 'AG':
        print('DL-er : ' + dlr)
        print(url)
        if audioUrl.strip() != '':
            print('Video has been converted')
            print('Audio URL : ' + audioUrl)
        else:
            start(url, sheet, i)
    i += 1

# start()

# yt = YouTube('https://www.youtube.com/watch?v=FuwH74mg3tQ')

# yt.streams.all()
# yt.streams.filter(subtype='mp4', progressive=True).first().download()
