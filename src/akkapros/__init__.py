"""
akkapros - Akkadian Prosody Toolkit
"""

__version__ = "2.0.0"
__author__ = "Samuel KABAK"
__license__ = "MIT"
__project__ = "Akkadian Prosody Toolkit"
__repo__ = "akkapros"
__repo_url__ = f"https://github.com/samuelkabak/{__repo__}"


def get_repo_url() -> str:
	"""Return the canonical project repository URL."""
	return __repo_url__


def get_version_display(tool_name: str | None = None) -> str:
	"""Return a professional multi-line version display for CLI tools."""
	lines = [
		f"{__project__} version {__version__}",
		f"Author: {__author__}",
		f"License: {__license__}",
		f"Repository: {get_repo_url()}",
	]
	if tool_name:
		lines.append(f"Tool: {tool_name}")
	return "\n".join(lines)


__version_display__ = get_version_display()

# Don't try to import non-existent objects
# Just make the package importable