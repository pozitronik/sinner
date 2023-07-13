import os
import shutil
import time
from argparse import Namespace
from typing import List, Any
from colorama import Fore, Style

import onnxruntime
import psutil
import torch

from sinner.Core import Core
from sinner.Parameters import Parameters
from sinner.processors.frame.BaseFrameProcessor import BaseFrameProcessor
from sinner.State import State
from sinner.utilities import resolve_relative_path, limit_resources, get_app_dir, suggest_execution_providers, suggest_execution_threads, decode_execution_providers, list_class_descendants
from sinner.validators.AttributeLoader import AttributeLoader, Rules


class Benchmark(AttributeLoader):
    source_path: str
    target_path: str
    output_path: str
    many_faces: bool
    extract_frames: bool
    max_memory: int
    execution_provider: List[str]
    frame_processor: str

    execution_threads: int
    frame_processors: list[str]
    temp_dir: str

    results: List[dict[str, Any]] = []
    parameters: Namespace
    delta: int = 1000000000  # ns, if the run time between runs more that the delta, stop running

    def rules(self) -> Rules:
        return [
            {
                'parameter': {'source', 'source-path'},
                'attribute': 'source_path',
                'default': resolve_relative_path('../tests/data/targets/target.png', __file__),
                'required': True,
                'help': 'Select a input image with the source face'
            },
            {
                'parameter': {'target', 'target-path'},
                'attribute': 'target_path',
                'required': True,
                'default': resolve_relative_path('../tests/data/frames', __file__),
                'help': 'Select the target file (image or video) or the directory'
            },
            {
                'parameter': {'output', 'output-path'},
                'attribute': 'output_path',
                'default': os.path.join(get_app_dir(), 'temp/benchmark'),
                'help': 'Select an output file or a directory'
            },
            {
                'parameter': 'many-faces',
                'default': True,
                'help': 'Enable every face processing in the target'
            },
            {
                'parameter': 'extract-frames',
                'default': False,
                'help': 'Extract video frames before processing'
            },
            {
                'parameter': 'max-memory',
                'default': int(psutil.virtual_memory().available / 1024**3)
            },
            {
                'parameter': 'execution-provider',
                'required': True,
                'default': ['cpu'],
                'choices': suggest_execution_providers()
            },
            {
                'parameter': 'temp-dir',
                'default': os.path.join(get_app_dir(), 'temp/benchmark'),
                'help': 'Select the directory for temporary files'
            },
            {
                'parameter': 'frame-processor',
                'default': 'FaceSwapper',
                'required': True,
                'choices': list_class_descendants(resolve_relative_path('processors/frame'), 'BaseFrameProcessor'),
                'help': 'Select the frame processor from available processors'
            },
        ]

    def __init__(self, parameters: Namespace | None = None):
        # processor: str, execution_providers: list[str] | None = None, source_path: str | None = None, target_path: str | None = None):
        super().__init__(parameters)
        self.parameters = parameters
        Parameters.update_parameters(parameters, self)  # load validated values back to parameters

        if self.execution_provider is None:
            execution_providers = onnxruntime.get_available_providers()
        else:
            execution_providers = decode_execution_providers(self.execution_provider)
        limit_resources(self.max_memory)

        for execution_provider in execution_providers:
            threads = 1
            last_execution_time = 0
            while True:
                print(f'Benchmarking {self.frame_processor} with {execution_provider} on {threads} thread(s)')
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                self.frame_processors = [self.frame_processor]
                self.execution_threads = threads
                self.execution_providers = [execution_provider]

                execution_time = self.benchmark()

                self.store_result(self.frame_processor, execution_provider, threads, execution_time)
                print(f"Result for {self.frame_processor} with {execution_provider} on {threads} thread(s) = {execution_time} ns (~{execution_time / 1000000000} sec -> {98 / (execution_time / 1000000000)} FPS)")
                if last_execution_time != 0 and execution_time > last_execution_time + self.delta:
                    break
                last_execution_time = execution_time
                threads += 1
        self.print_results()

    def store_result(self, processor: str, execution_provider: str, threads: int, execution_time: int) -> None:
        self.results.append({'processor': processor, 'provider': execution_provider, 'threads': threads, 'time': execution_time})

    def benchmark(self) -> int:
        current_target_path = self.target_path
        current_handler = Core.suggest_handler(self.parameters, current_target_path)
        state = State(
            parameters=self.parameters,
            frames_count=current_handler.fc,
            temp_dir=self.temp_dir
        )
        processor_name = self.frame_processors[0]
        current_processor = BaseFrameProcessor.create(processor_name, self.parameters, state)
        start_time = time.time_ns()
        current_processor.process(frames_handler=current_handler, extract_frames=self.extract_frames, desc=processor_name)
        end_time = time.time_ns()
        self.release_resources()
        return end_time - start_time

    def print_results(self) -> None:
        style_set = [Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
        self.results = sorted(self.results, key=lambda x: (x['processor'], x['provider'], x['threads']))
        provider = ''
        style_index = -1
        fastest_run = min(self.results, key=lambda x: x['time'])['time']  # fastest
        slowest_run = max(self.results, key=lambda x: x['time'])['time']  # slowest
        for stats in self.results:
            seconds = int(int(stats['time']) / 1000000000)
            fps = round(98 / seconds, 2)
            p_style = style_set[0]
            if provider != stats['provider']:
                provider = stats['provider']
                style_index += 1
                p_style = style_set[style_index]
            r_time = stats['time']
            if r_time == slowest_run:
                r_time = f'{Fore.RED}{r_time}{Style.RESET_ALL}'
            elif r_time == fastest_run:
                r_time = f'{Fore.GREEN}{r_time}{Style.RESET_ALL}'
            else:
                r_time = f'{Fore.BLUE}{r_time}{Style.RESET_ALL}'
            print(f"Result for {Fore.YELLOW}{stats['processor']}{Style.RESET_ALL} with {p_style}{provider}{Style.RESET_ALL} on {Fore.YELLOW}{stats['threads']}{Style.RESET_ALL} thread(s) ="
                  f" {r_time} ns (~{seconds} sec -> {fps} FPS)")

    def release_resources(self) -> None:
        if 'CUDAExecutionProvider' in self.execution_providers:
            torch.cuda.empty_cache()
