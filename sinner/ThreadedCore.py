from threading import Thread
from multiprocessing import Manager
from sinner.Core import Core
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor


class ThreadedCore(Core):

    def run(self) -> None:
        threads: list[Thread] = []

        with Manager() as manager:
            frame_buffers = manager.dict()

            for name in self.frame_processor:
                frame_buffers[name] = manager.list()

            for i, name in enumerate(self.frame_processor):
                next_index = i + 1
                next_name = self.frame_processor[next_index] if next_index < len(self.frame_processor) else None

                current_processor = BaseFrameProcessor.create(name, self.parameters)

                if i == 0:  # pass the first dictionary item to fill it in a separate thread
                    threads.append(Thread(target=current_processor.fill_initial_buffer, args=(frame_buffers[name],)))

                thread: Thread = Thread(target=current_processor.process_buffered, args=(frame_buffers, name, next_name, i))
                self.update_status(f'Start {name} thread')
                threads.append(thread)

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()
