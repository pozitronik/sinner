import os
import shutil
import time
from typing import List

import psutil

from sinner.core import Core
from sinner.utilities import resolve_relative_path, limit_resources, get_app_dir


class BenchmarkParameters:
    source_path: str = resolve_relative_path('../tests/data/targets/target.png', __file__)
    target_path: str = resolve_relative_path('../tests/data/frames', __file__)
    output_path: str = os.path.join(get_app_dir(), 'temp/benchmark')
    many_faces: bool = True
    extract_frames: bool = False
    max_memory: int = psutil.virtual_memory().available
    execution_threads: int
    execution_providers: List[str] = ['CUDAExecutionProvider']
    frame_processors: list[str]
    temp_dir: str = os.path.join(get_app_dir(), 'temp/benchmark')


class Benchmark:
    results: dict[str, int] = {}
    last_execution_time: int = 0

    def __init__(self, processor: str):
        threads = 1
        params = BenchmarkParameters()
        limit_resources(params.max_memory)
        delta = 3000000000
        while True:
            print(f'Benchmarking on {threads} thread(s)')
            shutil.rmtree(params.temp_dir, ignore_errors=True)
            params.frame_processors = [processor]
            params.execution_threads = threads
            core = Core(params=params)
            start_time = time.time_ns()
            core.benchmark()
            end_time = time.time_ns()
            execution_time = end_time - start_time
            self.results[str(threads)] = execution_time
            if self.last_execution_time != 0 and execution_time > self.last_execution_time + delta:
                break
            self.last_execution_time = execution_time
            threads += 1
        self.print_results()

    def print_results(self) -> None:
        for key, value in self.results.items():
            print(f'Threads: {key} = {value} ns')
