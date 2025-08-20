import subprocess
import json
from typing import Type, Dict, Any
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

class PlaywrightMCPInput(BaseModel):
    tool_name: str = Field(description="The name of the Playwright MCP tool to run (e.g., 'browser_navigate').")
    tool_args: Dict[str, Any] = Field(description="The arguments for the Playwright MCP tool as a dictionary.")

class PlaywrightMCPTool(BaseTool):
    name = "PlaywrightMCP"
    description = "Executes a command on the Playwright MCP server to control a web browser. Use this for all browser-related tasks."
    args_schema: Type[BaseModel] = PlaywrightMCPInput

    def _run(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        # Construct the command payload for the MCP server
        mcp_command = {
            "tool": tool_name,
            "args": tool_args
        }
        command_json = json.dumps(mcp_command)

        # Define the docker command to run the MCP server
        docker_command = ["docker", "run", "-i", "--rm", "mcp/playwright"]

        try:
            print(f"▶️ Executing Playwright MCP command: {command_json}")

            # Start the subprocess
            process = subprocess.Popen(
                docker_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True  # Use text mode for automatic encoding/decoding of streams
            )

            # Send the command to the container's stdin and get the output
            stdout, stderr = process.communicate(input=command_json)

            # Check for errors
            if process.returncode != 0:
                error_message = f"Playwright MCP tool '{tool_name}' failed with exit code {process.returncode}."
                if stderr:
                    error_message += f"\\nError details: {stderr.strip()}"
                if stdout:
                    error_message += f"\\nOutput: {stdout.strip()}"
                print(f"🔥 MCP Error: {error_message}")
                return error_message

            # If successful, return the output from the container
            print(f"✅ MCP Result: {stdout.strip()}")
            return stdout.strip()

        except FileNotFoundError:
            error_message = "Error: The 'docker' command was not found. Please ensure Docker is installed and accessible in the system's PATH."
            print(f"🔥 MCP Error: {error_message}")
            return error_message
        except Exception as e:
            error_message = f"An unexpected error occurred while trying to run the Playwright MCP tool: {e}"
            print(f"🔥 MCP Error: {error_message}")
            return error_message

    def _arun(self, tool_name: str, tool_args: Dict[str, Any]):
        raise NotImplementedError("PlaywrightMCPTool does not support async")
