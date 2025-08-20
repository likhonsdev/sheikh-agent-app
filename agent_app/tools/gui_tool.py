from typing import Optional, Type, List
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from vncdotool import api
import os
import google.generativeai as genai
from PIL import Image

# --- VNC Manager ---
# Manages the connection to the VNC server in the sandbox container
class VNCManager:
    def __init__(self, host, port, password):
        self.host = host
        self.port = port
        self.password = password
        self.client: Optional[api.VNCDoToolClient] = None

    def connect(self):
        if not self.client or not self.client.is_connected():
            print(f"▶️ Connecting to VNC server at {self.host}:{self.port}...")
            try:
                self.client = api.connect(f'{self.host}::{self.port}', password=self.password)
                print("✅ VNC connection successful.")
            except Exception as e:
                print(f"🔥 VNC Connection Error: {e}")
                self.client = None

    def get_client(self) -> Optional[api.VNCDoToolClient]:
        self.connect() # Ensure we are connected before returning the client
        return self.client

    def close_client(self):
        if self.client and self.client.is_connected():
            self.client.disconnect()
            print("⏹️ VNC connection closed.")

# The agent_gui_sandbox is the hostname inside the Docker network
vnc_manager = VNCManager(host='agent_gui_sandbox', port=5901, password='agent123')


# --- Input Schemas ---
class MouseMoveInput(BaseModel):
    x: int = Field(description="The x-coordinate to move the mouse to.")
    y: int = Field(description="The y-coordinate to move the mouse to.")

class TypeTextInput(BaseModel):
    text: str = Field(description="The text to type on the keyboard.")

class CaptureScreenInput(BaseModel):
    filename: str = Field(description="The filename for the screenshot, e.g., 'desktop_view.png'.")


# --- LangChain Tools for GUI Control ---

class MouseMoveTool(BaseTool):
    name = "MouseMove"
    description = "Moves the mouse cursor to a specific (x, y) coordinate on the screen."
    args_schema: Type[BaseModel] = MouseMoveInput

    def _run(self, x: int, y: int) -> str:
        client = vnc_manager.get_client()
        if not client: return "VNC client not connected."
        client.mouseMove(x, y)
        return f"Mouse moved to ({x}, {y})."

class MouseClickTool(BaseTool):
    name = "MouseClick"
    description = "Performs a left mouse click at the current cursor position."

    def _run(self) -> str:
        client = vnc_manager.get_client()
        if not client: return "VNC client not connected."
        client.mousePress(1) # 1 for left click
        return "Mouse clicked."

class TypeTextTool(BaseTool):
    name = "TypeText"
    description = "Types the given text using the keyboard. Useful for terminals, search bars, etc."
    args_schema: Type[BaseModel] = TypeTextInput

    def _run(self, text: str) -> str:
        client = vnc_manager.get_client()
        if not client: return "VNC client not connected."
        client.keyPress(text)
        return f"Typed text: '{text}'"

class CaptureScreenTool(BaseTool):
    name = "CaptureGUIScreen"
    description = "Captures the current view of the GUI desktop and saves it to the shared 'screenshots' folder. This is the primary way to 'see' the environment."
    args_schema: Type[BaseModel] = CaptureScreenInput

    def _run(self, filename: str) -> str:
        client = vnc_manager.get_client()
        if not client: return "VNC client not connected."
        path = f"/app/screenshots/{filename}"
        client.captureScreen(path)
        return f"Screen captured and saved to {filename}. You should now analyze this image to decide the next action."

# --- NEW VISION TOOL ---

class DescribeScreenInput(BaseModel):
    query: str = Field(description="The question to ask about the screen. E.g., 'Where is the terminal icon?' or 'What is the text in the error message?'")
    image_path: str = Field(description="The path to the screenshot file to analyze, e.g., '/app/screenshots/desktop.png'.")

class DescribeScreenTool(BaseTool):
    name = "DescribeScreen"
    description = """
    Analyzes a captured screenshot of the GUI and answers a question about it.
    Crucial for understanding the screen to find coordinates for clicking or to read text.
    Always use CaptureGUIScreen first to get an up-to-date image.
    """
    args_schema: Type[BaseModel] = DescribeScreenInput

    def _run(self, query: str, image_path: str) -> str:
        try:
            print(f"👀 Analyzing screen with vision: {query}")
            # Ensure API key is configured
            if not os.getenv("GOOGLE_API_KEY"):
                return "Error: GOOGLE_API_KEY is not set."
            genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

            vision_model = genai.GenerativeModel('gemini-pro-vision')
            img = Image.open(image_path)

            # The prompt guides the model to give precise, actionable answers
            full_prompt = f"""
            Analyze this screenshot of a desktop. The user's query is: '{query}'.
            Respond with a concise description. If the user is asking for the location of something,
            provide the most likely (x, y) coordinate. The screen resolution is 1280x720.
            Example response: 'The terminal icon is at coordinate (500, 15).'
            """

            response = vision_model.generate_content([full_prompt, img])
            return f"Vision Analysis: {response.text}"
        except FileNotFoundError:
            return f"Error: Screenshot file not found at '{image_path}'. Did you run CaptureGUIScreen first?"
        except Exception as e:
            return f"Error using vision model: {e}"

# --- Add all tools to a list for easy import ---
gui_tools = [
    CaptureScreenTool(),
    DescribeScreenTool(), # The new vision tool!
    MouseMoveTool(),
    MouseClickTool(),
    TypeTextTool(),
]
