# Module 5: MCP - Model Context Protocol Integration

**Duration:** 3-4 hours
**Difficulty:** Advanced
**Prerequisites:** Modules 1-4 completed

## Learning Objectives

By the end of this module, you will be able to:

- ✅ Understand Model Context Protocol (MCP) architecture
- ✅ Create custom MCP servers for external tools
- ✅ Integrate MCP servers with Claude and LLM applications
- ✅ Build SPICE simulation integration via MCP
- ✅ Create component database MCP servers
- ✅ Connect multiple data sources through MCP
- ✅ Debug and troubleshoot MCP connections
- ✅ Deploy production MCP servers

## What is MCP?

**Model Context Protocol (MCP)** is an open protocol developed by Anthropic that standardizes how AI applications connect to external data sources and tools.

### The Problem MCP Solves

Before MCP, each integration required custom code:

```python
# Without MCP - Custom integration for each tool
def use_spice_simulator(circuit):
    # Custom SPICE integration code...

def query_database(query):
    # Custom database code...

def fetch_datasheet(part):
    # Custom API code...
```

**Problems:**
- ❌ No standardization
- ❌ Difficult to maintain
- ❌ Hard to share integrations
- ❌ Each developer reinvents the wheel

### The MCP Solution

MCP provides a **standardized protocol** for connecting AI to tools:

```python
# With MCP - Standardized protocol
mcp_client.connect_to_server("spice-simulator")
mcp_client.call_tool("simulate_circuit", params)

mcp_client.connect_to_server("component-database")
mcp_client.call_tool("search_component", params)
```

**Benefits:**
- ✅ Standardized interface
- ✅ Easy to implement
- ✅ Shareable servers
- ✅ Ecosystem of tools

---

## MCP Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     MCP ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │            AI APPLICATION (Claude, GPT-4)               │   │
│  │  • Understands natural language                         │   │
│  │  • Decides which tools to use                           │   │
│  │  • Processes tool results                               │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                         │                                       │
│                         │ MCP Protocol                          │
│                         │                                       │
│  ┌──────────────────────▼──────────────────────────────────┐   │
│  │                  MCP CLIENT                              │   │
│  │  • Manages server connections                           │   │
│  │  • Routes tool calls                                    │   │
│  │  • Handles protocol communication                       │   │
│  └──────────────────────┬──────────────────────────────────┘   │
│                         │                                       │
│         ┌───────────────┼───────────────┐                      │
│         │               │               │                      │
│  ┌──────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐               │
│  │MCP SERVER 1 │ │MCP SERVER 2│ │MCP SERVER 3│               │
│  │  (SPICE)    │ │(Component  │ │(Datasheet  │               │
│  │             │ │ Database)  │ │   API)     │               │
│  └──────┬──────┘ └─────┬──────┘ └─────┬──────┘               │
│         │              │              │                        │
│  ┌──────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐               │
│  │  LTspice    │ │  ChromaDB  │ │  HTTP API  │               │
│  │  Simulator  │ │  Vector DB │ │  Service   │               │
│  └─────────────┘ └────────────┘ └────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

1. **MCP Client**: Application that connects to MCP servers
2. **MCP Server**: Provides tools and resources via MCP protocol
3. **Tools**: Functions that the AI can call
4. **Resources**: Data sources the AI can access
5. **Prompts**: Templates the server can provide

---

## MCP Protocol Basics

### Server Capabilities

MCP servers can expose three types of capabilities:

#### 1. Tools (Functions)
Functions the AI can execute:

```python
{
  "name": "simulate_circuit",
  "description": "Run SPICE simulation on a circuit",
  "parameters": {
    "circuit_netlist": {"type": "string"},
    "analysis_type": {"type": "string"}
  }
}
```

#### 2. Resources (Data)
Data sources the AI can read:

```python
{
  "uri": "component://IRF540N",
  "name": "IRF540N Datasheet",
  "mimeType": "text/plain"
}
```

#### 3. Prompts (Templates)
Pre-defined prompt templates:

```python
{
  "name": "analyze_circuit",
  "description": "Analyze a power supply circuit",
  "arguments": ["circuit_type", "voltage", "current"]
}
```

---

## Exercise 5.1: Creating Your First MCP Server

### Basic MCP Server Structure

**Python (using mcp SDK):**

```python
from mcp.server import Server, Tool
from mcp.types import TextContent

# Create server
server = Server("power-electronics-tools")

# Define a tool
@server.tool()
async def calculate_resistor_power(
    voltage: float,
    current: float
) -> str:
    """Calculate power dissipation in a resistor."""
    power = voltage * current

    # Recommend power rating (2x safety factor)
    recommended = power * 2

    # Find standard rating
    standard_ratings = [0.125, 0.25, 0.5, 1, 2, 5, 10]
    rating = next((r for r in standard_ratings if r >= recommended), 10)

    result = f"""Power Calculation:
- Voltage: {voltage}V
- Current: {current}A
- Power: {power:.3f}W
- Recommended rating: {rating}W (2x safety factor)
"""
    return result

# Run server
if __name__ == "__main__":
    server.run()
```

### Installing MCP SDK

```bash
pip install mcp
```

### Running the Server

```bash
python mcp_server.py
```

---

## Exercise 5.2: MCP Client Integration

### Connecting to MCP Server

**Python:**

```python
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Initialize Claude client
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Connect to MCP server
server_params = StdioServerParameters(
    command="python",
    args=["mcp_server.py"]
)

async def use_mcp_tools():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize connection
            await session.initialize()

            # List available tools
            tools_list = await session.list_tools()
            print(f"Available tools: {tools_list}")

            # Use tool with Claude
            message = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                tools=tools_list.tools,
                messages=[{
                    "role": "user",
                    "content": "Calculate power for 5V at 100mA"
                }]
            )

            # Handle tool calls
            if message.stop_reason == "tool_use":
                for content in message.content:
                    if content.type == "tool_use":
                        # Call MCP tool
                        result = await session.call_tool(
                            content.name,
                            content.input
                        )
                        print(f"Tool result: {result}")
```

---

## Exercise 5.3: SPICE Simulation MCP Server

### Why SPICE + MCP?

**SPICE (Simulation Program with Integrated Circuit Emphasis)** is the industry standard for circuit simulation. Integrating SPICE with AI through MCP enables:

- ✅ AI-driven circuit analysis
- ✅ Automated design verification
- ✅ What-if scenario testing
- ✅ Natural language to simulation

### SPICE MCP Server

**File:** `examples/servers/spice_mcp_server.py`

```python
from mcp.server import Server
import subprocess
import tempfile
import os

server = Server("spice-simulator")

@server.tool()
async def simulate_circuit(
    netlist: str,
    analysis_type: str = "tran"
) -> str:
    """
    Run SPICE simulation on a circuit netlist.

    Args:
        netlist: SPICE netlist (complete circuit description)
        analysis_type: Type of analysis (tran, ac, dc, op)

    Returns:
        Simulation results as text
    """
    # Create temporary netlist file
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.cir',
        delete=False
    ) as f:
        f.write(netlist)
        netlist_file = f.name

    try:
        # Run ngspice (open-source SPICE)
        result = subprocess.run(
            ['ngspice', '-b', netlist_file],
            capture_output=True,
            text=True,
            timeout=30
        )

        return result.stdout

    except subprocess.TimeoutExpired:
        return "Error: Simulation timeout (>30s)"
    except FileNotFoundError:
        return "Error: ngspice not installed"
    finally:
        os.unlink(netlist_file)

@server.tool()
async def analyze_buck_converter(
    vin: float,
    vout: float,
    iout: float,
    freq: float = 100e3
) -> str:
    """
    Generate and simulate a buck converter circuit.

    Args:
        vin: Input voltage (V)
        vout: Output voltage (V)
        iout: Output current (A)
        freq: Switching frequency (Hz)

    Returns:
        Simulation results with efficiency estimate
    """
    # Calculate component values
    duty_cycle = vout / vin
    inductance = (vin - vout) * duty_cycle / (0.3 * iout * freq)
    capacitance = iout * (1 - duty_cycle) / (freq * 0.05 * vout)

    # Generate SPICE netlist
    netlist = f"""Buck Converter Simulation
Vin in 0 DC {vin}
L1 sw out {inductance*1e6}u
C1 out 0 {capacitance*1e6}u
Rload out 0 {vout/iout}
V_pulse gate 0 PULSE(0 10 0 1n 1n {duty_cycle/freq} {1/freq})
M1 sw gate in in NMOS_MODEL
D1 0 sw DIODE_MODEL

.model NMOS_MODEL NMOS(Vto=3 Kp=10)
.model DIODE_MODEL D(Is=1e-14)

.tran 0.1u 1m
.print tran v(out) i(Vin)
.end
"""

    result = await simulate_circuit(netlist, "tran")

    return f"""Buck Converter Analysis:
Input: {vin}V
Output: {vout}V @ {iout}A
Frequency: {freq/1000:.0f}kHz

Calculated Components:
- Inductor: {inductance*1e6:.1f}µH
- Capacitor: {capacitance*1e6:.1f}µF
- Duty Cycle: {duty_cycle*100:.1f}%

Simulation Results:
{result}
"""

if __name__ == "__main__":
    server.run()
```

**See:** `examples/servers/spice_mcp_server.py` for complete implementation.

---

## Exercise 5.4: Component Database MCP Server

### Exposing ChromaDB through MCP

**File:** `examples/servers/component_db_mcp_server.py`

```python
from mcp.server import Server, Resource
import chromadb
import json

server = Server("component-database")

# Initialize ChromaDB
db_client = chromadb.PersistentClient(path="./component_db")
collection = db_client.get_or_create_collection("components")

@server.tool()
async def search_components(
    query: str,
    n_results: int = 5,
    component_type: str = None
) -> str:
    """
    Search component database with natural language.

    Args:
        query: Search query (e.g., "MOSFET for 24V 10A motor")
        n_results: Number of results
        component_type: Filter by type (MOSFET, Regulator, etc.)

    Returns:
        JSON array of matching components
    """
    where_clause = {"component_type": component_type} if component_type else None

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where_clause
    )

    components = []
    for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
        components.append({
            "part_number": metadata.get("part_number"),
            "type": metadata.get("component_type"),
            "specs": doc
        })

    return json.dumps(components, indent=2)

@server.tool()
async def get_component_datasheet(part_number: str) -> str:
    """
    Retrieve complete datasheet for a component.

    Args:
        part_number: Component part number (e.g., "IRF540N")

    Returns:
        Complete datasheet text
    """
    try:
        result = collection.get(ids=[part_number])
        if result['documents']:
            return result['documents'][0]
        return f"Datasheet not found for {part_number}"
    except Exception as e:
        return f"Error: {str(e)}"

@server.resource("component://{part_number}")
async def get_component_resource(uri: str) -> str:
    """Expose components as MCP resources."""
    part_number = uri.split("//")[1]
    return await get_component_datasheet(part_number)

if __name__ == "__main__":
    server.run()
```

---

## Exercise 5.5: Enhanced Power Electronics Assistant with MCP

### Full Integration

**File:** `examples/assistant_with_mcp.py`

```python
import asyncio
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPEnhancedAssistant:
    """Power Electronics Assistant with MCP integration."""

    def __init__(self):
        self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.mcp_sessions = {}

    async def connect_mcp_server(self, name: str, command: str, args: list):
        """Connect to an MCP server."""
        server_params = StdioServerParameters(command=command, args=args)

        read, write = await stdio_client(server_params).__aenter__()
        session = ClientSession(read, write)
        await session.initialize()

        self.mcp_sessions[name] = session
        print(f"✅ Connected to MCP server: {name}")

    async def get_all_tools(self):
        """Gather tools from all connected MCP servers."""
        all_tools = []

        for name, session in self.mcp_sessions.items():
            tools_list = await session.list_tools()
            all_tools.extend(tools_list.tools)
            print(f"📦 Loaded {len(tools_list.tools)} tools from {name}")

        return all_tools

    async def chat(self, user_message: str):
        """Chat with assistant using MCP tools."""

        # Get all available tools
        tools = await self.get_all_tools()

        # Create Claude message
        messages = [{"role": "user", "content": user_message}]

        response = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            tools=tools,
            messages=messages
        )

        # Handle tool calls
        while response.stop_reason == "tool_use":
            # Process tool uses
            tool_results = []

            for content in response.content:
                if content.type == "tool_use":
                    # Find which server has this tool
                    result = await self._call_mcp_tool(
                        content.name,
                        content.input
                    )

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": result
                    })

            # Continue conversation with tool results
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                tools=tools,
                messages=messages
            )

        # Return final response
        return response.content[0].text

    async def _call_mcp_tool(self, tool_name: str, arguments: dict):
        """Call tool on appropriate MCP server."""
        for name, session in self.mcp_sessions.items():
            try:
                result = await session.call_tool(tool_name, arguments)
                return result.content[0].text
            except:
                continue

        return f"Error: Tool {tool_name} not found"

async def main():
    assistant = MCPEnhancedAssistant()

    # Connect to MCP servers
    await assistant.connect_mcp_server(
        "spice",
        "python",
        ["examples/servers/spice_mcp_server.py"]
    )

    await assistant.connect_mcp_server(
        "components",
        "python",
        ["examples/servers/component_db_mcp_server.py"]
    )

    # Use assistant with MCP tools
    response = await assistant.chat(
        "Simulate a buck converter: 12V input, 5V output, 2A load"
    )

    print(f"\n🤖 Assistant: {response}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## MCP Server Configuration

### Config File Format

**File:** `config/mcp_servers.json`

```json
{
  "mcpServers": {
    "spice-simulator": {
      "command": "python",
      "args": ["examples/servers/spice_mcp_server.py"],
      "description": "SPICE circuit simulation"
    },
    "component-database": {
      "command": "python",
      "args": ["examples/servers/component_db_mcp_server.py"],
      "description": "Component specification lookup"
    },
    "datasheet-api": {
      "command": "python",
      "args": ["examples/servers/datasheet_api_server.py"],
      "description": "Online datasheet retrieval"
    }
  }
}
```

### Loading Config

```python
import json

def load_mcp_config(config_file: str):
    """Load MCP server configuration."""
    with open(config_file, 'r') as f:
        config = json.load(f)
    return config['mcpServers']

async def connect_all_servers(config_file: str):
    """Connect to all configured MCP servers."""
    servers = load_mcp_config(config_file)

    for name, config in servers.items():
        await assistant.connect_mcp_server(
            name,
            config['command'],
            config['args']
        )
```

---

## Debugging MCP Connections

### Common Issues

**1. Server Not Starting**
```bash
# Test server directly
python examples/servers/spice_mcp_server.py

# Check for errors in output
```

**2. Tool Not Found**
```python
# List available tools
tools_list = await session.list_tools()
print([tool.name for tool in tools_list.tools])
```

**3. Communication Error**
```python
# Enable MCP logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

**4. Timeout Issues**
```python
# Increase timeout
result = subprocess.run(
    ['ngspice', '-b', netlist_file],
    timeout=60  # Increase from 30s
)
```

---

## Best Practices

### Security

1. **Input Validation**
```python
@server.tool()
async def simulate_circuit(netlist: str):
    # Validate input
    if len(netlist) > 10000:
        return "Error: Netlist too large"

    # Sanitize file paths
    if ".." in netlist or "/" in netlist:
        return "Error: Invalid characters"
```

2. **Sandboxing**
```python
# Run simulations in isolated environment
# Use Docker or virtual machines for untrusted code
```

3. **Rate Limiting**
```python
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=10, period=60)  # 10 calls per minute
async def simulate_circuit(netlist: str):
    # ...
```

### Performance

1. **Caching**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_component_datasheet(part_number: str):
    # Cache frequently accessed datasheets
```

2. **Async Operations**
```python
# Use async for I/O operations
async def fetch_datasheet(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.text()
```

3. **Connection Pooling**
```python
# Reuse database connections
db_pool = chromadb.PersistentClient(path="./db")
```

---

## Production Deployment

### Docker Container

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

# Install ngspice
RUN apt-get update && apt-get install -y ngspice

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy MCP server
COPY spice_mcp_server.py .

CMD ["python", "spice_mcp_server.py"]
```

### Systemd Service

**File:** `/etc/systemd/system/mcp-spice.service`

```ini
[Unit]
Description=MCP SPICE Simulator Server
After=network.target

[Service]
Type=simple
User=mcp
WorkingDirectory=/opt/mcp-servers
ExecStart=/usr/bin/python3 spice_mcp_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Real-World Applications

### 1. Design Automation

```python
# AI-driven circuit optimization
response = await assistant.chat("""
Optimize this buck converter for maximum efficiency:
- Input: 12V
- Output: 5V @ 3A
- Size constraint: <2cm²

Simulate multiple configurations and recommend best design.
""")
```

### 2. Interactive Learning

```python
# Educational circuit exploration
response = await assistant.chat("""
Explain how this RC filter works and show me the frequency response:

Vin ---[1kΩ]--- Vout
                 |
               [1µF]
                 |
                GND
""")
```

### 3. Troubleshooting

```python
# AI-assisted debugging
response = await assistant.chat("""
My buck converter output is 3.2V instead of 5V.
Input is 12V, load is 2A.
Simulate possible failure modes and suggest diagnosis.
""")
```

---

## Self-Assessment

Before moving to Module 6, ensure you can:

- [ ] Explain MCP architecture and benefits
- [ ] Create a basic MCP server with tools
- [ ] Connect MCP client to servers
- [ ] Integrate MCP with Claude API
- [ ] Build SPICE simulation MCP server
- [ ] Expose databases through MCP
- [ ] Debug MCP connections
- [ ] Deploy MCP servers in production

---

## Additional Resources

- [MCP Official Documentation](https://modelcontextprotocol.io/)
- [Anthropic MCP Guide](https://docs.anthropic.com/claude/docs/model-context-protocol)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [ngspice Documentation](http://ngspice.sourceforge.net/)

---

## Next Steps

Ready for terminal integration? Continue to:

**[Module 6: Claude Code CLI →](../06-claude-code-cli/README.md)**

Learn about Claude's official CLI and terminal integration!

---

**Questions or issues?** Open a GitHub issue or check the examples.
