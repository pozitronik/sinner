import customtkinter as ctk
import cv2

from PIL import Image, ImageTk
from PIL.Image import Resampling
from customtkinter import CTkLabel, CTk

from sinner.core import Core
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.typing import Frame
from sinner.utilities import is_image, is_video


class Preview:
    core: Core
    preview_label: CTkLabel

    def __init__(self, core: Core):
        self.core = core

    def show(self) -> CTk:
        root = ctk.CTk()
        root.title('Preview')
        root.protocol('WM_DELETE_WINDOW', lambda: self.destroy())
        root.configure()
        root.resizable(width=True, height=True)

        self.preview_label = ctk.CTkLabel(root, text='')
        self.preview_label.pack(fill='both', expand=True)
        # self.preview_label.bind('<Configure>', lambda event: self.resize_image(event, self.preview_label))
        preview_slider = ctk.CTkSlider(root, to=0, command=lambda frame_value: self.update_preview(self.preview_label, frame_value))

        if is_image(self.core.params.target_path):
            preview_slider.pack_forget()
        if is_video(self.core.params.target_path):
            video_frame_total = BaseFrameHandler.create(handler_name=self.core.params.frame_handler, target_path=self.core.params.target_path).fc
            preview_slider.configure(to=video_frame_total)
            preview_slider.pack(fill='x')
            preview_slider.set(0)

        self.update_preview(self.preview_label)
        return root

    @staticmethod
    def render_image_preview(frame: Frame) -> ImageTk.PhotoImage:
        image = Image.fromarray(frame)
        return ImageTk.PhotoImage(image)

    def update_preview(self, preview_label: CTkLabel, frame_number: int = 0) -> None:
        frame = self.core.get_frame(frame_number)
        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        label_width = preview_label.winfo_width()
        label_height = preview_label.winfo_height()
        pil_image = pil_image.resize((label_width, label_height), Resampling.LANCZOS)
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
