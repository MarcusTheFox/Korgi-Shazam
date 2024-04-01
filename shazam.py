from tkinter import filedialog, messagebox, ttk
from tkinter import *
from PIL import Image, ImageTk
import requests, os, time, threading
import json
from pydub import AudioSegment
import pyaudio
#import ffmpeg
import wave
import webbrowser



def Start():
    START_frame.place_forget()
    METHOD_frame.place(x = 0, y = 0)

def To_Music():
    METHOD_frame.place_forget()
    MICRO_frame.place_forget()
    REC_frame.place_forget()
    MUSIC_frame.place(x=0, y=0)

def File_Browse():
    audio_file = filedialog.askopenfilename(filetypes = (('MP3 files', '*.mp3'), ('WAV files', '*.wav')))
    if audio_file:
        song_full = AudioSegment.from_file(audio_file)
        song_cuted = song_full[:20000] 
        song_cuted.export("temporary_song.mp3", format="mp3")
                
        Searching_in_API()

        To_Music()

def Record_Micro():
    METHOD_frame.place_forget()
    MICRO_frame.place(x=0, y=0)

def Back_to_Method():

    try:
        os.remove('temporary_song.mp3')
        os.remove('track_image.jpg')
    except FileNotFoundError: None

    music_info.configure(state = 'normal')
    label_recording.configure(text = 'Идет запись...')

    not_found_frame.place_forget()
    REC_frame.place_forget()
    MICRO_frame.place_forget()
    MUSIC_frame.place_forget()
    METHOD_frame.place(x=0, y=0)

def No_Text():
    messagebox.showerror(title="Ошибка", message="У этого трека нет текста")
    return

def Start_Record():        

    def Recording():
        global FORMAT, CHANNELS, RATE, CHUNK, RECORD_SECONDS, WAVE_OUTPUT_FILENAME
        audio = pyaudio.PyAudio()  

        # start Recording
        stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)                     

        frames = []  

        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):  
            data = stream.read(CHUNK)                         
            frames.append(data)                                 

        # stop Recording
        stream.stop_stream()                                    
        stream.close()                                          
        audio.terminate()       

        # Closing all open files                                                     
        waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')        
        waveFile.setnchannels(CHANNELS)                         
        waveFile.setsampwidth(audio.get_sample_size(FORMAT))    
        waveFile.setframerate(RATE)                             
        waveFile.writeframes(b''.join(frames))                  
        waveFile.close()

    def Recording_bar(n):
        x = time.time()
        progress['value'] = 0
        while progress['value'] < 100:        
            if time.time() - x > n:
                x = time.time()
                progress['value'] += n*5
                REC_frame.update_idletasks()
                print(progress['value'])                
    
    MICRO_frame.place_forget()
    REC_frame.place(x=0, y=0)

    recording_thread = threading.Thread(target=Recording)

    recording_thread.start()
    Recording_bar(0.5)
    while threading.active_count() > 1:
        time.sleep(1)
    recording_thread.join()
    label_recording.configure(text = 'Ищу ваш трэк...')
    Searching_in_API()  
    

def Searching_in_API():
    
    data = {
        'return': 'timecode,lyrics,apple_music,deezer,spotify',
        'api_token': '6bf83be2ab7eb008ea786deb8e605e32'
    }
    result = requests.post('https://api.audd.io/', data=data, files={'file': open('temporary_song.mp3', 'rb')})

    data = json.loads(result.text)

    def Music_Text():
        try:
            lyrics_a = data['result']['lyrics']['lyrics']    
        except KeyError:
            No_Text()
            return
            
        else:

            if len(lyrics_a) <40:   ##Not good, not bad
                No_Text()
                return

            else:
                
                Text_Window = Toplevel(window)
                Text_Window.title('Track text')
                Text_Window.resizable(False, False)
                Text_Window.focus()

                music_text = Text(Text_Window, width = 60, height = 40,\
                    font = ('System'))
                music_text.place(x = 0, y = 0)
                Text_Window.geometry(f'{music_text.winfo_reqwidth()}x{music_text.winfo_reqheight()}+400+20')
                music_text.configure(state = 'normal')
                music_text.delete(1.0, END)

                full_title_a = data['result']['lyrics']['full_title']
                full_title_b = full_title_a.replace(' by',' - ')
                full_title_c = full_title_b.replace('Â','').replace('â', '')

                full_lyrics_b = 'Текст песни:\n' + full_title_c + '\n\n' + lyrics_a + '\n' 
                print(full_lyrics_b)

                music_text.insert(1.0, full_lyrics_b)
                music_text.tag_add('text', 1.0, END)
                music_text.tag_config('text', font = ('System'), justify = CENTER)
                music_text.configure(state = 'disabled')

    def Apple_Music():
        try:
            url = data['result']['apple_music']['url']
        except KeyError:
            messagebox.showerror(title="Ошибка", message="Отсутствует на Apple Music")
        else:
            url = data['result']['apple_music']['url']
            webbrowser.open_new_tab(url)

    def Deezer():
        try:
            url = data['result']['deezer']['link']
        except KeyError:
            messagebox.showerror(title="Ошибка", message="Отсутствует на Deezer")
        else:
            url = data['result']['deezer']['link']
            webbrowser.open_new_tab(url)

    deezer = Button(MUSIC_frame, text = 'Deezer',\
        font = ('System'), width = 19, command = Deezer)                                
    deezer.place(x = 38, y = 540) 

    apple_music = Button(MUSIC_frame, text = 'Apple Music',
        font = ('System'), width = 19, command = Apple_Music)                            
    apple_music.place(x = deezer.winfo_reqwidth()+int(deezer.place_info()['x'])+7, y = 540)

    btn_music_text = Button(MUSIC_frame, text = 'Текст песни',\
        font = ('System'), width = 20, height = 2, command = Music_Text)                            
    btn_music_text.place(x = 500, y = 540)

    try:
        file_found_status = data['result']
    except KeyError:
        file_found_status = None

    if file_found_status == None:
        Music_Not_Found()
    else:
        music_info.tag_delete('text')
        music_info.delete(1.0, END)

        artist = (data['result']['artist'])
        name = (data['result']['title'])
        try:
            album = (data['result']['album'])
        except KeyError:
            album = '----'
        try:
            release = (data['result']['release_date'])
        except KeyError:
            release = '----'
        try:
            audio_label = (data['result']['label'])
        except KeyError:
            audio_label = '----'
        text = f'Автор:\n{artist}\n\nНазвание:\n{name}\n\nАльбом:\n{album}\
\n\nДата релиза\n{release}\n\nЛейбл звукозаписи:\n{audio_label}'
        music_info.insert(1.0, text)

        music_info.tag_add('text', '1.0', END)
        music_info.tag_config('text', font = ('System' , 10), justify = CENTER)
        music_info.configure(state = 'disabled')

        try:
            url_image = data['result']['deezer']['album']['cover_medium']                           ##
        except KeyError:
            label_track = Label(MUSIC_frame, text = 'No image', font = ('System' , 20), justify = CENTER)                         #   Создает область Label, в которое вставляется скачанная картинка
            label_track.place(x = 75, y = 20) 
            To_Music()
            return

        global music_image
        music_image = requests.get(url_image)                                       #   Получаем картинку из интернета по ее ссылке
        with open('track_image.jpg', 'wb') as file:                                 #   <\ Картинка загружается на компьютер
            file.write(music_image.content)                                         #   </
        
        music_image = Image.open('track_image.jpg').resize((250, 250))              #   <\ Открывается скачаная картинка и сжимается до размеров 250х250
        music_image = ImageTk.PhotoImage(music_image)                               #   </
        label_track = Label(MUSIC_frame, image=music_image)                         #   Создает область Label, в которое вставляется скачанная картинка
        label_track.place(x = 75, y = 20)                                           #   Размещает кнопку на координатах x и y
        To_Music()

def Music_Not_Found():
    REC_frame.place_forget()
    METHOD_frame.place_forget()
    not_found_frame.place(x=0, y=0)

########################################################
##                                                    ##
##                  Create Window                     ##
##                                                    ##
########################################################

window = Tk()                                                       #
window.title('Korgi Music')                                         #
width_window, height_window = 900, 600                              #
window.geometry(f'{width_window}x{height_window}+200+50')           #
window.resizable(False, False)                                      #

########################################################
##                                                    ##
##                    Start Frame                     ##
##                                                    ##
########################################################

START_frame = Frame(window, width = width_window, height = height_window)           #
START_frame.place(x = 0, y = 0)                                                     #

start_bg_image = Image.open('ui_1.png').resize((width_window, height_window))       #
start_bg_image = ImageTk.PhotoImage(start_bg_image)                                 #
label = Label(START_frame, image=start_bg_image)                                    #
label.place(x = -2, y = -2)                                                         #

btn_start = Button(START_frame, text = 'Начать', \
    font = ('System', 45), command = Start)                             #
btn_start.place(x = 50, y = 230)                                        #

#######################################################
##                                                   ##
##             Method Selection Frame                ##
##                                                   ##
#######################################################

METHOD_frame = Frame(window, width = width_window, height = height_window)          #

method_bg_image = Image.open('ui_2.png').resize((width_window, height_window))      #
method_bg_image = ImageTk.PhotoImage(method_bg_image)                               #
label_frame2 = Label(METHOD_frame, image=method_bg_image)                           #
label_frame2.place(x = -2, y = -2)                                                  #

btn_micro = Button(METHOD_frame, text = 'Микрофон', width = 10,\
    font = ('System', 30), command = Record_Micro)                          #
btn_micro.place(x = 50, y = 200)                                            #

btn_file = Button(METHOD_frame, text = 'Файл', width = 10,\
    font = ('System', 30), command = File_Browse)                           #
btn_file.place(x = 50, y = 300)                                             #

########################################################
##                                                    ##
##                    Micro Frame                     ##
##                                                    ##
########################################################

MICRO_frame = Frame(window, width = width_window, height = height_window)           #

micro_bg_image = Image.open('ui_2.png').resize((width_window, height_window))       #
micro_bg_image = ImageTk.PhotoImage(micro_bg_image)                                 #
label_micro = Label(MICRO_frame, image=micro_bg_image)                              #
label_micro.place(x = -2, y = -2)                                                   #

record_question = Label(MICRO_frame, width = 16, text = 'Начать запись?',\
    font = ('System', 20))                                                  #   Создает область Label, в которое вставляется текст с вопросом
record_question.place(x = 50, y = 250)                                      #   Размещает Label на координатах x и y

record_sound = Button(MICRO_frame, text = 'Да', width = 5,\
    font = ('System', 30), command = Start_Record)                              #
record_sound.place(x = 50, y = 300)                                         #

back = Button(MICRO_frame, text = 'Нет', width = 5,\
    font = ('System', 30), command = Back_to_Method)                        #   Создает кнопку с функцией Back_to_Method()
back.place(x = 194, y = 300)                                                #

#######################################################
##                                                   ##
##                   Record Frame                    ##
##                                                   ##
#######################################################

REC_frame = Frame(window, width = width_window, height = height_window)           #                                                   #

rec_bg_image = Image.open('ui_2.png').resize((width_window, height_window))       #
rec_bg_image = ImageTk.PhotoImage(rec_bg_image)                                 #
label_rec = Label(REC_frame, image=rec_bg_image)                                    #
label_rec.place(x = -2, y = -2)    

progress = ttk.Progressbar(REC_frame, length=250, mode = 'determinate')
progress.place(x=50, y=500)

label_recording = Label(REC_frame, text = 'Идет запись...', font = ('System', 20))
label_recording.place(x=50, y=400)

#######################################################
##                                                   ##
##                    Music Frame                    ##
##                                                   ##
#######################################################

MUSIC_frame = Frame(window, width = width_window, height = height_window)           #   Создается пространство Frame с размерами окна

music_bg_image = Image.open('ui_3.png').resize((width_window, height_window))       #   <\ Открывается наша картинка и сжимается до размеров окна
music_bg_image = ImageTk.PhotoImage(music_bg_image)                                 #   </
label_music = Label(MUSIC_frame, image=music_bg_image)                              #   Создает область Label, в которое вставляется наша картинка
label_music.place(x = -2, y = -2)                                                   #   Размещает Label на координатах x и y

music_info = Text(MUSIC_frame, font = ('System'), width = 41, height = 15, wrap = WORD)
music_info.place(x = 36, y = 280)
music_info.tag_add('text', '1.0', END)

btn_back = Button(MUSIC_frame, width = 20, height = 2, text = 'Найти другой трек',\
     font = ('System'), command = Back_to_Method)                          
btn_back.place(x = 690, y = 540)      

##########################################################
###                                                    ###
###                   Музыка не найдена                ###
###                                                    ###
##########################################################

not_found_frame = Frame(window, width = width_window, height = height_window)

nf_image = Image.open('ui_4.png').resize((width_window, height_window))      
nf_image = ImageTk.PhotoImage(nf_image)
nf_label = Label(not_found_frame, image=nf_image)
nf_label.place(x = -2, y = -2)

nf_btn_back = Button(not_found_frame, text = 'Найти другой трек',\
     font = ('System', 20), command = Back_to_Method)                            
nf_btn_back.place(x = 580, y = 250)

#######################################################

###                                                 ###
##                                                   ##
#               Распознование музыки                  #
##                                                   ##
###                                                 ###

## Record
FORMAT = pyaudio.paInt16         
CHANNELS = 1                
RATE = 44100                ## Audio parameters
CHUNK = 1024                
RECORD_SECONDS = 20         
WAVE_OUTPUT_FILENAME = "temporary_song.mp3"  ## File name 


#######################################################
window.mainloop()
try:
    os.remove('temporary_song.mp3')         # удаляет не наши файлы
    os.remove('track_image.jpg')
except FileNotFoundError: None