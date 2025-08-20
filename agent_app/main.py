import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub

# Import our custom tools
from tools.todo_tool import ToDoTool, ViewTasksTool
from tools.computer_tool import ComputerTool
from tools.playwright_mcp_tool import PlaywrightMCPTool
# Import the NEW GUI tools and manager
from tools.gui_tool import MouseMoveTool, MouseClickTool, TypeTextTool, CaptureScreenTool, vnc_manager

# --- Vision-Powered Upgrade (Optional but Recommended) ---
# To make the agent truly autonomous, you would add a vision model.
# Here's how you could structure a tool for that.
# You would need to pip install google-generativeai pillow
# from langchain.tools import BaseTool
# import google.generativeai as genai
# from PIL import Image
#
# class DescribeScreenTool(BaseTool):
#     name = "DescribeScreen"
#     description = "Analyzes a captured screenshot of the GUI and describes what is visible or answers a question about it. Use this to understand the screen and find coordinates for clicking."
#
#     def _run(self, query: str, image_path: str) -> str:
#         try:
#             genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
#             vision_model = genai.GenerativeModel('gemini-pro-vision')
#             img = Image.open(image_path)
#             full_prompt = f"Analyze this screenshot. {query}"
#             response = vision_model.generate_content([full_prompt, img])
#             return f"Vision Analysis: {response.text}"
#         except Exception as e:
#             return f"Error using vision model: {e}"
# -------------------------------------------------------------

def main():
    load_dotenv()
    print("🤖 Visual Agent is starting up...")

    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)

    # Define the expanded toolset
    tools = [
        PlaywrightMCPTool(),
        CaptureScreenTool(),
        MouseMoveTool(),
        MouseClickTool(),
        TypeTextTool(),
        ToDoTool(),
        ViewTasksTool(),
        ComputerTool(), # Still useful for non-interactive tasks!
    ]

    prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

    print("\n✅ Visual Agent is ready!")
    print("👀 You can watch the agent work by:")
    print("   1. Using a VNC client to connect to: vnc://localhost:5901 (password: agent123)")
    print("   2. Opening this URL in your browser: http://localhost:6901/?password=agent123")
    print("\nAsk me to perform tasks on the desktop. Type 'exit' to quit.")

    try:
        # Main interaction loop
        while True:
            user_input = input("\n👤 You: ")
            if user_input.lower() == 'exit':
                print("🤖 Shutting down...")
                break

            if user_input:
                response = agent_executor.invoke({"input": user_input})
                print(f"🤖 Agent: {response['output']}")

    finally:
        # Crucial: Close all connections gracefully
        vnc_manager.close_client()

if __name__ == '__main__':
    main()
