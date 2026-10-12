# Skills MCP Server

[![M8ven Score](https://m8ven.ai/badge/mcp/rajpreetcodes/skills_mcp_server)](https://m8ven.ai/mcp/rajpreetcodes/skills_mcp_server)

An MCP (Model Context Protocol) server that exposes your Claude Skills library as a discoverable, searchable, and composable skill registry. Designed for seamless integration with **Tasklet** (via HTTP/SSE) and local MCP hosts like **OpenCode**, **Claude Desktop**, and **Cursor** (via STDIO).

## Background and Motivation

AI agent environments like Tasklet require configuring custom skills and prompts manually through their UI, typically one skill at a time. When managing a rich personal library of 100 to 200+ specialized engineering skills, adding them individually by hand is tedious, slow, and impossible to maintain as instructions evolve.

Furthermore, dumping dozens of skills directly into an agent's static context or system prompt wastes thousands of tokens per turn and causes prompt dilution.

This MCP server was built to eliminate that bottleneck:

1. **Zero Manual Copy-Pasting**: Point the server at your existing local skills folder and all skills are immediately available.
2. **On-Demand Retrieval**: Models dynamically search (`search_skills`) and load (`get_skill`) only the relevant skill instructions when a task calls for them, keeping context windows lean.
3. **Universal Portability**: By implementing the standard Model Context Protocol (MCP SDK 2.2.0), the same local skills library can be accessed across Tasklet, Claude Desktop, Claude.ai Web, Cursor, Windsurf, Zed, and CLI agents.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
                        SKILL SOURCE (Canonical)
                 Local Skills Directory (~/.claude/skills)
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
       ┌─────────────┐                   ┌─────────────┐
       │  LOCAL MODE │                   │ REMOTE MODE │
       │  (STDIO)    │                   │  (HTTP+SSE) │
       └──────┬──────┘                   └──────┬──────┘
              │                                 │
       ┌──────┴──────┐                   ┌──────┴──────┐
       ▼             ▼                   ▼             ▼
   OpenCode    Claude Desktop        Tasklet      Other MCP
   Cursor      Other Local           Cloud         Hosts
   Hosts       Hosts                 Agent
```

## Features

- **Dynamic Discovery**: Automatically finds all skills in your skills directory
- **Smart Search**: Natural language search across names, descriptions, tags, triggers, and categories
- **Multi-Skill Loading**: Retrieve multiple skills at once for complex tasks
- **Profiles/Bundles**: Composable skill profiles for common workflows (product-builder, senior-engineer, researcher, designer)
- **MCP Native**: Full support for Tools, Resources, and Prompts
- **Dual Transport**: STDIO for local, HTTP+SSE for remote (Tasklet)
- **Secure**: Optional Bearer token auth for remote deployments
- **No Duplication**: Reads your existing skills in-place; no copying required

## Configuring Your Skills Directory

You can point the server to any local directory containing skills:

- **Windows**: `C:\Users\<username>\.claude\skills` or `D:\projects\my-skills`
- **macOS**: `/Users/<username>/.claude/skills`
- **Linux**: `/home/<username>/.claude/skills`

There are three ways to configure your skills path:

1. **Command Line Flag** (simplest):
   ```bash
   python -m src.server --skill-root "path/to/your/skills"
   ```

2. **Configuration File** (`config.json`):
   ```json
   {
     "skill_root": "/path/to/your/skills",
     "profile_dir": "profiles",
     "port": 8080
   }
   ```

3. **Environment Variable** (`.env` or shell):
   ```bash
   export SKILL_ROOT="/path/to/your/skills"
   ```

---

## Client Setup

### 1. Claude Desktop (Local STDIO)

Add to `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "skills": {
      "command": "python",
      "args": [
        "-m", "src.server",
        "--transport", "stdio",
        "--skill-root", "C:\\Users\\<username>\\.claude\\skills"
      ],
      "cwd": "L:\\My Innovations\\Skills_MCP_Server"
    }
  }
}
```

Restart Claude Desktop. All 10 skills tools are immediately available in chats.

---

### 2. Claude Browser Version (Claude.ai Web)

Because Claude.ai runs in the cloud, it cannot directly reach `localhost:8080` on your physical workstation. Connect it via a secure SSE tunnel:

**Step 1: Start the HTTP server pointing to your skills folder**
```bash
cd L:\My Innovations\Skills_MCP_Server
python -m src.server --transport http --host 0.0.0.0 --port 8080 --skill-root "C:\Users\<username>\.claude\skills"
```

**Step 2: Expose the server to the internet using an SSH tunnel**
Run in a separate terminal:
```bash
ssh -R 80:localhost:8080 tinyfi.sh
```
*(Alternatively, use `ngrok http 8080` or Cloudflare Tunnel).*
This outputs a public URL: `https://<tunnel-id>.tinyfi.sh`.

**Step 3: Connect inside Claude.ai (Browser)**
1. Open [Claude.ai](https://claude.ai) in your browser.
2. Go to **Settings -> Integrations / Connectors** (or MCP settings).
3. Click **Add Remote MCP Server**.
4. Fill in the connection settings:
   - **Name**: `my-skills`
   - **Transport**: `SSE`
   - **URL**: `https://<tunnel-id>.tinyfi.sh/mcp/sse`
   - **Authorization Header**: `Bearer <AUTH_TOKEN>` (if auth is enabled)
5. Save. Claude in your web browser now has direct access to your local skills library.

---

### 3. Cursor

In Cursor **Settings -> Features -> MCP -> Add New MCP Server**:
- **Type**: `command`
- **Command**: `python -m src.server --transport stdio --skill-root "/path/to/skills"`
- **Working Directory**: `/path/to/Skills_MCP_Server`

---

### 4. Windsurf IDE Setup

Windsurf connects to Skills MCP Server over STDIO or HTTP/SSE using its Cascade AI assistant.

#### Configuration File Location
Windsurf stores MCP server configurations in `mcp_config.json`:
- **macOS / Linux**: `~/.codeium/windsurf/mcp_config.json`
- **Windows**: `%USERPROFILE%\.codeium\windsurf\mcp_config.json` (e.g. `C:\Users\<username>\.codeium\windsurf\mcp_config.json`)

To open or edit this file in Windsurf:
1. Open the Command Palette (`Cmd+Shift+P` on macOS, `Ctrl+Shift+P` on Windows/Linux).
2. Run **Windsurf: Configure MCP Servers** (or click the **hammer/plug icon** in the Cascade panel and select **Configure** / **View raw config**).
3. If the directory or file does not exist, create the `.codeium/windsurf/` directory and `mcp_config.json` file.

#### STDIO Configuration Example (Recommended)

Add Skills MCP Server under the top-level `"mcpServers"` key using your virtual environment Python:

**macOS / Linux (`~/.codeium/windsurf/mcp_config.json`):**
```json
{
  "mcpServers": {
    "skills": {
      "command": "/path/to/Skills_MCP_Server/.venv/bin/python",
      "args": [
        "-m",
        "src.server",
        "--transport",
        "stdio",
        "--skill-root",
        "/path/to/skills"
      ],
      "cwd": "/path/to/Skills_MCP_Server",
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

**Windows (`%USERPROFILE%\.codeium\windsurf\mcp_config.json`):**
```json
{
  "mcpServers": {
    "skills": {
      "command": "C:\\path\\to\\Skills_MCP_Server\\.venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "src.server",
        "--transport",
        "stdio",
        "--skill-root",
        "C:\\Users\\<username>\\.claude\\skills"
      ],
      "cwd": "C:\\path\\to\\Skills_MCP_Server",
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

> **Windows Path Notes:**
> - In JSON strings, Windows backslashes must be escaped with double backslashes (`C:\\path\\to\\...`) or written with forward slashes (`C:/path/to/...`).
> - Point to the virtual environment binary at `.venv\Scripts\python.exe`.
> - Always specify `"cwd"` pointing to your cloned `Skills_MCP_Server` repository root so Python can resolve the `src` package.

#### Remote HTTP / SSE Option

If running the standalone HTTP server (`python -m src.server --transport http --port 8080`), connect via Windsurf's `serverUrl` field:
```json
{
  "mcpServers": {
    "skills": {
      "serverUrl": "http://localhost:8080/mcp/sse"
    }
  }
}
```

#### Reload & Verify Connection
1. Save `mcp_config.json`.
2. In the Cascade panel, click the **Refresh** button next to MCP servers (or restart Windsurf).
3. Confirm that `skills` shows a green connected status indicator.
4. Test with Cascade in chat: *"List available skills using list_skills"* or check the tools list to see all 10 MCP tools.

---

### 5. Zed Editor Setup

Zed integrates MCP servers via its Assistant panel using the `context_servers` setting.

#### Configuration File Location
Zed stores settings in `settings.json`:
- **Linux & macOS**: `~/.config/zed/settings.json` (or `~/.zed/settings.json` on macOS)
- **Windows**: `%APPDATA%\Zed\settings.json` (e.g. `C:\Users\<username>\AppData\Roaming\Zed\settings.json`)

To open this file in Zed:
1. Open the Command Palette (`Cmd+Shift+P` on macOS, `Ctrl+Shift+P` on Windows/Linux).
2. Type and run **`zed: open settings`** (or press `Cmd-,` on macOS, `Ctrl-,` on Windows/Linux).
3. If creating a new file, initialize it with `{}`.

#### Preserving Existing Settings (Merge Guide)
Do **not** overwrite your existing `settings.json`. Instead, add or merge the `"context_servers"` object into your configuration.

**macOS / Linux (`~/.config/zed/settings.json`):**
```json
{
  "context_servers": {
    "skills": {
      "command": "/path/to/Skills_MCP_Server/.venv/bin/python",
      "args": [
        "-m",
        "src.server",
        "--transport",
        "stdio",
        "--skill-root",
        "/path/to/skills"
      ],
      "env": {
        "PYTHONPATH": "/path/to/Skills_MCP_Server"
      }
    }
  }
}
```

**Windows (`%APPDATA%\Zed\settings.json`):**
```json
{
  "context_servers": {
    "skills": {
      "command": "C:\\path\\to\\Skills_MCP_Server\\.venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "src.server",
        "--transport",
        "stdio",
        "--skill-root",
        "C:\\Users\\<username>\\.claude\\skills"
      ],
      "env": {
        "PYTHONPATH": "C:\\path\\to\\Skills_MCP_Server"
      }
    }
  }
}
```

**Merged Example with Pre-Existing Settings:**
```json
{
  "theme": "One Dark",
  "ui_font_size": 16,
  "context_servers": {
    "skills": {
      "command": "/path/to/Skills_MCP_Server/.venv/bin/python",
      "args": [
        "-m",
        "src.server",
        "--transport",
        "stdio",
        "--skill-root",
        "/path/to/skills"
      ],
      "env": {
        "PYTHONPATH": "/path/to/Skills_MCP_Server"
      }
    }
  }
}
```

> **Why `PYTHONPATH` in Zed?**
> Unlike Windsurf, Zed's `context_servers` schema does not include a `cwd` (working directory) property. Setting `"PYTHONPATH"` in the `"env"` block ensures Python can locate and import the `src` package regardless of the project folder opened in Zed. Alternatively, install the package in editable mode (`pip install -e .` inside `.venv`).

#### Remote HTTP / SSE Option in Zed

If running the standalone HTTP/SSE server:
```json
{
  "context_servers": {
    "skills": {
      "url": "http://localhost:8080/mcp/sse"
    }
  }
}
```

#### Reload & Verify Connection
1. Save `settings.json` (Zed automatically hot-reloads configuration files upon saving).
2. Open the Assistant panel (`Cmd-Alt-B` on macOS, `Ctrl-Alt-B` on Windows/Linux, or click the speech bubble in the right dock).
3. If Zed displays a **Worktree Trust** prompt for local MCP server execution, select **Trust** to authorize the server.
4. Verify server status under **Settings -> AI -> MCP Servers** (`agent: open settings` in the Command Palette).
5. In the Assistant conversation, test by asking: *"Use the list_skills tool to search available skills."*

---

### 6. Antigravity IDE / Gemini IDE

Add to your workspace `mcp_config.json`:
```json
{
  "mcpServers": {
    "skills": {
      "command": "python",
      "args": ["-m", "src.server", "--transport", "stdio", "--skill-root", "C:\\path\\to\\skills"],
      "cwd": "L:\\My Innovations\\Skills_MCP_Server"
    }
  }
}
```

---

### Cross-Platform Troubleshooting

When configuring Skills MCP Server across editors (Windsurf, Zed, Claude Desktop, Cursor), refer to the following common issues and resolutions:

#### 1. Windows Paths vs. Linux/macOS Paths
- **JSON Escape Sequences**: In JSON string values on Windows, single backslashes are interpreted as escape characters. Always escape backslashes with double backslashes (e.g. `"C:\\Users\\user\\Skills_MCP_Server"`) or use forward slashes (`"C:/Users/user/Skills_MCP_Server"`).
- **Tilde Expansion**: Paths containing `~` (e.g. `~/.venv/bin/python`) are not expanded by JSON parsers. Always specify full absolute paths (e.g. `/home/username/Skills_MCP_Server/...` or `/Users/username/...`).

#### 2. Python Executables, Virtual Environments, and Missing Dependencies
- **System Python vs. Virtual Environment**: Point directly to the virtual environment Python executable:
  - Linux / macOS: `/path/to/Skills_MCP_Server/.venv/bin/python`
  - Windows: `C:\path\to\Skills_MCP_Server\.venv\Scripts\python.exe`
- **Missing Module Errors (`No module named 'mcp'`)**: Occurs when dependencies are not installed in the target Python environment. Run:
  ```bash
  cd /path/to/Skills_MCP_Server
  source .venv/bin/activate       # On Windows: .venv\Scripts\activate
  pip install -e .
  ```

#### 3. Spaces in Paths and JSON Escaping
- If your path contains spaces (e.g. `C:\Users\John Doe\Skills_MCP_Server` or `L:\My Innovations\...`), write it plainly within JSON strings: `"C:\\Users\\John Doe\\Skills_MCP_Server"`.
- Do **not** wrap arguments with additional shell quotes inside JSON strings (e.g., use `"--skill-root", "C:\\My Skills"` instead of `"--skill-root", "\"C:\\My Skills\""`).

#### 4. Invalid JSON or Misplaced Configuration Keys
- **Schema Differences**:
  - Windsurf, Claude Desktop, Cursor, and Antigravity use top-level key **`"mcpServers"`**.
  - Zed uses top-level key **`"context_servers"`**.
- **JSON Syntax Errors**: Ensure there are no trailing commas before closing braces (`}`) or brackets (`]`), and verify that all keys and strings are enclosed in double quotes.

#### 5. Incorrect Working Directories and Script Paths
- The entry point `-m src.server` requires Python to resolve the `src` package directory.
- In Windsurf and Claude Desktop: always set `"cwd": "/path/to/Skills_MCP_Server"`.
- In Zed (which does not have a `cwd` key): set `"env": { "PYTHONPATH": "/path/to/Skills_MCP_Server" }` or run `pip install -e .`.

#### 6. Unsupported Transports, Failed Connections, and Server Startup Errors
- **Protocol**: Skills MCP Server implements STDIO and Server-Sent Events (SSE). It does not support Streamable HTTP POST RPC.
- **SSE URL**: When using remote transport in Windsurf or Zed, point to the SSE endpoint: `http://localhost:8080/mcp/sse`.
- **Garbled STDIO Frames**: Do not add print statements to `stdout` in server code; MCP protocol frames require clean standard I/O. All logging in Skills MCP Server is routed to `stderr`.

#### 7. Reloading Editors and Checking Available MCP Tools
- **Windsurf**: Click the hammer/refresh icon in the Cascade panel, or restart Windsurf.
- **Zed**: Save `settings.json` (auto-reloads), or restart via Command Palette (`zed: restart`). Ensure worktree trust is granted.
- **Verify Tools**: When connected, verify that all 10 MCP tools (`list_skills`, `search_skills`, `get_skill`, `get_skills`, `list_profiles`, `get_profile`, `resolve_profile`, `refresh_skills`, `get_categories`, `get_skill_stats`) appear in your editor's tool list.

---

## Claude Code CLI Setup

Connect [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview) to Skills MCP Server to give the CLI agent full access to your personal skills library, profiles, and prompts. Both **STDIO** (local process) and **HTTP/SSE** (remote/persistent daemon) transports are supported.

### Prerequisites

1. **Python**: Python `>= 3.10` is required. Verify your version:
   ```bash
   python3 --version
   ```
2. **Claude Code CLI**: Installed and authenticated:
   ```bash
   npm install -g @anthropic-ai/claude-code
   claude --version
   ```
3. **Repository Setup**: Clone this repository and install its dependencies in a virtual environment:
   ```bash
   git clone https://github.com/rajpreetcodes/Skills_MCP_Server.git
   cd Skills_MCP_Server
   python3 -m venv .venv
   source .venv/bin/activate       # On Windows: .venv\Scripts\activate
   pip install -e .
   ```
   *(Required dependencies from `pyproject.toml`: `mcp[cli]>=2.2.0`, `fastapi>=0.141.0`, `uvicorn>=0.53.0`, `python-dotenv>=1.1.0`, `pyyaml>=6.0`)*
4. **Skills Directory**: Have a directory containing your skills library (e.g., `~/.claude/skills` on macOS/Linux or `C:\Users\<username>\.claude\skills` on Windows).
5. **Configuration (Optional)**: Set custom options in `config.json` or via environment variables (`SKILL_ROOT`, `PROFILE_DIR`, `AUTH_TOKEN`, `PORT`).

### Option A: STDIO Transport

**When to use STDIO**: Recommended for local development when Claude Code runs on the same machine as your skills library. Claude Code launches the server as a child process and communicates directly over standard input/output. No background daemon or open network port is required, and Claude Code manages the server process lifecycle automatically.

#### 1. CLI Registration Command

Run `claude mcp add` using the `--transport stdio` flag. The double dash (`--`) separates Claude Code options from the Python server command:

```bash
# From anywhere (replace with your actual paths):
claude mcp add --transport stdio skills \
  -- /path/to/Skills_MCP_Server/.venv/bin/python -m src.server \
  --transport stdio \
  --skill-root /path/to/skills
```

*Windows (PowerShell / CMD):*
```powershell
claude mcp add --transport stdio skills -- C:\path\to\Skills_MCP_Server\.venv\Scripts\python.exe -m src.server --transport stdio --skill-root C:\Users\<username>\.claude\skills
```

*From the repository root:*
```bash
cd /path/to/Skills_MCP_Server
claude mcp add --transport stdio skills -- python -m src.server --transport stdio --skill-root /path/to/skills
```

> **Configuration Details:**
> - **Python executable**: Point directly to your virtual environment Python binary (`.venv/bin/python` or `.venv\Scripts\python.exe`) so installed dependencies are used.
> - **Entry point**: `-m src.server` runs the main server entry point.
> - **Arguments**: `--transport stdio` specifies STDIO mode; `--skill-root` sets your skills folder (overrides default).
> - **Scope options**: By default, registration applies locally to the current project (`~/.claude.json`). Add `--scope user` to make skills available across all projects, or `--scope project` to save to `.mcp.json` in the current project root.

#### 2. Manual Configuration File Example

Alternatively, add the server definition directly to `~/.claude.json` (user scope) or `.mcp.json` (project scope):

```json
{
  "mcpServers": {
    "skills": {
      "type": "stdio",
      "command": "/path/to/Skills_MCP_Server/.venv/bin/python",
      "args": [
        "-m",
        "src.server",
        "--transport",
        "stdio",
        "--skill-root",
        "/path/to/skills"
      ],
      "cwd": "/path/to/Skills_MCP_Server"
    }
  }
}
```

*Windows configuration:*
```json
{
  "mcpServers": {
    "skills": {
      "type": "stdio",
      "command": "C:\\path\\to\\Skills_MCP_Server\\.venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "src.server",
        "--transport",
        "stdio",
        "--skill-root",
        "C:\\Users\\<username>\\.claude\\skills"
      ],
      "cwd": "C:\\path\\to\\Skills_MCP_Server"
    }
  }
}
```

> **Note on `cwd`**: Specifying `"cwd"` pointing to the `Skills_MCP_Server` directory ensures Python can resolve the `src` package.

### Option B: HTTP Transport

**When to use HTTP**: Recommended when running the server on a remote host, inside Docker, or as a persistent daemon accessible simultaneously across multiple MCP clients (such as Claude Code CLI and Tasklet).

> **Protocol Note:** Skills MCP Server implements the **Server-Sent Events (SSE)** protocol via `mcp.server.sse.SseServerTransport`. The MCP endpoint is `/mcp/sse`. It does not support Streamable HTTP.

#### 1. Start the Server

From the repository root, start the server in HTTP mode:

```bash
cd /path/to/Skills_MCP_Server
source .venv/bin/activate

# Local development (no authentication)
python -m src.server --transport http --host 0.0.0.0 --port 8080 --skill-root /path/to/skills
```

If securing the server with a Bearer token (recommended for remote or shared deployments):
```bash
export AUTH_TOKEN="your-secure-token-here"
python -m src.server --transport http --host 0.0.0.0 --port 8080 --skill-root /path/to/skills
```

Verify that the server is up and running:
```bash
curl http://localhost:8080/health
# Response: {"status":"healthy","skills":...,"profiles":4,"version":"0.1.0"}
```

#### 2. Register in Claude Code CLI

Register the SSE endpoint (`/mcp/sse`) with Claude Code:

```bash
# Standard registration (no auth)
claude mcp add --transport sse skills http://localhost:8080/mcp/sse
```

*With Bearer token authentication:*
```bash
claude mcp add --transport sse skills http://localhost:8080/mcp/sse --header "Authorization: Bearer your-secure-token-here"
```

*(Note: In Claude Code v2.1.265+, `--transport http skills http://localhost:8080/mcp/sse` also automatically negotiates the SSE transport).*

#### 3. Manual Configuration File Example

If using `~/.claude.json` or `.mcp.json`:

```json
{
  "mcpServers": {
    "skills": {
      "type": "sse",
      "url": "http://localhost:8080/mcp/sse"
    }
  }
}
```

*With authentication header:*
```json
{
  "mcpServers": {
    "skills": {
      "type": "sse",
      "url": "http://localhost:8080/mcp/sse",
      "headers": {
        "Authorization": "Bearer your-secure-token-here"
      }
    }
  }
}
```

### Verify the Connection

Follow these steps to confirm your connection and diagnose any potential configuration issues.

#### 1. Inspect Server Status via CLI

List registered MCP servers to verify connection status:
```bash
claude mcp list
```
Expected output confirms the server is connected:
```text
skills: ... - ✓ Connected
```

Inspect detailed server settings:
```bash
claude mcp get skills
```

#### 2. Verify in an Interactive Claude Code Session

Start a Claude Code session:
```bash
claude
```

Inside the session, run the `/mcp` command:
```text
/mcp
```
Verify that `skills` appears active and exposes all 10 MCP tools:
- `list_skills` — Browse skill catalog with pagination and category filters
- `search_skills` — Natural language search across skills and tags
- `get_skill` / `get_skills` — Retrieve full skill instructions
- `list_profiles` / `get_profile` / `resolve_profile` — Manage and resolve skill bundles
- `refresh_skills` — Reload skill registry after adding new skills
- `get_categories` / `get_skill_stats` — Taxonomy and registry statistics

Test the integration in chat:
```text
Can you search my skills for "python" using the search_skills tool?
```

#### 3. Troubleshooting Common Issues

| Issue / Error | Cause | Solution |
|---------------|-------|----------|
| `ModuleNotFoundError: No module named 'mcp'` (STDIO) | Virtual environment is not used or dependencies are missing | Specify the full path to your virtualenv Python binary: `/path/to/Skills_MCP_Server/.venv/bin/python`. Ensure dependencies are installed via `pip install -e .`. |
| `ModuleNotFoundError: No module named 'src'` (STDIO) | Python ran outside the repository directory | Add `"cwd": "/path/to/Skills_MCP_Server"` in your JSON configuration or pass `--env PYTHONPATH=/path/to/Skills_MCP_Server` when registering. |
| Server status shows `Failed to connect` (STDIO) | Invalid Python or skills path | Verify that the Python executable exists, is executable, and `--skill-root` points to an existing directory. |
| Server status shows `Failed to connect` (HTTP) | Server process is not running or incorrect URL | Check if the server is running with `curl http://localhost:8080/health`. Ensure the URL includes `/mcp/sse` (e.g. `http://localhost:8080/mcp/sse`). |
| `401 Unauthorized` or `403 Forbidden` (HTTP) | Missing or mismatched Bearer token | Ensure the token passed in `--header "Authorization: Bearer <token>"` matches `AUTH_TOKEN` on the server. |
| `Use SSE endpoint for MCP` error | Client contacted `/mcp/rpc` with standard HTTP POST | Use `--transport sse` and point to `http://localhost:8080/mcp/sse`. |
| `No skills found` returned by tools | Skills folder is empty or improperly structured | Ensure `--skill-root` contains folders with valid `SKILL.md` files (see [Adding Skills](#adding-skills)). |

To remove and re-register the server at any time:
```bash
claude mcp remove skills
```

---

## MCP Capabilities

### Tools

| Tool | Purpose |
|------|---------|
| `list_skills` | Browse skill catalog with pagination & category filter |
| `search_skills` | Natural language search for relevant skills |
| `get_skill` | Load full instructions for a single skill |
| `get_skills` | Batch load multiple skills efficiently |
| `list_profiles` | List available skill profiles/bundles |
| `get_profile` | View profile definition and resolved skills |
| `resolve_profile` | Get flat list of skill IDs from a profile (supports stages) |
| `refresh_skills` | Reload registry after adding/removing skills |
| `get_categories` | List all skill categories |
| `get_skill_stats` | Registry statistics |

### Resources

| URI Pattern | Description |
|-------------|-------------|
| `skill://list` | Complete skill catalog as JSON |
| `skill://categories` | All categories with counts |
| `skill://{skill-id}` | Full skill content as Markdown |
| `skill://{skill-id}/{file}` | Supporting files (references, data) |

### Prompts

| Prompt | Purpose |
|--------|---------|
| `activate_skill` | Load single skill with optional context |
| `activate_skills` | Load multiple skills with clear boundaries |
| `activate_profile` | Load entire profile (resolves nested profiles) |
| `suggest_skills` | Get AI recommendations for a task description |

## Usage Examples

### Agent Workflow: "Design a polished SaaS dashboard"

```python
# 1. Agent searches for relevant skills
results = search_skills("design polished dashboard ui ux")
# → Returns: ui-ux-pro-max, impeccable, choosing-design-styles, design-consultation

# 2. Agent loads top matches
skills = get_skills(["ui-ux-pro-max.ui-ux-pro-max", "impeccable.impeccable", ...])
# → Returns full instructions for each skill, clearly separated

# 3. Agent applies combined expertise to the task
```

### Agent Workflow: "Build a secure production API"

```python
# Use profile for structured workflow
profile = resolve_profile("senior-engineer")
# → Returns: [investigate, diagnose, plan-eng-review, ponytail, tdd, review, cso, ...]

# Or load specific stages
research_skills = resolve_profile("product-builder", stage="research")
impl_skills = resolve_profile("product-builder", stage="implementation")
```

### Using Profiles

```yaml
# profiles/product-builder.yaml
name: product-builder
stages:
  research:
    - research
    - research-deep
  design:
    - ui-ux-pro-max
    - impeccable
  implementation:
    - ponytail
    - tdd
  validation:
    - qa
    - review
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SKILL_ROOT` | Path to skills directory | `C:\Users\rajpr\.claude\skills` |
| `PROFILE_DIR` | Profiles directory | `profiles` |
| `TRANSPORT` | `stdio` or `http` | `stdio` |
| `HOST` | HTTP bind address | `0.0.0.0` |
| `PORT` | HTTP port | `8080` |
| `LOG_LEVEL` | Log level | `INFO` |
| `AUTH_TOKEN` | Bearer token for HTTP auth | (none) |

### Config File (`config.json`)

```json
{
  "skill_root": "C:\\Users\\rajpr\\.claude\\skills",
  "profile_dir": "profiles",
  "transport": "stdio",
  "host": "0.0.0.0",
  "port": 8080,
  "log_level": "INFO",
  "auth_token": null
}
```

## Adding Skills

Simply add a new directory under `C:\Users\rajpr\.claude\skills\` with a `SKILL.md` file:

```
skills/
  my-new-skill/
    SKILL.md          # Required: frontmatter + instructions
    references/       # Optional: supporting files
      guide.md
      data.json
```

Then call `refresh_skills` tool or restart the server.

**Skill Frontmatter Example:**

```yaml
---
name: my-skill
description: What this skill does
category: ui-ux
version: "1.0.0"
tags: [design, components]
triggers: ["design a button", "create component"]
allowed-tools: [Read, Write, Bash]
license: MIT
---
# My Skill

Instructions here...
```

## Adding Profiles

Create a YAML file in `profiles/`:

```yaml
# profiles/my-workflow.yaml
name: my-workflow
description: My custom workflow
skills:
  - skill-one
  - skill-two
profiles:
  - other-profile  # Nested profile
stages:
  phase1:
    - skill-one
  phase2:
    - skill-two
```

## Remote Deployment Architecture

### For Tasklet (Cloud)

Since Tasklet runs in the cloud, it cannot access your local Windows filesystem. The remote server must have access to the skill content.

**Recommended Approach:**

1. **Git-backed skills**: Push `C:\Users\rajpr\.claude\skills` to a private Git repo
2. **CI/CD sync**: On push, CI builds Docker image with skills embedded OR deploys to server that clones the repo
3. **Server mounts**: Docker volume or persistent disk with skills content

```
Git Repo (skills) → CI/CD → Docker Image → Cloud Run / K8s / VM
                                                    ↓
                                              Tasklet connects
```

**Docker with Embedded Skills:**

```dockerfile
# In Dockerfile, copy skills at build time
COPY skills/ /skills/
```

**Or Runtime Sync (for frequent updates):**

```bash
# In container startup script
git clone https://github.com/you/skills.git /skills
# Then run server with SKILL_ROOT=/skills
```

### Authentication

**Always use `AUTH_TOKEN` for remote deployments:**

```bash
# Generate secure token
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set in environment
export AUTH_TOKEN="generated-token-here"
```

Tasklet connection must include: `Authorization: Bearer <token>`

## Testing

```bash
# Run all tests
cd L:\My Innovations\Skills_MCP_Server
pytest tests/ -v

# Run specific test file
pytest tests/test_registry.py -v
pytest tests/test_search.py -v
pytest tests/test_profiles.py -v
pytest tests/test_server.py -v
```

## MCP Inspector Validation

```bash
# Install inspector
npm install -g @modelcontextprotocol/inspector

# Test STDIO mode
npx @modelcontextprotocol/inspector python -m src.server --transport stdio

# Test HTTP mode (in separate terminal)
python -m src.server --transport http --port 8080
# Then in inspector: connect to http://localhost:8080/mcp/sse
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No skills found" | Check `SKILL_ROOT` path exists and has `SKILL.md` files |
| "Connection refused" | Verify server is running, port accessible, firewall allows traffic |
| "401 Unauthorized" | Check `AUTH_TOKEN` matches in server env and connection headers |
| "Skill not found" | Run `refresh_skills` tool after adding skills |
| "Circular dependency" | Check profile YAML for circular `profiles:` references |
| STDIO: garbled output | Ensure no `print()` to stdout; all logging goes to stderr |

## Security Considerations

- **Never expose HTTP without auth** in production
- **Use HTTPS** behind reverse proxy (nginx, Caddy, Cloudflare Tunnel)
- **Built-in Rate Limiting**: In HTTP mode, configurable sliding-window rate limiting (`RATE_LIMIT_ENABLED`, `RATE_LIMIT_PER_MINUTE`) protects endpoints against denial-of-service attempts
- **Restrict network access** to authorized client IPs only
- **Read-only skill mount** (`:ro` in Docker)
- **No arbitrary code execution**: server only reads skill files

## Privacy

Skills MCP Server is a local-first engineering tool. It contains zero tracking, zero telemetry, and zero remote analytics. All skill indexing, search queries, and prompt resolutions execute strictly in local process memory on your machine. For complete details, see [PRIVACY.md](PRIVACY.md).

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details. Individual skill files retain their respective author licenses in their corresponding directories.