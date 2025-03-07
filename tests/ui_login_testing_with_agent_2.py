import os
import logging
from pathlib import Path
import argparse
import sys
from io import StringIO
from smolagents import CodeAgent, DuckDuckGoSearchTool, LiteLLMModel
from dotenv import load_dotenv
import pytest
from playwright.sync_api import sync_playwright

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('test_execution.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class TestRunner:
    def __init__(self):
        load_dotenv()
        self.results_dir = Path('test-results')
        self.results_dir.mkdir(exist_ok=True)
        self.model = LiteLLMModel(model_id="gemini/gemini-2.0-flash-lite", api_key=os.getenv("GEMINI_API_KEY"))
        
        self.agent = CodeAgent(
            tools=[DuckDuckGoSearchTool()],
            model=self.model,
            additional_authorized_imports=[
                "import pytest",
                "from playwright.sync_api import sync_playwright",
                "asyncio"
            ]
        )
        
        self.instructions = """
        Generate a Python string containing a Playwright test suite for https://practice.expandtesting.com/login:
        1. Use Playwright's sync API with pytest as the test framework.
        2. Include the following test cases:
            - Positive test: Login with valid credentials (username='practice', password='SuperSecretPassword!'), verify successful login by checking for a welcome message or logout button.
            - Negative tests:
                - Invalid credentials (username='wronguser', password='wrongpass'), verify error message appears.
                - Empty fields (username='', password=''), verify error message appears.
                - Username only (username='practice', password=''), verify error message appears.
        3. Optimize for efficiency:
            - Use a single browser instance via pytest fixture with scope='session'.
            - Minimize setup/teardown by reusing the page object.
            - Provide clear pass/fail assertions with descriptive messages.
        4. Return the complete test code as a string, including imports (pytest, playwright.sync_api).
        5. Do not execute the code or create files; only return the string.
        """

    def run_tests(self, debug=False):
        """Generate and execute the test suite in memory"""
        try:
            # Generate the test suite
            logger.info("Starting test suite generation")
            debug_instructions = self.instructions
            if debug:
                debug_instructions += "\n6. Add debug support by setting headless=False and slow_mo=500 in the browser launch configuration."
                logger.info("Generating with debug mode enabled")
            
            result = self.agent.run(debug_instructions)
            logger.info("Test suite generated successfully")
            
            # Handle the result
            if isinstance(result, str):
                test_code = result
            elif isinstance(result, dict) and 'code' in result:
                test_code = result['code']
            else:
                logger.warning("Unexpected result format, using as string")
                test_code = str(result)
            
            # Execute the tests in memory
            self._execute_tests_in_memory(test_code, debug)
            
            return test_code
            
        except Exception as e:
            logger.error(f"Test process failed: {e}")
            raise

    def _execute_tests_in_memory(self, test_code, debug):
        """Execute the generated test code in memory"""
        try:
            logger.info("Executing tests in memory")
            
            # Redirect stdout to capture test output
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            # Define pytest arguments
            pytest_args = [
                "-v",  # Verbose output
                f"--junitxml={self.results_dir / 'results.xml'}"
            ]
            if debug:
                pytest_args.append("--capture=no")  # Show live output
            
            # Execute the test code in the current namespace
            exec(test_code, globals())
            
            # Run pytest programmatically on the in-memory tests
            # We need to trick pytest into running the defined functions
            exit_code = pytest.main(pytest_args + ["-k", "test_"])
            
            # Capture and log the output
            test_output = sys.stdout.getvalue()
            logger.info(f"Test output:\n{test_output}")
            
            sys.stdout = old_stdout
            
            if exit_code == 0:
                logger.info("Tests executed successfully")
            else:
                logger.warning(f"Test execution completed with exit code {exit_code} (some tests may have failed)")
                
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            raise
        finally:
            sys.stdout = old_stdout

def main():
    parser = argparse.ArgumentParser(description="Generate and execute Playwright test suite in memory")
    parser.add_argument('--debug', action='store_true', help='Run tests with debug mode (visible browser)')
    args = parser.parse_args()

    runner = TestRunner()
    runner.run_tests(debug=args.debug)

if __name__ == "__main__":
    main()