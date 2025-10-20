"""
System agent for file operations and terminal commands.
Uses Python directly for file ops - NO manual parsing bullshit.
"""

from typing import Dict, Any
import os
import glob
from pathlib import Path


class SystemAgent:
    """
    System operations using Python file operations.
    NO hardcoding - uses actual Python functions.
    """

    def __init__(self, tool_registry, safety_checker, llm_client=None):
        """
        Initialize system agent.

        Args:
            tool_registry: PlatformToolRegistry instance
            safety_checker: SafetyChecker for validating operations
            llm_client: LLM for understanding tasks
        """
        self.tool_registry = tool_registry
        self.safety_checker = safety_checker
        self.file_tool = tool_registry.get_tool("file")
        self.process_tool = tool_registry.get_tool("process")
        self.llm_client = llm_client

    async def execute_task(self, task: str) -> Dict[str, Any]:
        """
        Execute system task using Python file operations.

        Args:
            task: Natural language task description

        Returns:
            Result dictionary
        """
        task_lower = task.lower()

        # Find/search operations
        if any(kw in task_lower for kw in ["find", "search", "look for", "locate"]):
            return await self._find_files(task)
        
        # Move/copy operations
        elif "move" in task_lower:
            return await self._move_file(task)
        elif "copy" in task_lower:
            return await self._copy_file(task)
        
        # Create operations
        elif "create" in task_lower and "folder" in task_lower:
            return await self._create_folder(task)
        
        # List operations
        elif "list" in task_lower:
            return await self._list_files(task)
        
        else:
            return {
                "success": False,
                "action_taken": "Unknown system operation",
                "method_used": "system",
                "error": f"Cannot handle task: {task}",
            }

    async def _find_files(self, task: str) -> Dict[str, Any]:
        """
        Find files using glob patterns.
        """
        try:
            # Determine search location
            if "document" in task.lower():
                search_dir = str(Path.home() / "Documents")
            elif "download" in task.lower():
                search_dir = str(Path.home() / "Downloads")
            elif "desktop" in task.lower():
                search_dir = str(Path.home() / "Desktop")
            else:
                search_dir = str(Path.home())

            # Determine file type
            if "image" in task.lower() or "picture" in task.lower() or "photo" in task.lower():
                patterns = ["*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp", "*.webp"]
            elif "video" in task.lower():
                patterns = ["*.mp4", "*.mov", "*.avi", "*.mkv"]
            elif "pdf" in task.lower():
                patterns = ["*.pdf"]
            elif "text" in task.lower() or "document" in task.lower():
                patterns = ["*.txt", "*.doc", "*.docx"]
            else:
                patterns = ["*"]

            print(f"  📂 Searching in: {search_dir}")
            print(f"  🔍 Patterns: {patterns}")

            # Search for files
            found_files = []
            for pattern in patterns:
                search_pattern = os.path.join(search_dir, "**", pattern)
                files = glob.glob(search_pattern, recursive=True)
                found_files.extend(files)

            # Limit results
            found_files = found_files[:20]  # Max 20 files

            if found_files:
                file_list = "\n".join([f"  - {os.path.basename(f)}" for f in found_files[:10]])
                return {
                    "success": True,
                    "action_taken": f"Found {len(found_files)} files in {search_dir}",
                    "method_used": "system",
                    "data": {
                        "files": found_files,
                        "count": len(found_files),
                        "search_dir": search_dir,
                        "preview": file_list,
                    },
                }
            else:
                return {
                    "success": False,
                    "action_taken": f"No files found in {search_dir}",
                    "method_used": "system",
                    "error": "No matching files found",
                }

        except Exception as e:
            return {
                "success": False,
                "action_taken": "File search failed",
                "method_used": "system",
                "error": str(e),
            }

    async def _move_file(self, task: str) -> Dict[str, Any]:
        """
        Move file - requires LLM to extract paths.
        """
        return {
            "success": False,
            "action_taken": "Move file",
            "method_used": "system",
            "error": "Move operation requires source and destination paths",
        }

    async def _copy_file(self, task: str) -> Dict[str, Any]:
        """
        Copy file - requires LLM to extract paths.
        """
        return {
            "success": False,
            "action_taken": "Copy file",
            "method_used": "system",
            "error": "Copy operation requires source and destination paths",
        }

    async def _create_folder(self, task: str) -> Dict[str, Any]:
        """
        Create folder using Python.
        """
        try:
            # Extract folder name (simple approach)
            words = task.split()
            folder_name = None
            for i, word in enumerate(words):
                if word.lower() in ["folder", "directory"] and i > 0:
                    # Look backwards for the name
                    for j in range(i - 1, -1, -1):
                        if words[j].lower() not in ["a", "the", "named", "called", "create"]:
                            folder_name = words[j]
                            break
                    break

            if not folder_name:
                return {
                    "success": False,
                    "error": "Could not determine folder name",
                    "method_used": "system",
                }

            # Determine location
            if "download" in task.lower():
                base_dir = Path.home() / "Downloads"
            elif "document" in task.lower():
                base_dir = Path.home() / "Documents"
            elif "desktop" in task.lower():
                base_dir = Path.home() / "Desktop"
            else:
                base_dir = Path.cwd()

            folder_path = base_dir / folder_name
            folder_path.mkdir(parents=True, exist_ok=True)

            return {
                "success": True,
                "action_taken": f"Created folder: {folder_path}",
                "method_used": "system",
                "data": {"path": str(folder_path)},
            }

        except Exception as e:
            return {
                "success": False,
                "action_taken": "Create folder failed",
                "method_used": "system",
                "error": str(e),
            }

    async def _list_files(self, task: str) -> Dict[str, Any]:
        """
        List files in a directory.
        """
        try:
            # Determine directory
            if "download" in task.lower():
                dir_path = Path.home() / "Downloads"
            elif "document" in task.lower():
                dir_path = Path.home() / "Documents"
            elif "desktop" in task.lower():
                dir_path = Path.home() / "Desktop"
            else:
                dir_path = Path.cwd()

            files = list(dir_path.iterdir())
            file_names = [f.name for f in files[:20]]  # Max 20

            return {
                "success": True,
                "action_taken": f"Listed {len(file_names)} files in {dir_path}",
                "method_used": "system",
                "data": {"files": file_names, "path": str(dir_path)},
            }

        except Exception as e:
            return {
                "success": False,
                "action_taken": "List files failed",
                "method_used": "system",
                "error": str(e),
            }
