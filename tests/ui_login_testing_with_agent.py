import os
from smolagents import CodeAgent, DuckDuckGoSearchTool, HfApiModel, LiteLLMModel
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file
model = LiteLLMModel(model_id="gemini/gemini-2.0-flash-lite", api_key=os.getenv(key="GEMINI_API_KEY"))
agent = CodeAgent(tools=[DuckDuckGoSearchTool()], model=model, 
                  additional_authorized_imports=["import pytest", "from playwright.sync_api import sync_playwright", "asyncio" ])
# agent = CodeAgent(tools=[DuckDuckGoSearchTool()], model=HfApiModel(model_id="Qwen/Qwen2.5-Coder-32B-Instruct"))
# agent = CodeAgent(tools=[DuckDuckGoSearchTool()], model=HfApiModel(model_id='https://pflgm2locj2t89co.us-east-1.aws.endpoints.huggingface.cloud/'))
# agent = CodeAgent(tools=[DuckDuckGoSearchTool()], model=HfApiModel(model_id="Qwen/Qwen2.5-Coder-32B-Instruct"))

# Updated instructions
instructions = """
Create a compact Playwright test suite for https://practice.expandtesting.com/login:
1. Use sync API, pytest
2. Tests: 
    - Pass: username='practice', password='SuperSecretPassword!'
    - Fail: invalid creds, empty fields, username only
3. Optimize for multiple runs:
    - Single browser instance
    - Minimal setup
    - Clear pass/fail reporting
4. Output JUnit XML reports for CI/CD integration.
5. Run the tests and ensure the test results (including the JUnit XML report) are stored locally in a designated directory (e.g., 'test-results') for easy access and review.
"""

# Run agent
try:
    result = agent.run(instructions)
    print("Agent completed successfully")
except Exception as e:
    print(f"Error during agent execution: {e}")

