from feature_extraction_server.core.job import Job
from feature_extraction_server.services.model_namespace import ModelNamespace
from feature_extraction_server.services.task_namespace import TaskNamespace
from feature_extraction_server.services.execution_state import ExecutionState

from simple_plugin_manager.service import Service

# from feature_extraction_server.core.exceptions import NoDefaultModelException, NoDefaultTaskException
import logging
logger = logging.getLogger(__name__)

class JobBuilder(Service):
    
    @staticmethod
    def initialize_service(model_namespace: ModelNamespace, task_namespace: TaskNamespace, execution_state: ExecutionState):
        logger.debug("Initializing JobBuilder")

        
        return JobBuilder(model_namespace = model_namespace, task_namespace = task_namespace, execution_state = execution_state)
    
    
    def __init__(self, model_namespace, task_namespace, execution_state):
        self.model_namespace = model_namespace
        self.task_namespace = task_namespace
        self.execution_state = execution_state
    
    def from_task_and_model_name(self, task_name, model_name, kwargs):
        model = self.model_namespace.instantiate_plugin(model_name)
        task = self.task_namespace.instantiate_plugin(task_name)
        return Job(task=task, model=model, kwargs=kwargs, execution_state=self.execution_state)
    
    # def from_task_name(self, task_name, kwargs):
    #     try:
    #         model_name = self.default_model_names[task_name]
    #     except KeyError:
    #         error_msg = f"Task {task_name} does not have a default model."
    #         logger.warn(error_msg)
    #         raise NoDefaultModelException(error_msg)
    #     return self.from_task_and_model_name(task_name, model_name, kwargs)
    
    # def from_defaults(self, kwargs):
    #     if self.default_task_name is None:
    #         error_msg = "No default task name is set."
    #         logger.warn(error_msg)
    #         raise NoDefaultTaskException(error_msg)
    #     return self.from_task_name(self.default_task_name, kwargs)