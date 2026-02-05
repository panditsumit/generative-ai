# ========================================================================
# AGENT AS MCP TOOL - Food Recipe Assistant
# ========================================================================
#
# This script demonstrates how to create an MCP (Model Context Protocol) server
# from an AI Agent. The agent exposes food recipe search functionality through MCP.
#
# SETUP: Install packages: pip install agent-framework openai mcp requests python-dotenv anyio pydantic
# .env file: OPENROUTER_ENDPOINT=https://openrouter.ai/api/v1, OPENROUTER_API_KEY=your_key
#
# CLAUDE DESKTOP CONFIG: Add to claude_desktop_config.json:
# {
#   "mcpServers": {
#     "food-recipes": {
#       "command": "python",
#       "args": ["/absolute/path/to/agent_as_mcp_tool.py"]
#     }
#   }
# }
# ========================================================================

import asyncio
import os
import json
import requests
from typing import Annotated, List, Dict, Any, Optional, Callable, Awaitable
from pydantic import Field
from dotenv import load_dotenv, find_dotenv
import anyio

# Core components for building Agent, tool-enabled agents
# Ensure you have installed: pip install -U agent-framework --pre
from agent_framework import ChatAgent, AgentRunContext, FunctionInvocationContext
from agent_framework.openai import OpenAIChatClient
from mcp.server.stdio import stdio_server

# ========================================================================
# PART 1: API Helper Functions
# ========================================================================
# These functions are the tools that the AI agent can call. Add your own
# functions here following the same pattern with proper docstrings and type hints.
# ========================================================================

# Helper to transform raw API response into clean, LLM-friendly format
def _clean_meal_data(meal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper function to restructure the raw meal API response into a clean,
    LLM-friendly format by combining ingredients and measures.
    """
    if not meal:
        return {}

    # Combine ingredients and measures into a single list
    ingredients = []
    for i in range(1, 21):
        ing = meal.get(f"strIngredient{i}")
        measure = meal.get(f"strMeasure{i}")
        if ing and ing.strip():
            ingredients.append(f"{measure.strip()} {ing.strip()}".strip())

    return {
        "id": meal.get("idMeal"),
        "name": meal.get("strMeal"),
        "category": meal.get("strCategory"),
        "area": meal.get("strArea"),
        "instructions": meal.get("strInstructions"),
        "ingredients": ingredients,
        "tags": meal.get("strTags"),
        "youtube_link": meal.get("strYoutube")
    }

# Tool: Get random meal from TheMealDB API
def get_random_meal() -> str:
    """
    Retrieves a random meal recipe from the database.
    Useful when the user wants a surprise suggestion or explicitly asks for a random recommendation.

    Returns:
        str: A JSON string containing the meal name, ingredients, and cooking instructions.
    """
    try:
        response = requests.get("https://www.themealdb.com/api/json/v1/1/random.php")
        response.raise_for_status()
        data = response.json()

        if not data.get("meals"):
            return json.dumps({"error": "No meal found."})

        meal = _clean_meal_data(data["meals"][0])
        return json.dumps(meal, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Failed to fetch random meal: {str(e)}"})

# Tool: Get meal by name from TheMealDB API
def get_meal_by_name(
    meal_name: Annotated[str, Field(description="The name of the meal to search for (e.g., 'Arrabiata', 'Burger').")]
) -> str:
    """
    Searches for a specific meal recipe by name.
    Use this when the user asks for a specific dish or wants to know how to cook a named item.

    Args:
        meal_name: The name of the dish to search for.

    Returns:
        str: A JSON string containing a list of matching meals with their details.
    """
    try:
        # The API requires a search query parameter 's'
        response = requests.get(f"https://www.themealdb.com/api/json/v1/1/search.php?s={meal_name}")
        response.raise_for_status()
        data = response.json()

        if not data.get("meals"):
            return json.dumps({"status": "not_found", "message": f"No meals found with the name '{meal_name}'."})

        # Clean and limit results (e.g., top 3 matches to save tokens)
        results = [_clean_meal_data(m) for m in data["meals"][:3]]
        return json.dumps(results, indent=2)

    except Exception as e:
        return json.dumps({"error": f"Failed to search for meal: {str(e)}"})


# ========================================================================
# PART 2: Configuration & Agent Setup
# ========================================================================
# Configure the AI agent with chat client, instructions, tools, and middleware.
# Customize AGENT_NAME and AGENT_INSTRUCTIONS for your use case.
# ========================================================================

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Setup OpenAIChatClient with OpenRouter (free model available)
# Replace with OpenAI (https://api.openai.com/v1) or other compatible endpoints
openai_chat_client = OpenAIChatClient(
    base_url=os.environ.get("OPENROUTER_ENDPOINT"),
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    model_id="nvidia/nemotron-3-nano-30b-a3b:free"
)

AGENT_NAME = "FoodAgent"

AGENT_INSTRUCTIONS = """You are an expert AI Chef dedicated to helping users discover and prepare delicious meals.

CORE BEHAVIORS:
1. **Tool Usage**: You have access to a recipe database. ALWAYS use the provided tools to answer questions about recipes. Do not guess or hallucinate ingredients.
   - Use `get_meal_by_name` when the user asks for a specific dish.
   - Use `get_random_meal` when the user is undecided, asks for a suggestion, or wants a surprise.

2. **Response Format**:
   - Start with an appetizing description of the dish.
   - List key ingredients clearly (based on the tool output).
   - Summarize the cooking instructions to be easy to follow.
   - If the tool provides a YouTube link, always include it at the end.
   - Include Tool Name used for fetching response

3. **Constraints**:
   - Keep your response friendly but strictly under 200 words.
   - If instructions are long, summarize the key steps to fit the word limit.
"""

# Middleware to log function calls for debugging
async def logging_function_middleware(
    context: FunctionInvocationContext,
    next: Callable[[FunctionInvocationContext], Awaitable[None]],
) -> None:
    """Middleware that logs function calls."""
    print(f"Calling function: {context.function.name}")
    await next(context)
    print(f"Function result: {context.result}")

# Create the Food Agent with tools and middleware
food_agent = ChatAgent(
    name=AGENT_NAME,
    chat_client=openai_chat_client,
    instructions=AGENT_INSTRUCTIONS,
    tools=[get_random_meal, get_meal_by_name],
    middleware=[logging_function_middleware]
)

# ========================================================================
# PART 3: Expose Agent as MCP Server
# ========================================================================
# Convert the agent to an MCP server using stdio transport for desktop clients.
# Run with: python agent_as_mcp_tool.py
# ========================================================================

# Convert the agent to an MCP server object
server = food_agent.as_mcp_server()

async def run():
    """
    Run the MCP server using stdio transport.
    This allows the agent to communicate with MCP clients (like Claude Desktop).
    """
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    try:
        anyio.run(run)
    except KeyboardInterrupt:
        pass