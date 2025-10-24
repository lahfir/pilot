"""
Coordinator agent for task analysis and delegation.
Uses LLM with structured outputs for intelligent task classification.
"""

from ..schemas.task_analysis import TaskAnalysis


class CoordinatorAgent:
    """
    Analyzes user tasks using LLM and delegates to appropriate specialized agents.
    Uses structured outputs to classify tasks and create execution plans.
    """

    def __init__(self, llm_client):
        """
        Initialize coordinator agent.

        Args:
            llm_client: LLM client for intelligent task analysis
        """
        self.llm_client = llm_client

    async def analyze_task(self, task: str) -> TaskAnalysis:
        """
        Analyze user task using LLM and break it down into specific sub-tasks.

        Args:
            task: User's natural language task description

        Returns:
            TaskAnalysis with classification and specific sub-tasks for each agent
        """
        prompt = f"""
You are an intelligent task coordinator. Your job is to:
1. Analyze the overall task
2. Determine which agents are needed
3. Break down the task into SPECIFIC sub-tasks for each agent
4. Define clear objectives and expected outputs for each agent

Original Task: "{task}"

IMPORTANT PRINCIPLES:
- Each agent should have a SPECIFIC, FOCUSED sub-task
- Sub-tasks should be sequential - each agent completes their part and hands off
- Browser agent: Research, gather data, download files, extract information
- GUI agent: Interact with desktop apps, open files, enter data, manipulate UI
- System agent: File operations, folder management, terminal commands

TASK BREAKDOWN GUIDELINES:

For Browser Agent:
- Objective: What SPECIFIC information/data to research and gather
- Expected Output: What data/information will be extracted (as text, screenshots, or downloaded files)
- The browser agent should STOP after gathering the data - NOT try to open desktop apps
- IMPORTANT: Only specify "download file" or "save as CSV" if the user EXPLICITLY asks for it
- If user just wants information, browser can extract it as text (no download needed)

For GUI Agent:
- Objective: What SPECIFIC desktop app interaction is needed (use data from previous agent)
- Expected Output: What should be accomplished in the desktop app
- Can reference files/data from browser agent if applicable

For System Agent:
- Objective: What SPECIFIC file/folder operations are needed
- Expected Output: What files/folders should exist after completion

EXAMPLES:

Task: "Research Nvidia stock and enter data in Numbers app"
- requires_browser: true
- requires_gui: true
- requires_system: false
- browser_subtask:
  - objective: "Research and gather Nvidia stock performance data from financial websites (current price, volume, market cap, etc.)"
  - expected_output: "Stock performance data extracted as text with key metrics"
- gui_subtask:
  - objective: "Open Numbers app, create new document, and manually enter the stock data from browser agent into a formatted table"
  - expected_output: "Numbers document with Nvidia stock data displayed in a table"

Task: "Research Tesla quarterly earnings and save as PDF"
- requires_browser: true
- requires_gui: false
- requires_system: false
- browser_subtask:
  - objective: "Find Tesla quarterly earnings report and download it as PDF"
  - expected_output: "Tesla earnings PDF file downloaded to Downloads folder"

Task: "Research Nvidia stock performance"
- requires_browser: true
- requires_gui: false
- requires_system: false
- browser_subtask:
  - objective: "Research current Nvidia stock performance including price, volume, market cap, and recent trends"
  - expected_output: "Stock performance summary with key metrics extracted as text"

Task: "Download image of Eiffel Tower and set as desktop wallpaper"
- requires_browser: true
- requires_gui: true
- requires_system: false
- browser_subtask:
  - objective: "Search for and download a high-quality image of the Eiffel Tower"
  - expected_output: "Downloaded image file saved to Downloads folder"
- gui_subtask:
  - objective: "Open System Preferences, navigate to Desktop settings, and set the downloaded image as wallpaper"
  - expected_output: "Desktop wallpaper changed to Eiffel Tower image"

Task: "Open Calculator app"
- requires_browser: false
- requires_gui: true
- requires_system: false
- gui_subtask:
  - objective: "Launch the Calculator application"
  - expected_output: "Calculator app open and ready"

Task: "Create a folder called Projects in Documents"
- requires_browser: false
- requires_gui: false
- requires_system: true
- system_subtask:
  - objective: "Create a new folder named 'Projects' in the Documents directory"
  - expected_output: "Projects folder exists in ~/Documents/"

Now analyze this task and provide the breakdown:
"""

        # Use LLM with structured output
        structured_llm = self.llm_client.with_structured_output(TaskAnalysis)
        analysis = await structured_llm.ainvoke(prompt)

        return analysis
