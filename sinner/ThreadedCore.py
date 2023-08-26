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

            extractor_handler = BaseFrameProcessor.suggest_handler(self.target_path, self.parameters)
            base_buffer = manager.list()
            for frame in extractor_handler:
                base_buffer.append(extractor_handler.extract_frame(frame))
            frame_buffers['FaceSwapper'] = base_buffer

            def sub_run(processor_name: str, next_processor_name: str, fc: int) -> None:
                current_processor = BaseFrameProcessor.create(processor_name, self.parameters)
                current_processor.process_buffered(frame_buffers, processor_name, next_processor_name, fc)

            for i, name in enumerate(self.frame_processor):
                next_index = i + 1
                next_name = self.frame_processor[next_index] if next_index < len(self.frame_processor) else None

                thread: Thread = Thread(target=sub_run, args=(name, next_name, extractor_handler.fc))
                self.update_status(f'Start {name} thread')
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()
