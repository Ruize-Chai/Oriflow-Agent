"""
ANSI COLORS AND COLORING TOOL
ANSI转义色与上色工具
"""

from typing import Dict
import os
# 使用colorama自动兼容颜色
# Try to enable ANSI sequences on Windows using colorama; fall back to ctypes when colorama absent
try:
	import colorama
	colorama.init()
except Exception:
	if os.name == 'nt':
		try:
			import ctypes
			kernel32 = ctypes.windll.kernel32
			h = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
			mode = ctypes.c_uint()
			if kernel32.GetConsoleMode(h, ctypes.byref(mode)):
				ENABLE_VT_PROCESSING = 0x0004
				kernel32.SetConsoleMode(h, mode.value | ENABLE_VT_PROCESSING)
		except Exception:
			pass


class GET_COLOR:
	'''
	ANSI COLORS
	'''
	RESET = "\033[0m"
	BOLD = "\033[1m"
	DIM = "\033[2m"
	UNDERLINE = "\033[4m"
	REVERSE = "\033[7m"

	BLACK = "\033[30m"
	RED = "\033[31m"
	GREEN = "\033[32m"
	YELLOW = "\033[33m"
	BLUE = "\033[34m"
	MAGENTA = "\033[35m"
	CYAN = "\033[36m"
	WHITE = "\033[37m"

	BG_BLACK = "\033[40m"
	BG_RED = "\033[41m"
	BG_GREEN = "\033[42m"
	BG_YELLOW = "\033[43m"
	BG_BLUE = "\033[44m"
	BG_MAGENTA = "\033[45m"
	BG_CYAN = "\033[46m"
	BG_WHITE = "\033[47m"

	# 亮色（可选）
	BRIGHT_BLACK = "\033[90m"
	BRIGHT_RED = "\033[91m"
	BRIGHT_GREEN = "\033[92m"
	BRIGHT_YELLOW = "\033[93m"
	BRIGHT_BLUE = "\033[94m"
	BRIGHT_MAGENTA = "\033[95m"
	BRIGHT_CYAN = "\033[96m"
	BRIGHT_WHITE = "\033[97m"

	@classmethod
	def as_dict(cls) -> Dict[str, str]:
		"""返回颜色名到 ANSI 码的映射字典。"""
		return {k: v for k, v in cls.__dict__.items() if k.isupper() and isinstance(v, str)}


def color(text: str, color_code: str) -> str:
	"""
	文本上色器
	"""
	return f"{color_code}{text}{GET_COLOR.RESET}"


__all__ = ["GET_COLOR", "color"]

