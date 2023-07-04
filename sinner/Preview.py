import customtkinter as ctk

from PIL import Image, ImageTk
from customtkinter import CTkLabel

from sinner.core import Core
from sinner.handlers.frame.BaseFrameHandler import BaseFrameHandler
from sinner.typing import Frame
from sinner.utilities import is_image, is_video


class Preview:

    def __init__(self, core: Core):
        self.core = core

    def show(self):
        root = ctk.CTk()
        root.title('Preview')
        root.protocol('WM_DELETE_WINDOW', lambda: self.destroy())
        root.configure()
        root.resizable(width=True, height=True)

        preview_label = ctk.CTkLabel(root, text='preview')
        preview_label.pack(fill='both', expand=True)
        preview_slider = ctk.CTkSlider(root, to=0, command=lambda frame_value: self.update_preview(preview_label, frame_value))
        if is_image(self.core.params.target_path):
            preview_slider.pack_forget()
        if is_video(self.core.params.target_path):
            video_frame_total = BaseFrameHandler.create(handler_name=self.core.params.frame_handler, target_path=self.core.params.target_path).fc
            preview_slider.configure(to=video_frame_total)
            preview_slider.pack(fill='x')
            preview_slider.set(0)

    @staticmethod
    def render_image_preview(frame: Frame) -> ImageTk.PhotoImage:
        image = Image.fromarray(frame)
        return ImageTk.PhotoImage(image)

    def update_preview(self, preview_label: CTkLabel, frame_number: int = 0) -> None:
        image = self.core.get_frame(frame_number)
        preview_label.configure(image=image)
        preview_label.image = image

    def destroy(self):
        pass
