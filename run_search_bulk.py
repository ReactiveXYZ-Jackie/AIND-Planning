from functools import wraps
import errno
import os
import signal
import argparse
from multiprocessing import (Pool, cpu_count)
from timeit import default_timer as timer
from aimacode.search import InstrumentedProblem
from aimacode.search import (breadth_first_search, astar_search,
    breadth_first_tree_search, depth_first_graph_search, uniform_cost_search,
    greedy_best_first_graph_search, depth_limited_search,
    recursive_best_first_search)
from my_air_cargo_problems import air_cargo_p1, air_cargo_p2, air_cargo_p3

PROBLEMS = [["Air Cargo Problem 1", air_cargo_p1],
            ["Air Cargo Problem 2", air_cargo_p2],
            ["Air Cargo Problem 3", air_cargo_p3]]
SEARCHES = [["breadth_first_search", breadth_first_search, ""],
            ['breadth_first_tree_search', breadth_first_tree_search, ""],
            ['depth_first_graph_search', depth_first_graph_search, ""],
            ['depth_limited_search', depth_limited_search, ""],
            ['uniform_cost_search', uniform_cost_search, ""],
            ['recursive_best_first_search', recursive_best_first_search, 'h_1'],
            ['greedy_best_first_graph_search', greedy_best_first_graph_search, 'h_1'],
            ['astar_search', astar_search, 'h_1'],
            ['astar_search', astar_search, 'h_ignore_preconditions'],
            ['astar_search', astar_search, 'h_pg_levelsum']]

# timeout
class TimeoutError(Exception):
    pass

def timeout(seconds=10, error_message="Function Timeout"):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wraps(func)(wrapper)

    return decorator

# for tracking down the problem status
class PrintableProblem(InstrumentedProblem):

    def __repr__(self):
        return '{:^10d}  {:^10d}  {:^10d}'.format(self.succs, self.goal_tests, self.states)

@timeout(600)
def run_search(problem_pack, search_function_pack, heuristic_pack=None):

    problem = problem_pack[0]
    problem_desc = problem_pack[1]
    search_function = search_function_pack[0]
    search_function_desc = search_function_pack[1]
    heuristic = heuristic_pack[0]
    heuristic_desc = heuristic_pack[1]

    start = timer()
    ip = PrintableProblem(problem)
    if heuristic is not None:
        node = search_function(ip, heuristic)
    else:
        node = search_function(ip)
    end = timer()

    if heuristic_desc is None:
        heuristic_desc = ""

    print("\nSolving {} using {}{}...".format(problem_desc, search_function_desc, heuristic_desc))
    print("\nExpansions   Goal Tests   New Nodes")
    print("{}\n".format(ip))

    show_solution(node, end - start)
    print()

def search_with_timeout(problem, search_fn, heuristic):
    try:
        run_search(problem, search_fn, heuristic)
    except TimeoutError as e:
        print(e)

def main():
    # results for storing parallel tasks
    results = []
    num_workers = cpu_count() - 1
    # start running search function
    # using 3 process workers
    with Pool(processes = num_workers) as pool:
        for pname, p in PROBLEMS:
            for sname, s_fn, h in SEARCHES:
                # extract arguments
                hstring = h if not h else " with {}".format(h)
                problem = p()

                if not h:
                    heuristic_pack = (None, None)
                else:
                    heuristic_pack = (getattr(problem, h), hstring)

                heuristic = None if not h else getattr(problem, h)

                result = pool.apply_async(search_with_timeout, ((problem,pname),\
                (s_fn, sname), heuristic_pack))
                results.append(result)

        for result in results:
            result.get()



def show_solution(node, elapsed_time):
    print("Plan length: {}  Time elapsed in seconds: {}".format(len(node.solution()), elapsed_time))
    for action in node.solution():
        print("{}{}".format(action.name, action.args))

if __name__=="__main__":
    main()
