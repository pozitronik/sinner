from threading import Thread
from sinner.Core import Core
from sinner.frame_buffers.FrameBufferManager import FrameBufferManager
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.typing import NumeratedFrame


class ThreadedCore(Core):

    def run(self) -> None:
        threads: list[Thread] = []

        frame_buffers = FrameBufferManager(self.frame_processor)

        for i, name in enumerate(self.frame_processor):
            current_processor = BaseFrameProcessor.create(name, self.parameters)

            if i == 0:  # pass the first dictionary item to fill it in a separate thread
                threads.append(Thread(target=current_processor.fill_initial_buffer, args=(frame_buffers, name)))

            thread: Thread = Thread(target=current_processor.process_buffered, args=(frame_buffers, name))
            self.update_status(f'Start {name} thread')
            threads.append(thread)

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
