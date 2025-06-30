import os
import re
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

load_dotenv()

# Can extend below with {context} & {resources}
planner_template = """
You are an expert CTF solver and are tasked with creating a detailed plan of how to generate a solution script to a team of CTF solvers.
Your output MUST use the following exact headers (case-sensitive):

Context:
<one or more lines describing the shared context>

Steps:
1. <first step>
2. <second step>
3. <…>

Problem: {problem}

Consider the following for context:
1. Problem Type (Cryptography, Reverse engineering, Web exploitation, binary exploitation, Crypto, Other). If other, specify as much as possible.

Consider the following for each step:
1. Required resources and tools
2. Potential challenges and means to overcome such
"""

solver_template = """
You are an expert CTF solver tasked with executing the following plan to generate a solution python script.

Problem:
{problem}

Plan: 
{plan}

Consider the following:
1. Strictly return the python script ONLY.
2. Have the script take in the problem as input as output ONLY the flag,
3. If you cannot solve, only state "CANNOT SOLVE" and provide breifly why.
4. Check over your work multiple times
"""

class Agent:
    def __init__(self, prompt_template):
        self.custom_prompt = PromptTemplate.from_template(prompt_template)
        self.llm = ChatOpenAI(model="gpt-4o-mini", 
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
        output_txt = raw_output.content
        return output_txt    
    # # generates DICT of executables to pass to multiple solver agents
    # def generate_plan2(self, problem: str) -> dict:
    #     input_prompt = self._generate_prompt(problem)
    #     raw_output = self.llm.invoke(input_prompt)
    #     output_txt = raw_output.content
    #     output_json = json.loads(output_txt)
    #     return output_json

class Solver(Agent):
    def __init__(self):
        super().__init__(solver_template)
    # No need for initial_prompt FOR NOW
    def generate_solution(self, problem:str, plan:str) -> str:
        # Helper Method to create a plan based on the problem and initial prompt
        input_prompt = self.custom_prompt.format(problem=problem, plan=plan)
        raw_output = self.llm.invoke(input_prompt)
        output_txt = raw_output.content
        return output_txt    



# local testing
if __name__ == "__main__":
    planner = Planner()
    solver = Solver()
    with open("problem.txt", 'r') as file:
            problem = file.read()
    plan = planner.generate_plan(problem=problem)
    solution = solver.generate_solution(problem=problem, plan=plan)
    print(solution)
