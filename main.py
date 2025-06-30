import sys
from agents import Planner, Solver

def main():
    if(len(sys.argv) != 2):
        print("Ussage: python main.py problem.txt")
        return 0
    with open(sys.argv[1], 'r') as file:
            problem = file.read()
    p_agent = Planner()
    s_agent = Solver()
    plan = p_agent.generate_plan(problem=problem)
    # print(plan)
    sol_script = s_agent.generate_solution(problem=problem, plan=plan)
    print(sol_script)


if __name__ == "__main__":
    main()
