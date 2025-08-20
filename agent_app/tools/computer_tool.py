from langchain.tools import BaseTool

class ComputerTool(BaseTool):
    name = "ComputerTool"
    description = "A dummy tool for computer interaction."

    def _run(self, *args, **kwargs):
        return "ComputerTool is not implemented yet."

    def _arun(self, *args, **kwargs):
        raise NotImplementedError("ComputerTool does not support async")
