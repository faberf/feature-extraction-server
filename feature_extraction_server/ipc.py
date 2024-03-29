import multiprocessing as mp
import threading
import logging
import uuid
from importlib import import_module
from feature_extraction_server.tasks import tasks
from feature_extraction_server.utils import get_memory_usage
import time 

class ModelProcessManager:
    def __init__(self):
        self.manager = mp.Manager()
        self.running_processes = self.manager.list()
        self.input_queues = self.manager.dict()
        self.results = self.manager.dict()  # {job_id: {"result": result_value, "error": exception_object}}
        self.process_state = self.manager.dict()  # {model_name: {"state": "running"|"starting"|"loading"|"start_failed"|"load_failed"|"stopped", "error": exception_object}}
        self.lock = self.manager.Lock()

    def add_job(self, model_name, task, kwargs):
        if model_name not in self.running_processes:
            self.start_process(model_name)
        job_id = str(uuid.uuid4())
        self.input_queues[model_name].put((job_id, task, kwargs))
        return job_id

    def start_process(self, model_name):
        with self.lock:
            if model_name in self.running_processes:
                logging.warning(f"Process {model_name} already running")
                return
            
            try:
                self.process_state[model_name] = {"state": "starting"}
                input_queue = self.manager.Queue()
                self.input_queues[model_name] = input_queue
                p = mp.Process(target=self.process_worker, args=(model_name, input_queue, self.results, self.process_state))
                p.start()
                self.running_processes.append(model_name)
            except Exception as e:
                logging.error(f"Process {model_name} failed to start")
                self.process_state[model_name] = {"state":"start_failed", "error":e}
                raise e
    
    def await_running(self, model_name):
        while not model_name in self.process_state or not self.process_state[model_name]['state'] == 'running':
            time.sleep(0.01)
            if self.process_state[model_name]['state'] == 'start_failed':
                logging.error(f"Process {model_name} failed to start")
                raise self.process_state[model_name]["error"]
            if self.process_state[model_name]['state'] == 'load_failed':
                logging.error(f"Process {model_name} failed to load")
                raise self.process_state[model_name]["error"]
    
    def await_stopped(self, model_name):
        while not model_name in self.process_state or not self.process_state[model_name]['state'] == 'stopped':
            time.sleep(0.01)
            if self.process_state[model_name]['state'] == 'start_failed':
                logging.error(f"Process {model_name} failed to start")
                raise self.process_state[model_name]["error"]
            if self.process_state[model_name]['state'] == 'load_failed':
                logging.error(f"Process {model_name} failed to load")
                raise self.process_state[model_name]["error"]
    
    def remove_process(self, model_name):
        input_queue = self.input_queues.get(model_name, None)
        if input_queue is None:
            raise ValueError(f"Process {model_name} not found")
        input_queue.put(None)
    

    def get_result(self, model_name, job_id):
        while job_id not in self.results:
            time.sleep(0.01)
            if self.process_state[model_name]['state'] == 'start_failed':
                logging.error(f"Process {model_name} failed to start")
                raise self.process_state[model_name]["error"]
            if self.process_state[model_name]['state'] == 'load_failed':
                logging.error(f"Process {model_name} failed to load")
                raise self.process_state[model_name]["error"]
        
        result_entry = self.results.pop(job_id)
        
        if 'error' in result_entry:
            logging.error(f"Error in process {model_name} while executing job {job_id}")
            raise result_entry['error']  # Propagate the error to the caller
        
        return result_entry['result']

    @staticmethod
    def process_worker(model_name, input_queue, results, process_state):
        process_state[model_name] = {"state": "loading"}
        try:
            module = import_module(f'feature_extraction_server.models.{model_name}')
        except ImportError:
            error_msg = f"Model {model_name} not found"
            logging.error(error_msg)
            process_state[model_name] = {"state":"load_failed", "error":ImportError(error_msg)}
            return
        process_state[model_name] = {"state": "running"}
        logging.debug(f"Process {model_name} loaded")
        logging.debug(f"Process {model_name} memory usage: {get_memory_usage()}")
        while True:
            next_job = input_queue.get()
            if next_job is None:
                process_state[model_name] = {"state": "stopped"}
                break
            
            job_id, task, kwargs = next_job
            try:
                base_function = getattr(module, task)
                task_function = tasks[task](base_function)
                ModelProcessManager.execute_job(job_id, task_function, kwargs, results)
            except AttributeError:
                error_msg = f"Function {task} not found in the {model_name} module"
                results[job_id] = {"error": AttributeError(error_msg)}

    @staticmethod
    def execute_job(job_id, function, kwargs, results):
        try:
            result = function(**kwargs)
            results[job_id] = {"result": result}
        except Exception as e:
            results[job_id] = {"error": e}
        
    def shutdown(self):
        # Kill all processes
        for process in self.running_processes:
            self.input_queues[process].put(None)

    def __del__(self):
        self.shutdown()
