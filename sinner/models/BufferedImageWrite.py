import os
from multiprocessing import Process, Queue
from typing import List, Tuple, Optional

from sinner.helpers.FrameHelper import write_to_image
from sinner.models.NumberedFrame import NumberedFrame


class AsyncWriter(Process):
    def __init__(self, write_queue: Queue):
        super().__init__()
        self.queue = write_queue
        self.running = True

    def run(self) -> None:
        while self.running:
            try:
                # Получаем батч кадров
                batch = self.queue.get()
                if batch is None:  # сигнал для завершения
                    self.running = False
                    break

                # Записываем весь батч
                for frame, path in batch:
                    if not write_to_image(frame.frame, path):
                        raise Exception(f"Error saving frame: {path}")

            except Exception as e:
                # Тут можно добавить логирование ошибок
                print(f"Writer error: {e}")


class BufferedImageWrite:
    def __init__(self, buffer_size: int = 8):
        self.frames: List[Tuple[NumberedFrame, str]] = []
        self.buffer_size = buffer_size
        self.write_queue: Queue = Queue()
        self.writer: Optional[AsyncWriter] = None

    def start(self) -> None:
        if self.writer is None:
            self.writer = AsyncWriter(self.write_queue)
            self.writer.start()

    def write_frame(self, frame: NumberedFrame, path: str) -> None:
        self.frames.append((frame, path))
        if len(self.frames) >= self.buffer_size:
            self.flush()

    def flush(self) -> None:
        if self.frames:
            if self.writer is None:
                self.start()
            # Отправляем копию батча в очередь
            self.write_queue.put(self.frames[:])
            self.frames.clear()

    def shutdown(self) -> None:
        if self.writer is not None:
            self.flush()  # записываем оставшиеся кадры
            self.write_queue.put(None)  # отправляем сигнал завершения
            self.writer.join()  # ждем завершения процесса
            self.writer = None
