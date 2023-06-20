from abc import ABC, abstractmethod

class BaseFrameProcessor(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def process(self):
        pass