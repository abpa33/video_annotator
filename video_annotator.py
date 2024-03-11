#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan  3 17:50:43 2024

@author: Constantin Grad
"""

import tkinter as tk
from tkinter import Label, Button, Checkbutton, Scrollbar, Canvas, messagebox
import cv2
from PIL import Image, ImageTk
import json
import os
import shutil
import numpy as np

class VideoAnnotator:
    def __init__(self, root):
        
        self.root = root
        self.root.title("Video Annotation Tool")
        self.root.configure(bg='#98FB98')
        

        # Initialisieren von video_capture
        self.video_capture = None

        user_home = os.path.expanduser('~')
        self.video_folder = os.path.join(user_home, 'abpa_video_data')
        
        # Überprüfen, ob der Ordner existiert und Videodateien laden
        if os.path.exists(self.video_folder):
            self.video_files = [f for f in os.listdir(self.video_folder) if f.endswith('.mp4')]
            self.current_video_index = 0
            if self.video_files:
                self.load_video()
        else:
            print("Ordner 'abpa_video_data' nicht gefunden.")

        # Scrollbar-Einstellungen
        self.scrollbar = Scrollbar(self.root)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas = Canvas(self.root, bg='#98FB98', yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.canvas.yview)

        # Frame im Canvas für Widgets
        self.frame = tk.Frame(self.canvas, bg='#98FB98')
        self.canvas.create_window((0, 0), window=self.frame, anchor='nw')

        self.video_label = Label(self.frame, text="No Video Selected")
        self.video_label.pack()

        self.select_folder_button = Button(self.frame, text="Select Folder", command=self.select_folder, bg='#32CD32', fg='black')
        self.select_folder_button.pack()

        self.canvas_video = tk.Canvas(self.frame, width=270, height=480, bg='#98FB98', highlightthickness=0)
        self.canvas_video.pack()

        # Checkboxen für das 1. Label
        self.label_options = {"geteert": tk.BooleanVar(), "gepflastert": tk.BooleanVar(),
                              "unbefestigt": tk.BooleanVar(), "unklar": tk.BooleanVar()}
        Label(self.frame, text="1. Label", bg='#98FB98').pack()
        for option, var in self.label_options.items():
            Checkbutton(self.frame, text=option, variable=var, bg='#98FB98').pack()

        # Checkboxen für das 2. Label
        self.second_label_options = {"nass": tk.BooleanVar(), "trocken": tk.BooleanVar(),
                                     "verschneit": tk.BooleanVar(), "unklar": tk.BooleanVar()}
        Label(self.frame, text="2. Label", bg='#98FB98').pack()
        for option, var in self.second_label_options.items():
            Checkbutton(self.frame, text=option, variable=var, bg='#98FB98').pack()

        # Checkboxen für das 3. Label
        self.third_label_options = {"tag": tk.BooleanVar(), "nacht": tk.BooleanVar(), "unklar": tk.BooleanVar()}
        Label(self.frame, text="3. Label", bg='#98FB98').pack()
        for option, var in self.third_label_options.items():
            Checkbutton(self.frame, text=option, variable=var, bg='#98FB98').pack()

        self.start_button = Button(self.frame, text="Start", command=self.start_video)
        self.start_button.pack()

        self.stop_button = Button(self.frame, text="Stop", command=self.stop_video)
        self.stop_button.pack()

        self.save_button = Button(self.frame, text="Save Label", command=self.save_label)
        self.save_button.pack()

        self.annotations = []
        self.video_path = ""
        self.video_capture = None
        self.current_frame_time = 0
        self.playing = False
        self.annotation_id = 0

        self.frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def select_folder(self):
        # Hartcodierter Pfad zum Ordner "abpa_video_data" im Benutzerordner
        user_home = os.path.expanduser('~')  # Erhalten des Benutzerordners
        self.video_folder = os.path.join(user_home, 'abpa_video_data')

        self.video_files = [f for f in os.listdir(self.video_folder) if f.endswith('.mp4')]
        self.current_video_index = 0
        if self.video_files:
            self.load_video()

    def load_video(self):
        if self.video_files and self.current_video_index < len(self.video_files):
            self.video_path = os.path.join(self.video_folder, self.video_files[self.current_video_index])
            if self.video_capture:
                self.video_capture.release()
            self.video_capture = cv2.VideoCapture(self.video_path, 0)
            self.playing = False

    def start_video(self):
        if self.video_capture is None or not self.video_capture.isOpened():
            self.load_video()
        if self.video_capture is not None:
            self.playing = True
            self.update_frame()
        else:
            print("Fehler: Video konnte nicht geladen werden.")

    def stop_video(self):
        self.playing = False
        self.release_video_capture()

    def rotate_frame(self, frame, angle):
        # Bestimmen des Rotationszentrums
        (h, w) = frame.shape[:2]
        center = (w // 2, h // 2)
    
        # Durchführen der Rotation
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated_frame = cv2.warpAffine(frame, M, (w, h))
    
        return rotated_frame

    def scale_and_center_frame(self, frame, canvas_width, canvas_height):
        h, w = frame.shape[:2]
        scale = min(canvas_width / w, canvas_height / h)
        new_w, new_h = int(w * scale), int(h * scale)
        frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
        # Neuen Frame mit schwarzen Rändern erstellen, um das Bild im Canvas zu zentrieren
        new_frame = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)
        x_offset = (canvas_width - new_w) // 2
        y_offset = (canvas_height - new_h) // 2
        new_frame[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = frame

        return new_frame

    def update_frame(self):
        if self.playing:
            ret, frame = self.video_capture.read()
            if ret:
                
                self.current_frame_time = self.video_capture.get(cv2.CAP_PROP_POS_MSEC)
                
                # Skalieren des Frames, um das Seitenverhältnis zu erhalten
                frame = self.scale_and_center_frame(frame, self.canvas_video.winfo_width(), self.canvas_video.winfo_height())
                
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
                
                self.canvas_video.create_image(
                    (self.canvas_video.winfo_width() - photo.width()) // 2,
                    (self.canvas_video.winfo_height() - photo.height()) // 2,
                    image=photo, anchor='nw')
                
                self.canvas_video.image = photo
                self.root.after(30, self.update_frame)
            else:
                self.playing = False

    def save_label(self):
        try:
            selected_labels = [option for option, var in self.label_options.items() if var.get()]
            label_1_str = ", ".join(selected_labels)

            selected_second_labels = [option for option, var in self.second_label_options.items() if var.get()]
            label_2_str = ", ".join(selected_second_labels)

            selected_third_labels = [option for option, var in self.third_label_options.items() if var.get()]
            label_3_str = ", ".join(selected_third_labels)
        
            video_title = os.path.basename(self.video_path)

            self.annotations.append({
            'video': video_title, 
            '1_label': label_1_str,
            '2_label': label_2_str,
            '3_label': label_3_str
            })

            self.save_to_json()

            labelled_folder = os.path.join(self.video_folder, 'labelled_data')
            if not os.path.exists(labelled_folder):
                os.makedirs(labelled_folder)
            shutil.move(self.video_path, os.path.join(labelled_folder, os.path.basename(self.video_path)))

            messagebox.showinfo("Erfolg", "Labels erfolgreich gespeichert")
        except Exception as e:
            messagebox.showerror("Fehler", "Ein Fehler ist aufgetreten: " + str(e))

        self.current_video_index += 1
        if self.current_video_index < len(self.video_files):
            self.load_video()
            self.start_video()  # Automatisches Starten des nächsten Videos
        else:
            self.canvas_video.delete("all")  # Entfernen des Videos aus dem Canvas

    def save_to_json(self):
        json_file_path = os.path.join(self.video_folder, 'annotations.json')
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as json_file:
                existing_data = json.load(json_file)
                existing_data.extend(self.annotations)
            with open(json_file_path, 'w') as json_file:
                json.dump(existing_data, json_file, indent=4)
        else:
            with open(json_file_path, 'w') as json_file:
                json.dump(self.annotations, json_file, indent=4)

        self.annotations = []

root = tk.Tk()
app = VideoAnnotator(root)
root.mainloop()


