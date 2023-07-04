import customtkinter as ctk
import cv2

from PIL import Image, ImageTk
from PIL.Image import Resampling
from customtkinter import CTkLabel, CTk, CTkSlider

from sinner.core import Core
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.typing import Frame
from sinner.utilities import is_image, is_video


class Preview:
    core: Core
    preview_label: CTkLabel
    preview_slider: CTkSlider

    def __init__(self, core: Core):
        self.core = core

    def show(self) -> CTk:
        root = ctk.CTk()
        root.title('Preview')
        root.protocol('WM_DELETE_WINDOW', lambda: self.destroy())
        root.configure()
        root.resizable(width=True, height=True)

        self.preview_label = CTkLabel(root, text='')
        self.preview_label.drop_target = True

        # self.preview_label.bind('<Configure>', lambda event: self.resize_image(event, self.preview_label))
        self.preview_slider = CTkSlider(root, to=0, command=lambda frame_value: self.update_preview(self.preview_label, frame_value))
        self.preview_label.bind("<Double-Button-1>", lambda event: self.update_preview(self.preview_label, int(self.preview_slider.get()), True))
        self.preview_label.bind("<Button-2>", lambda event: self.change_source(int(self.preview_slider.get())))
        self.preview_label.bind("<Button-3>", lambda event: self.change_target(int(self.preview_slider.get())))
        self.preview_label.pack(fill='both', expand=True)

        self.init_slider()

        self.update_preview(self.preview_label, int(self.preview_slider.get()))
        return root

    def init_slider(self) -> None:
        if is_image(self.core.params.target_path):
            self.preview_slider.pack_forget()
        if is_video(self.core.params.target_path):
            video_frame_total = BaseFrameHandler.create(handler_name=self.core.params.frame_handler, target_path=self.core.params.target_path).fc
            self.preview_slider.configure(to=video_frame_total)
            self.preview_slider.pack(fill='x')
            self.preview_slider.set(video_frame_total / 2)

    def change_source(self, frame_number: int = 0) -> None:
        if self.core.change_source(ctk.filedialog.askopenfilename(title='Select a source')):
            self.update_preview(self.preview_label, frame_number, True)

    def change_target(self, frame_number: int = 0) -> None:
        if self.core.change_target(ctk.filedialog.askopenfilename(title='Select a target')):
            self.update_preview(self.preview_label, frame_number, True)
            self.init_slider()

    @staticmethod
    def render_image_preview(frame: Frame) -> ImageTk.PhotoImage:
        image = Image.fromarray(frame)
        return ImageTk.PhotoImage(image)

    def update_preview(self, preview_label: CTkLabel, frame_number: int = 0, processed: bool = False) -> None:
        frame = self.core.get_frame(frame_number, processed)
        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        image = ImageTk.PhotoImage(pil_image)
        preview_label.configure(image=image)
        preview_label.image = image

    @staticmethod
    def destroy():
        quit()

    @staticmethod
    def resize_image(event, label: CTkLabel):
        # Get the new size of the label
        pil_image = ImageTk.getimage(label.image)

        original_width, original_height = pil_image.size
        target_width, target_height = (event.width, event.height)

        if original_width / original_height > target_width / target_height:
            new_width = target_width
            new_height = int(original_height * (target_width / original_width))
        else:
            new_height = target_height
            new_width = int(original_width * (target_height / original_height))

        # Resize the image to fit the label
        resized_image = pil_image.resize((new_width, new_height), Resampling.LANCZOS)
        resized_photo_image = ImageTk.PhotoImage(resized_image)
        # Update the label's image
        label.configure(image=resized_photo_image)
        label.image = resized_photo_image
