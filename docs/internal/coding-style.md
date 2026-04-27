### 🤖 Agent-Optimized Coding Style Guide v1.0

**Core Principle:** Optimize for the **lowest token cost per logical operation**, while preserving executability and correctness. Every character an agent reads or writes costs money.

#### 1. Imports & Structure: Group and Minimize
*   **Rule:** Put all imports at the top. Use the smallest number of lines possible. **Do not** add blank lines between import groups. A single blank line after all imports is allowed to separate from code.
*   **Why:** Every newline costs a token. Grouped imports are faster for an agent to locate and parse.
*   **Agent-Optimized Example:**
    ```python
    import sys, os, json
    from pathlib import Path
    from typing import Dict, List, Optional

    from myapp import core, utils
    ```
*   **Avoid:**
    ```python
    import sys
    import os

    import json

    from myapp import core
    from myapp import utils
    ```

#### 2. Comments: High Density, Low Volume
*   **Rule:** Comments should be **single-line, above the code**, and as concise as possible. Use `# <space>comment` format. **Never** use inline (right-hanging) comments except for trivial `# noqa` or `# type: ignore`.
*   **Why:** Inline comments break line scanning and add tokens that don't help the agent understand the *block* purpose. A short preceding comment is more token-efficient per explanatory value.
*   **Agent-Optimized Example:**
    ```python
    # Retry with backoff on rate limit
    for attempt in range(3):
        try:
            return api_call()
        except RateLimitError:
            time.sleep(2 ** attempt)
    ```
*   **Avoid:**
    ```python
    for attempt in range(3):
        try:
            return api_call()
        except RateLimitError:
            time.sleep(2 ** attempt)  # Exponential backoff for rate limiting
    ```

#### 3. Strings: Single Quotes by Default, No f-string Overhead
*   **Rule:** Use **single quotes** `''` for all strings unless the string contains single quotes. Use double quotes `""` *only* to avoid escaping internal single quotes. For docstrings, use `"""triple double quotes"""`.
*   **Why:** Single quotes save one keypress per string (no Shift key), but more importantly, they reduce token entropy and are the most common convention in token-efficient training data. Use `%` or `.format()` for complex strings if an f-string causes many dedicated `{var}` tokens.
*   **Agent-Optimized Example:**
    ```python
    name = 'Agent'
    error = f'Failed on {name}'  # Still fine for 1-2 vars
    debug = 'Value: %s' % value  # Sometimes more token-efficient
    ```

#### 4. Line Length: Short and Dense (88-100 characters)
*   **Rule:** Aim for **maximum 100 characters**, but do not force wrap. Let the model decide. Short lines (60-80) are often token-cheaper than long ones because they avoid large single-token runs.
*   **Why:** Very long lines become one giant token, which is inefficient to sample and parse. Short lines also keep diffs clean.
*   Use `ruff` with `line-length = 100`.

#### 5. Functions & Classes: Single Purpose, Clear Flow
*   **Rule:** One class per module. One primary function per class. Keep functions **short (under 20 lines of logic)**. Use obvious, action-based names (`process_item`, `send_request`).
*   **Why:** Agents can only "attend" to so many lines at once. Short functions reduce the need to scroll or re-read context. Clear names act as mini-comments without token cost.
*   **Agent-Optimized Example:**
    ```python
    class DataProcessor:
        def clean(self, record: Dict) -> Dict:
            if not record:
                return {}
            return {k: v for k, v in record.items() if v is not None}
    ```

#### 6. Control Flow: Explicit Comparisons
*   **Rule:** Prefer explicit comparisons (`is None`, `== 0`, `len(x) == 0`) over implicit truthiness, *unless* the variable is known to be a boolean.
*   **Why:** Explicit conditions are unambiguous and prevent the agent from having to resolve the truthiness rules of arbitrary types. This reduces reasoning errors and rework.
*   **Agent-Optimized Example:**
    ```python
    if len(items) == 0:
        return
    if result is None:
        raise ValueError('No result')
    while retries > 0:
        call()
    ```

#### 7. Exception Handling: Narrow and Local
*   **Rule:** Keep `try` blocks as short as 1-3 lines. Catch specific exceptions. Use `except Exception as e:` only as a last resort for logging + re-raise.
*   **Why:** Broad exception blocks hide bugs and confuse agents that are trying to reason about failure paths. Narrow blocks are faster to execute and easier to analyze.
*   **Agent-Optimized Example:**
    ```python
    try:
        data = parse(raw)
    except ParseError as e:
        log.warning('Parse failed: %s', e)
        data = default
    ```

#### 8. Token-Optimization-Specific Rules
*   **Rule A:** Use `result = fn()` and `if result:` over `if fn():` if the result is used again later. Calling `fn()` twice doubles token cost.
*   **Rule B:** Use `from module import name` for names used more than twice in a file. It saves `module.` tokens each time.
*   **Rule C:** Use `if x is not None` rather than `if not x is None` (fewer tokens, clearer).
*   **Rule D:** Use `return` and `continue` early to flatten nesting. Deeply nested code is token-expensive and hard for agents to track.
*   **Rule E:** Use `# region <name>` and `# endregion` to mark logical blocks. Some agents treat these as summarization hints.

#### 9. Formatting & Tooling for Agent Cost Control
*   Use **Ruff** for formatting (fast, low-config, widely used in agent training data).
*   Use **`dis` or `tokenize`** to profile token count of critical files. Aim for less than 1500 tokens per file (approx 50-70 lines of actual code/comments).
*   Prefer **`# fmt: off`** and **`# fmt: on`** around long lookup tables or data structures that would otherwise be reformatted across many expensive lines.

### 🔁 Migration from Barry's Guide to Agent Style

| Barry's Guide Rule | Agent-Optimized Rule (Save Cost, Keep Clarity) |
| :--- | :--- |
| Two blank lines between top-level blocks | **One blank line maximum** between functions/classes. |
| Comments as complete sentences | **Fragments allowed** where unambiguous: `# Retry up to 3 times.` |
| `if len(seq) == 0` preferred over `if seq` | Use **`if not seq` for sequences**, but `if x is None` for optionals — explicit when type can vary. |
| One class per module | **One class per module, plus small helper functions** (≤20 lines). |
| Narrow `try` blocks (good) | Keep same but **prefer `except` that immediately returns or assigns a fallback**. |
| Public/non-public via underscores | **Same**, but omit double-underscore unless essential — it adds token noise. |

### 📊 Example: Before and After Agent Optimization

**Original (Human-optimized, high token count):**
```python
class ConfigurationError(Exception):
    """Raised when the application configuration is invalid."""
    pass

def load_configuration(file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.

    If no file path is provided, the default 'config.json' will be used.
    Returns a dictionary of configuration parameters.
    """
    if file_path is None:
        file_path = 'config.json'
    try:
        with open(file_path, 'r') as fp:
            config = json.load(fp)
    except FileNotFoundError:
        # Fall back to default configuration if file not found
        config = {'debug': False, 'timeout': 30}
    return config
```

**Agent-Optimized (Lower token cost, same logic):**
```python
class ConfigError(Exception):
    pass

def load_config(path: str = None) -> dict:
    path = path or 'config.json'
    try:
        with open(path) as fp:
            return json.load(fp)
    except FileNotFoundError:
        return {'debug': False, 'timeout': 30}
```
