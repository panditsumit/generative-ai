# Generative AI with Microsoft Agent Framework

This repository contains examples and demonstrations of using the Microsoft Agent Framework to build AI-powered food agents. The agents can help users discover recipes, prepare meals, and engage in multi-turn conversations about cuisine.

## Project Overview

This project showcases three main concepts using the Microsoft Agent Framework:

### 1. Basic Food Agent
A simple conversational agent that suggests random dishes from various cuisines around the world.

### 2. Function Tools Enabled Agent
An advanced agent that integrates with external APIs (TheMealDB) to fetch real-world recipe data. This agent can:
- Get random meal suggestions
- Search for specific meals by name
- Provide detailed cooking instructions with ingredients

### 3. Multi-turn Conversation Agent
An agent that maintains conversation context using threads, allowing users to reference previous interactions and orders.

## Key Features

- Integration with OpenRouter API for LLM inference
- Real-world data integration through TheMealDB API
- Conversation context management with threading
- Customizable agent personalities and instructions
- Middleware support for function call logging

## Technologies Used

- Microsoft Agent Framework
- Python 3
- Jupyter Notebooks
- OpenRouter API
- TheMealDB API

## Notebooks

1. `basic_food_agent.ipynb` - Simple food suggestion agent
2. `agent_with_function_tools.ipynb` - Advanced agent with API integration
3. `multi_turn_conversation_agent.ipynb` - Context-aware conversational agent
4. `human_in_the_loop.ipynb` - Agent with human in the loop for moderation

Each notebook demonstrates different aspects of building AI agents with the Microsoft Agent Framework.

## Requirements

See `microsoft-agent-framework/installation/requirements.txt` for the list of dependencies.

## License

This project is licensed under the MIT License - see the LICENSE file for details.