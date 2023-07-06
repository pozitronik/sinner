import os
import shutil
import time
from typing import List

import onnxruntime
import psutil
import torch
from sinner.core import Core
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.state import State
from sinner.utilities import resolve_relative_path, limit_resources, get_app_dir


class BenchmarkParameters:
    source_path: str = resolve_relative_path('../tests/data/targets/target.png', __file__)
    target_path: str = resolve_relative_path('../tests/data/frames', __file__)
    output_path: str = os.path.join(get_app_dir(), 'temp/benchmark')
    many_faces: bool = True
    extract_frames: bool = False
    max_memory: int = psutil.virtual_memory().available
    execution_threads: int
    execution_providers: List[str]
    frame_processors: list[str]
    temp_dir: str = os.path.join(get_app_dir(), 'temp/benchmark')


class Benchmark:
    results: List[dict[str, str, int, int]] = []
    last_execution_time: int = 0
    params: BenchmarkParameters

    def __init__(self, processor: str, execution_providers: list[str] | None = None):
        self.params = BenchmarkParameters()
        if execution_providers is None:
            execution_providers = onnxruntime.get_available_providers()
        limit_resources(self.params.max_memory)
        delta = 3000000000
        for execution_provider in execution_providers:
            threads = 1
            while True:
                print(f'Benchmarking {processor} with {execution_provider} on {threads} thread(s)')
                shutil.rmtree(self.params.temp_dir, ignore_errors=True)
                self.params.frame_processors = [processor]
                self.params.execution_threads = threads
                self.params.execution_providers = [execution_provider]

                execution_time = self.benchmark()

                self.store_result(processor, execution_provider, threads, execution_time)
                print(f"Result for {processor} with {execution_provider} on {threads} thread(s) = {execution_time} ns (~{execution_time / 1000000000} sec -> {98 / (execution_time / 1000000000)} FPS)")
                if self.last_execution_time != 0 and execution_time > self.last_execution_time + delta:
                    break
                self.last_execution_time = execution_time
                threads += 1
        self.print_results()

    def store_result(self, processor: str, execution_provider: str, threads: int, execution_time: int):
        self.results.append({'processor': processor, 'provider': execution_provider, 'threads': threads, 'time': execution_time})

    def benchmark(self) -> int:
        current_target_path = self.params.target_path
        current_handler = Core.suggest_handler(current_target_path)
        state = State(
            source_path=self.params.source_path,
            target_path=current_target_path,
            frames_count=current_handler.fc,
            temp_dir=self.params.temp_dir
        )
        processor_name = self.params.frame_processors[0]
        current_processor = BaseFrameProcessor.create(processor_name, self.params, state)
        start_time = time.time_ns()
        current_processor.process(frames_handler=current_handler, extract_frames=self.params.extract_frames, desc=processor_name)
        end_time = time.time_ns()
        self.release_resources()
        return end_time - start_time

    def print_results(self) -> None:
        self.results = sorted(self.results, key=lambda x: (x['processor'], x['provider'], x['threads']))
        for stats in self.results:
            seconds = int(int(stats['time']) / 1000000000)
            fps = round(98 / seconds, 2)
            print(f"Result for {stats['processor']} with {stats['provider']} on {stats['threads']} thread(s) = {stats['time']} ns (~{seconds} sec -> {fps} FPS)")

    def release_resources(self) -> None:
        if 'CUDAExecutionProvider' in self.params.execution_providers:
            torch.cuda.empty_cache()
