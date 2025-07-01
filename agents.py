import tempfile
import os
import re
import subprocess
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

load_dotenv()

planner_template = """
You are tasked with giving detailed steps to produce a python script that can properly produce the flag
from reverse engineering the provided obfuscated C code. Your tasks will be passed to an expert CTF solver.
The solver will also be provided this outline. 

Follow the rules below strictly:
1. Ensure each step has very detailed instructions to execute them.
2. Provide addtional context helpful to solve at the very top, include any background knoweledge needed to solve
3. Assume that the solver has absolutley zero external knoweledge other then exactly what you output.
4. Be as detailed as absolutley possible, leave zero room for interpretation.

Your output should strictly follow the format below:
Context:
<Context here>

Steps:
Step 1: <Step + actions to execute it>
Step 2: ...

Below is the problem:
{problem}
"""

solver_template = """
When generating the solution script, follow all below strictly:
1. Your code should require absolutely zero human input at all
    a. No need for human editing the script (no "Replace with actual flag")
    b. No need for human input
2. Your code should print out the valid flag ONLY.
3. Follow the provided plan strictly
4. Do NOT provide anything other then the script. strictly return the code with zero explanation

Below is the plan provided:
{plan}

Your code should resemble the following:
def rol(j: int, h: int) -> int:
    # CHAR TRANSFORMATION LOGIC


def ror(j: int, h: int) -> int:
    # CHAR TRANSFORMATION LOGIC

expected = [ # ARRAY OF ENCODED VALUES FROM ORIGINAL
]
for i in range(len(expected))
    z =  # LOGIC TO REVERSE encryption
    z =  # LOGIC TO REVERSE encryption
    z =  # LOGIC TO REVERSE encryption
    z =  # LOGIC TO REVERSE encryption
    z ^= # LOGIC TO REVERSE encryption
    print(chr(z), end='')
"""

debugging_template = """
Your provided code failed. Below was the failure point, fix it. 
Return ONLY the fixed python script and nothing else.

Orignal (failed) python script:
{og_code}

Error:
{error}
"""
# 
class Agent:
    def __init__(self, prompt_template):
        self.custom_prompt = PromptTemplate.from_template(prompt_template)
        self.llm = ChatOpenAI(model="gpt-4o", 
                              max_tokens=None, 
                              max_retries=2, 
                              api_key = os.getenv("OPENAI_API_KEY"))

class Planner(Agent):
    def __init__(self):
        super().__init__(planner_template)

    # Possibly introduce extra complexity later on
    def _generate_prompt(self, problem: str) -> str:
        # Helper method to generate the prompt for the OpenAI API
        return self.custom_prompt.format(problem=problem)
    
    # No need for initial_prompt FOR NOW
    def generate_plan(self, problem:str) -> str:
        # Helper Method to create a plan based on the problem and initial prompt
        input_prompt = self._generate_prompt(problem)
        raw_output = self.llm.invoke(input_prompt)
        refined_output = raw_output.content
        for __ in range(3):
            refined_output = self._refine_plan(refined_output)
        return refined_output
    
    def _refine_plan(self, plan:str) -> str:
        refine_prompt = f"""
Improve the following plan to be as understable for a LLM as possible.
Return ONLY the improved script, nothing else.
plan: {plan}
"""
        refined_plan = self.llm.invoke(refine_prompt)
        return refined_plan.content


class Solver(Agent):
    def __init__(self):
        super().__init__(solver_template)
        self.max_attempts = 5  # Limit the number of recursive attempts
        self.debug_prompt = PromptTemplate.from_template(debugging_template)

    def generate_solution(self, plan: str) -> str:
        input_prompt = self.custom_prompt.format(plan=plan)
        raw_output = self.llm.invoke(input_prompt)
        solution_script = raw_output.content
        return sanitize_script(solution_script)
    # Code make general function lol but lazy
    def debugged_solution(self, error: str, og_code: str) -> str:
        input_prompt = self.debug_prompt.format(error=error, og_code=og_code)
        raw_output = self.llm.invoke(input_prompt)
        solution_script = raw_output.content
        return sanitize_script(solution_script)

    def check_script(self, solve_script: str, attempt: int = 0):
        if attempt >= self.max_attempts:
            print(f"Max attempts ({self.max_attempts}) reached. Unable to generate a working solution.")
            return None

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(solve_script)
            temp_file_path = temp_file.name
        try:
            result = subprocess.run(['python', temp_file_path], capture_output=True, text=True, timeout=30)
            script_out = result.stdout
            print("\nScript Output:")
            print(script_out)

            
            if result.returncode != 0:
                script_err = result.stderr
                print("\nScript Errors:")
                print(script_err)
                
                # Generate a new solution based on the error
                new_solution = self.debugged_solution(error=script_err, og_code=solve_script)
                
                # Recursive call with the new solution
                return self.check_script(new_solution, attempt + 1)
            else:
                print("Script executed successfully!")
                flag_pattern = r"bctf\{[^}]+\}"
                match = re.search(flag_pattern, script_out)
                if match:
                    flag = match.group(0)
                    print(flag)
                    return flag
                else:
                    print("Script executed successfully, but no flag in the correct format was found.")
                    error = """
                    Your script ran properly but FAILED to retrieve proper flag. 
                    Your output should NATURALLY (no hardcoding) return a flag in format of bctf{......}
                    Below is your original output:
                    {script_out}
                    """
                    new_solution = self.debugged_solution(error, og_code=solve_script)
                    return self.check_script(new_solution, attempt + 1)

        except subprocess.TimeoutExpired:
            print("Script execution timed out after 30 seconds.")
            script_err = "The previous solution timed out. Please provide a more efficient solution."
            new_solution = self.debugged_solution(error=script_err, og_code=solve_script)
            return self.check_script(new_solution, attempt + 1)

        except Exception as e:
            print(f"An error occurred while executing the script: {str(e)}")
            new_solution = self.debugged_solution(error=str(e), og_code=solve_script)
            return self.check_script(new_solution, attempt + 1)

        finally:
            os.unlink(temp_file_path)

    def solve(self, plan: str):
        initial_solution = self.generate_solution(plan)
        return self.check_script(initial_solution)

def sanitize_script(ai_output:str) -> str:
    lines = ai_output.split('\n')
    if len(lines) <= 2:
        return ""  # Return empty string if there are 2 or fewer lines
    else:
        return '\n'.join(lines[1:-1])

# local testing
if __name__ == "__main__":
    planner = Planner()
    solver = Solver()

    with open("marx.c", 'r') as file:
        problem = file.read()

    plan = planner.generate_plan(problem=problem)
    print(plan)
    solution = solver.solve(plan)
    print(solution)