import os
import re
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

load_dotenv()

# Can extend below with {context} & {resources}
planner_template = """
You are a planner AI agent and are tasked with creating a detailed plan of how to write a solution script
to retrieve the flag in python for the CTF problem below. Your plan will be given to another AI agent to 
generate the actual python solving script. Think very deep.

Consider the following when generating:
1. Assume the AI agent has 0 external knowledge at all.
2. If nesscarry, provide explict knowledge such as needed array values and techniques to solve.
3. Do NOT generate a plan for a brute force solution.
4. Be as exact as possible

Follow the format below:
Steps:
1. <first step>
2. <second step>
3. <…>

Problem provided below: 
{problem}
"""

solver_template = """
You are an AI agent tasked with executing the following plan to generate a solution python script. Think very deep.

Consider the following:
1. Strictly return the python script ONLY. No additional text ever.
2. The script, when ran, should ONLY print out the flag.
3. Assume absolutely 0 edits are possible, return a script completley finished.
4. If you cannot solve, only state "CANNOT SOLVE" and provide briefly why.

Plan: 
{plan}

"""

independent_template = """
You are tasked with generating a python script to solve the following CTF problem below. 

You output should strictly adhere the following:
1. Return a solving script ONLY, no additional text at all.
2. Your solution should NOT be brute force
3. Assume zero external help. No user input or code edits ever.
4. The code should output the actual solutino flag ONLY.
5. If you cannot solve, only state "CANNOT SOLVE" and provide briefly why.

Problem:
{problem}
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

class Solver(Agent):
    def __init__(self):
        super().__init__(solver_template)
    # No need for initial_prompt FOR NOW
    def generate_solution(self, plan:str) -> str:
        # Helper Method to create a plan based on the problem and initial prompt
        input_prompt = self.custom_prompt.format(plan=plan)
        raw_output = self.llm.invoke(input_prompt)
        output_txt = raw_output.content
        # EXTRACT ONLY THE CODE PORTION
        sol_script = None
        return output_txt    

# FOR TESTING ONLY
class Independent(Agent):
    def __init__(self):
        super().__init__(independent_template)
    def generate_solution(self, problem:str) -> str:
        # Helper Method to create a plan based on the problem and initial prompt
        input_prompt = self.custom_prompt.format(problem=problem)
        raw_output = self.llm.invoke(input_prompt)
        output_txt = raw_output.content
        # EXTRACT ONLY THE CODE PORTION
        sol_script = None
        return output_txt    

# class Executer(Agent):
#     def __init__(self):
#         super().__init__(executer_template)
#     # Def generate actual flag
#     def generate_flag(self, problem:str, solve_script) -> str:
#         # RUN THE CODE AND EXTRACT THE FLAG
#         pass


# local testing
if __name__ == "__main__":
    planner = Planner()
    solver = Solver()
    independent = Independent()
    # executer = Executer()

    with open("marx.c", 'r') as file:
        problem = file.read()

    # plan = planner.generate_plan(problem=problem)
    # print(plan)
    # solution_script = solver.generate_solution(plan=plan)
    # print(solution_script)
    solution = independent.generate_solution(problem=problem)
    print(solution)
    #flag = executer.generate_flag(problem=problem, code=solution_script)

    #print("Extracted Flag:", flag)

