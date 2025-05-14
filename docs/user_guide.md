# User guide

<!--TOC-->

- [User guide](#user-guide)
  - [Simple agent network](#simple-agent-network)
  - [Hocon files](#hocon-files)
    - [Import and Substitution](#import-and-substitution)
    - [Manifest](#manifest)
    - [Agent network](#agent-network)
      - [Agent specifications](#agent-specifications)
      - [Tool specifications](#tool-specifications)
      - [LLM specifications](#llm-specifications)
  - [LLM configuration](#llm-configuration)
    - [OpenAI](#openai)
    - [Ollama](#ollama)
  - [Multi-agent networks](#multi-agent-networks)
  - [Coded tools](#coded-tools)
    - [Simple tool](#simple-tool)
    - [API calling tool](#api-calling-tool)
    - [Sly data](#sly-data)
  - [Toolbox](#toolbox)
  - [Logging and debugging](#logging-and-debugging)
  - [Advanced](#advanced)
    - [Subnetworks](#subnetworks)
    - [AAOSA](#aaosa)
  - [Connect with other agent frameworks](#connect-with-other-agent-frameworks)

<!--TOC-->

## Simple agent network

The `music_nerd` agent network is the simplest agent network possible: it contains a single agent
that answers questions about music since the 60s. See its description here: [docs/examples/music_nerd.md](../docs/examples/music_nerd.md).

The steps to start the server and the client are described in the [README](../README.md).
When starting, the first thing the server will do is load the agent network configurations
from the "manifest" file. The manifest file is specified by the `AGENT_MANIFEST_FILE` environment variable:
```
AGENT_MANIFEST_FILE="./registries/manifest.hocon"
```
Open [./registries/manifest.hocon](../registries/manifest.hocon) and look at its contents. It should look something like this:
```hocon
{
    # ... other agent networks ... #
    "music_nerd.hocon": true,
    # ... other agent networks ... #
}
```
This tells the server to load the `music_nerd.hocon` file from the same `/registries` folder.

Setting the value to `false` would make the server ignore this agent network.

Open [../registries/music_nerd.hocon](../registries/hello_world.hocon) and have a look at it.
For now just note that it contains:
- an `llm_config` section that specifies which LLM to use by default for the agents in this file
- a `tools` section that contains a single agent, the "frontman", called `MusicNerd`

Read the instructions of the agent to see what it does.
Feel free to modify the instructions to see how it affects the agent's behavior.
See if you can make it a soccer expert for instance!

We'll describe the structure of agent networks' `.hocon` files in next section.

## Hocon files

### Import and Substitution

HOCON files support importing content from other HOCON files using the unquoted keyword `include`, followed by whitespace and the path to the imported file as a quoted string:
```hocon
include "config.hocon"
```
> **Note**: The file path in include should be an **absolute path** to ensure it can be resolved correctly.

HOCON supports value substitution by referencing previously defined configuration values. This allows constants to be defined once and reused throughout the file.

To substitute a value, wrap the referenced key in `${}`:
```hocon
"function": ${aaosa_call}
```

To substitute a nested value inside an object or dictionary, use dot notation:
```hocon
"name": ${info.name}
```

Note that substitutions are **not parsed inside quoted strings**. If you need to include a substitution within a string, you can quote only the non-substituted parts:
```hocon
"instructions": ${instruction_prefix} "main instruction" ${instruction_suffix}
```
You can see a working example here: [../registries/smart_home_include.hocon](../registries/smart_home_include.hocon).

For more details, please see [https://github.com/lightbend/config/blob/main/HOCON.md#substitutions](https://github.com/lightbend/config/blob/main/HOCON.md#substitutions)

### Manifest

A manifest file is a list of agent network configurations that the server will load.

It's simple dictionary where the keys are the names of the agent network configuration files
and the values are booleans. For instance:
```hocon
{
    "agent_network_A.hocon": true,
    "agent_network_B.hocon": false,
    "agent_network_C.hocon": true,
}
```
In this example the server will load agent networks A and C but not B.

When you start the server, you can see which agent networks have been loaded by looking at the logs:
```
> python -m neuro_san.service.agent_main_loop --port 30011

tool_registries found: ['agent_network_A', 'agent_network_C']
```

For more details, please check the [Agent Manifest HOCON File Reference](https://github.com/leaf-ai/neuro-san/blob/main/docs/manifest_hocon_reference.md) documentation.

### Agent network

#### Agent specifications

| **Field**    | **Description**                                                                                                                              |
|--------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| agent_name   | text handle for other agent specs and hosting system to refer to                                                                             |
| function     | Open AI function spec (standard) that formally describes the various inputs that the agent expects                                           |
| instructions | text that sets up the agent in detail for its task                                                                                           |
| command      | text that sets the agent in motion after it receives all its inputs                                                                          |
| tools        | optional list of references to other agents that this agent is allowed to call in the course of working through their input and instructions |
| llm_config   | optional agent-specification for different LLMs for different purposes such as specialization, costs, etc.                                   |

#### Tool specifications

| **Field**     | **Description**                                                                                   |
|---------------|---------------------------------------------------------------------------------------------------|
| agent_name    | text handle for other agent specs to refer to                                                     |
| function      | Open AI function spec (standard) that formally describes the various inputs that the tool expects |
| method        | Code reference to the function that is to be invoked when the tool is called.                     |

#### LLM specifications

| **Field**   | **Description**                                                                                                                       |
|-------------|---------------------------------------------------------------------------------------------------------------------------------------|
| model_name  | name of the model to use (i.e. “gpt-4o”, “claude-3-haiku”)                                                                            |
| *_api_key   | api key value or environment variable to reference to allow access to the LLM provider if different from hosting environment default. |
| temperature | optional level of randomness 0.0-1.0 to use for LLM results                                                                           |

See next section for more information about how to specify the LLM(s) to use.

For a full description of the fields, please refer to the [Agent Network HOCON File Reference](https://github.com/leaf-ai/neuro-san/blob/main/docs/agent_hocon_reference.md) documentation.

## LLM configuration

The `llm_config` section of the agent network configuration file specifies which LLM to use
for the agents in this file. It can be specified:
- at the agent network level, to apply to all agents in this file
- at the agent level, to apply to a specific agent

For a full description of the fields, please refer to the [LLM config](https://github.com/leaf-ai/neuro-san/blob/main/docs/agent_hocon_reference.md#llm_config) documentation.

For instructions about how to extend the default LLM descriptions shipped with the `neuro-san` library,
please refer to the [LLM Info HOCON File Reference](https://github.com/leaf-ai/neuro-san/blob/main/docs/llm_info_hocon_reference.md) documentation.

### OpenAI

To use an OpenAI LLM, set the `OPENAI_API_KEY` environment variable to your OpenAI API key
and specify which model to use in the `model_name` field:
```hocon
    "llm_config": {
        "model_name": "gpt-4o",
    },
```

See [./examples/music_nerd.md](./examples/music_nerd.md) for an example.

### Ollama

To use an LLM that runs locally with [Ollama](https://ollama.com/):
- Make sure the Ollama server is running
- Make sure the model is downloaded, up to date and available in the Ollama server. For instance, `ollama run llama3.1`
  will download the model and make it available for use. `ollama pull llama3.1`
  will update the model to the latest version if needed.
- If the agent network contains tools, make sure the model can call tools:
  see [Ollama's documentation for models that support tools](https://ollama.com/search?c=tools)
- Set the `class` and `model_name` fields in the `llm_config` section of the agent network configuration file:
```hocon
    "llm_config": {
        "class": "ollama",
        "model_name": "llama3.1",
    },
```

See [./examples/music_nerd_pro_local.md](./examples/music_nerd_pro_local.md) for an example.

For more information about how to use Ollama with LangChain,
see [this page](https://python.langchain.com/docs/integrations/chat/ollama/)


## Multi-agent networks

## Coded tools

### Simple tool

### API calling tool

### Sly data

A `sly_data` dictionary can be passed along with the `ChatRequest` from the client side.
The `sly_data` will not be seen by the LLMs, and by default, will not leave the agent network.
Within the agent network the `sly_data` is visible to the coded tools and can be used as a
bulletin-board between coded tools.

This policy is one of security-by-default, whereby no `sly_data` gets out of the agent network
at all unless otherwise specified. It's only when a boundary is crossed that the question of
what goes through arises. There are 3 boundaries:

1.  What goes out to external networks (`to_downstream`). For instance, you may not want to send
    credentials to an agent network that lives on another server.
2.  What comes in from external networks (`from_upstream`). For instance, you might not trust what's
    coming from an agent network that lives on another server.
3.  What goes back to the client (`to_upstream`). For instance, you might not want secrets from
    the server side to be shared with the clients that connect to it.

So by default nothing is shared, and you have to explicitly state what goes through.

Suppose you have an agent network that takes in two numbers,
the name of an operation (say, addition/subtraction/multiplication/division), and asks another
agent network to perform the operation on the numbers. To pass the numbers as `sly_data` to the
downstream agent network you must specify the following in the .hocon file of the agent that
is connecting to the downstream agent network:

```hocon
"allow": {
    "to_downstream": {
        # Specifying this allows specific sly_data
        # keys from this agent network to be sent
        # to downstream agent networks
        "sly_data": ["x", "y"]
   }
}
```

To get `sly_data` coming back from a downstream agent network, i.e., to get the result of
adding two numbers, you must specify the following in the .hocon file of the agent that is
connecting to the downstream agent network:

```hocon
"allow": {
    "from_downstream": {
        # Specifying this allows specific sly_data
        # keys to be ingested from downstream agent
        # networks as sly_data for this agent network
        "sly_data": ["equals"]
    }
}
```

To allow frontman agent to return `sly_data` to the client, you must specify the following in
the .hocon file of the frontman (the only agent that is connected to the client):

```hocon
"allow": {
    "to_upstream": {
        # Specifying this allows sly_data keys
        # from this network to be passed back
        # to the calling client
        "sly_data": ["equals"]
    }
}
```

All the above .hocon "allow" blocks can be combined in a single "allow" block. An example
is given [here](https://github.com/leaf-ai/neuro-san/blob/main/neuro_san/registries/math_guy_passthrough.hocon#L54)

For a full reference, please check the [neuro-san documentation](https://github.com/leaf-ai/neuro-san/blob/main/docs/agent_hocon_reference.md#allow)

## Toolbox

## Logging and debugging

## Advanced

### Subnetworks

### AAOSA

AAOSA stands for **A**daptive **A**gent **O**riented **S**oftware **A**rchitecture.

In this architecture, agents decide if they can answer inquiries or if they need to call other agents to help them.

Reference:
[Iterative Statistical Language Model Generation for Use with an
Agent-Oriented Natural Language Interface ](https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=3004005f1e736815b367be83f2f90cc0fa9e0411)

<!-- (https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=011fb718658d611294613286c0f4b143aed40f43) -->

Look at [../registries/smart_home.hocon](../registries/smart_home.hocon) and in particular:
- aaosa_instructions
- aaosa_call
- aaosa_command

## Connect with other agent frameworks

- MCP: [MCP BMI SSE](./examples/mcp_bmi_sse.md) is an example of an agent network that uses [MCP](https://www.anthropic.com/news/model-context-protocol)
to call an agent that calculates the body mass index (BMI).
- Agentforce: [Agentforce](./examples/agentforce.md) is an agent network that delegates queries to a [Salesforce Agentforce](https://www.salesforce.com/agentforce/)
agent to interact with a CRM system.
- CrewAI: (coming soon)
- A2A: (coming soon)
 
