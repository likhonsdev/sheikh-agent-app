from langchain.tools import BaseTool

class ToDoTool(BaseTool):
    name = "ToDoTool"
    description = "A dummy tool for managing a to-do list."

    def _run(self, *args, **kwargs):
        return "ToDoTool is not implemented yet."

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("ToDoTool does not support async")

class ViewTasksTool(BaseTool):
    name = "ViewTasksTool"
    description = "A dummy tool for viewing tasks."

    def _run(self, *args, **kwargs):
        return "ViewTasksTool is not implemented yet."

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("ViewTasksTool does not support async")
