import tasklist
import importlib

class Task:
    'class for managing and storing task parameters'
    
    def __init__(self, taskname):
        self.name = taskname

    def run(self, cameraInput, userInput):
        return importlib.import_module(f"tasklist.{self.name}").run(cameraInput, userInput)