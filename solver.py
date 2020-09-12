import argparse
import itertools
import json
from enum import Enum
from collections import deque

VERSION = "0.0.1"

parser = argparse.ArgumentParser(description='Parameterized complexity')
parser.add_argument('-f', dest='filename', action='store', default=None,
                    help='the path of the file to open')

args = parser.parse_args()


class Tractability(Enum):
    INTRACTABLE = "intractable"
    TRACTABLE = "tractable"


class ParameterizedProblem:
    def __init__(self):
        self.name = ""
        self.parameters = frozenset([])
        self.reductions = {}
        self.antireductions = {}
        self.tractable = {}
        self.intractable = {}

        # Session variables
        self.registered_impacts = []

    def manual_initialization(self, guided):
        print("Name of the problem:")
        if guided:
            print("Example: DBU")
        self.name = prompt()

        print("Parameters:")
        if guided:
            print("Example: a b c d e")
        self.parameters = frozenset(prompt().split())

        print("Known tractable problems:")
        if guided:
            print("Example: a b c d e")
            print("-1 to stop")

        self.add_problem(self.tractable, loop=True)

        print("Known intractable problems:")
        if guided:
            print("Example: a b c d e")
            print("-1 to stop")

        self.add_problem(self.intractable, loop=True)

        print("Known FPT-reductions:")
        if guided:
            print("Example: a b c > a b")
            print("-1 to stop")

        self.add_reduction(loop=True)

        print("Done initializing")

    # Interaction functions
    def add_problem(self, tract_class, loop=False):
        while True:
            line = prompt()
            if line == "-1":
                break

            problem = frozenset(line.split())
            if not self.check_parameters_validity(problem):
                continue

            if tract_class == Tractability.TRACTABLE:
                tract_class = self.tractable
            elif tract_class == Tractability.INTRACTABLE:
                tract_class = self.intractable

            tract_class[problem] = True

            if not loop:
                print("Successfully added problem tractability")
                break

    def add_reduction(self, loop=False):
        while True:
            line = prompt()
            if line == "-1":
                break
            reduction = list(map(lambda x: frozenset(x.split()), line.split(">")))

            if len(reduction) != 2:
                print("Syntax error")
                continue

            correct = True
            for problem in reduction:
                if not self.check_parameters_validity(problem):
                    correct = False

            if not correct:
                continue

            self._add_reduction(reduction[0], reduction[1])

            if not loop:
                print("Successfully added reduction")
                break

    def _add_reduction(self, initial_problem, final_problem):
        if initial_problem not in self.reductions:
            self.reductions[initial_problem] = [final_problem]
        else:
            self.reductions[initial_problem].append(final_problem)

        if final_problem not in self.antireductions:
            self.antireductions[final_problem] = [initial_problem]
        else:
            self.antireductions[final_problem].append(initial_problem)

    # Problem-solving and search functions
    def get_natural_reductions(self, problem):
        reduced_problems = []
        for n in range(len(problem)-1, 0, -1): #len(problem)-1 ?
            problems_n = list(map(frozenset, itertools.combinations(problem, n)))
            reduced_problems.extend(problems_n)

        return reduced_problems

    def get_natural_antireductions(self, problem):
        reduced_problems = []
        complement = frozenset(self.parameters.difference(problem))

        for n in range(1, len(complement)):
            problems_n = list(map(lambda s: frozenset(s).union(problem), itertools.combinations(complement, n)))
            reduced_problems.extend(problems_n)

        return reduced_problems

    def get_user_reductions(self, problem):
        reduced_problems = []
        for candidate, possible_reductions in self.reductions.items():
            if candidate.issubset(problem):
                base_problem = problem.difference(candidate)
                for new_parameters in possible_reductions:
                    new_problem = base_problem.union(new_parameters)
                    reduced_problems.append(new_problem)

        return reduced_problems

    def get_user_antireductions(self, problem):
        reduced_problems = []
        for candidate, possible_antireductions in self.antireductions.items():
            if candidate.issubset(problem):
                base_problem = problem.difference(candidate)
                for new_parameters in possible_antireductions:
                    new_problem = base_problem.union(new_parameters)
                    reduced_problems.append(new_problem)

        return reduced_problems

    def solve(self, problem, tractability):
        if not self.check_parameters_validity(problem):
            return

        previous = {problem: None}
        stack = deque([problem])
        visited = {problem: True}

        while len(stack) > 0:
            current_problem = stack.pop()

            # Solution found
            if (tractability == Tractability.TRACTABLE and current_problem in self.tractable) or \
               (tractability == Tractability.INTRACTABLE and current_problem in self.intractable):
                print("Solution found:")
                proof = []
                while current_problem is not None:
                    proof.append(current_problem)
                    current_problem = previous[current_problem]

                if tractability == Tractability.TRACTABLE:
                    proof.reverse()

                for step_problem in proof:
                    print(f"-> {self.frozenset_prettyprint(step_problem)}-{self.name}")

                if tractability == Tractability.INTRACTABLE and problem not in self.intractable or \
                   tractability == Tractability.TRACTABLE and problem not in self.tractable:

                    trac = ["tractable", "intractable"][tractability == Tractability.INTRACTABLE]
                    print(f"Register the problem as a known {trac} problem? Y/n")
                    line = prompt(yesno=True)
                    if line:
                        st = [self.tractable, self.intractable][tractability == Tractability.INTRACTABLE]
                        st[problem] = True
                        print(f"Successfully registered {self.frozenset_prettyprint(problem)} as a known {trac} problem")

                return

            successors = []
            if tractability == Tractability.TRACTABLE:
                successors = self.get_natural_reductions(current_problem)
                successors.extend(self.get_user_reductions(current_problem))
            else:
                successors = self.get_natural_antireductions(current_problem)
                successors.extend(self.get_user_antireductions(current_problem))

            for succ in successors:
                if succ not in visited:
                    previous[succ] = current_problem
                    visited[succ] = True
                    stack.append(succ)

        print("No solution found")

    # Exploration functions
    def open_problems(self, impact=False):
        self._saturate_check()

        print("Currently open problems:")
        currently_open_problems = []
        for problem in self._parameters_powerset():
            if problem not in self.intractable and problem not in self.tractable:
                currently_open_problems.append(problem)

        if len(currently_open_problems) == 0:
            print("No open problem found, congratulation!")
            return

        if not impact:
            print("".join(map(lambda p: "- " + self.frozenset_prettyprint(p) + "\n", currently_open_problems)))

        else:
            self.registered_impacts = [frozenset()]
            for id, problem in zip(range(1, len(currently_open_problems)), currently_open_problems):
                problem_impact = self.impact(problem)
                print(f"{id} - {self.frozenset_prettyprint(problem)} ({len(problem_impact['tractable'])}/{len(problem_impact['intractable'])})")
                self.registered_impacts.append({"problem": problem, "problems_list": problem_impact})

    def impact(self, problem):
        newly_solved = {}

        for tractability in [Tractability.TRACTABLE, Tractability.INTRACTABLE]:
            solved_by = {}
            stack = deque([problem])

            while len(stack) > 0:
                current_problem = stack.pop()

                if tractability == Tractability.INTRACTABLE:
                    successors = self.get_natural_reductions(current_problem)
                    successors.extend(self.get_user_reductions(current_problem))
                else:
                    successors = self.get_natural_antireductions(current_problem)
                    successors.extend(self.get_user_antireductions(current_problem))

                for succ in successors:
                    if succ not in self.tractable and \
                       succ not in self.intractable and \
                       succ not in solved_by:
                        solved_by[succ] = True
                        stack.append(succ)

            results = list(solved_by.keys())
            try:
                results.remove(problem)
            except ValueError:
                pass
            newly_solved[tractability.value] = results

        return newly_solved

    def print_known_impact(self, id):
        if len(self.registered_impacts) == 0:
            print("Please run command open impact first")
            return

        if not id > 0 or id >= len(self.registered_impacts):
            print(f"Invalid problem id. Must be between 0 and {len(self.registered_impacts)}")
            return

        problem = self.registered_impacts[id]["problem"]
        problems_list = self.registered_impacts[id]["problems_list"]

        for tractability in ["tractable", "intractable"]:
            print(f"Problems that are {tractability} assuming {self.frozenset_prettyprint(problem)} is {tractability}:")
            print("".join(map(lambda p: "- " + self.frozenset_prettyprint(p) + "\n", problems_list[tractability])))

    def print_impact(self, problem):
        if not self.check_parameters_validity(problem):
            return

        self._saturate_check()

        problems_list = self.impact(problem)

        for tractability in ["tractable", "intractable"]:
            print(f"Problems that are {tractability} assuming {self.frozenset_prettyprint(problem)} is {tractability}:")
            print("".join(map(lambda p: "- " + self.frozenset_prettyprint(p) + "\n", problems_list[tractability])))

    def _saturate_check(self):
        print("The database must be saturated first")
        print("Saturate ? [Y/n]")
        do_saturate = prompt(yesno=True)
        if do_saturate:
            self.saturate(verbose=1)
        else:
            print("Skipping database saturation. Warning: unexpected results may ensue!")

    def _parameters_powerset(self):
        val_to_param = list(self.parameters)

        for v in range(1, 2 ** len(self.parameters)):
            problem = set()
            for i in range(len(self.parameters)):
                if v & (1 << i):
                    problem.add(val_to_param[i])

            yield frozenset(problem)

    def saturate(self, verbose=2):
        if verbose > 1:
            print("Saturating database...")
        counts = {"tractable": 0, "intractable": 0}
        for tractability in [Tractability.TRACTABLE, Tractability.INTRACTABLE]:
            if verbose >= 2:
                print(f"Searching for {tractability.value} problems...")
            newly_found = self._percolate(tractability)
            if len(newly_found) > 0:
                new_problems = "- ".join(map(lambda p: self.frozenset_prettyprint(p) + "\n", newly_found))
                if verbose >= 2:
                    print(f"Newly found {tractability.value} problems:\n {new_problems}")
                counts[tractability.value] = len(newly_found)
            else:
                if verbose >= 2:
                    print(f"No new {tractability.value} problem found")

        if verbose >= 1:
            print(f"Added {counts['tractable']} tractable and {counts['intractable']} intractable problems to database")

    # Find all problems for which we have a solution
    def _percolate(self, tractability):
        if tractability not in [Tractability.INTRACTABLE, Tractability.TRACTABLE]:
            return

        newly_found = []
        visited = [self.tractable, self.intractable][tractability == Tractability.INTRACTABLE]
        stack = deque(visited.keys())

        while len(stack) > 0:
            current_problem = stack.pop()

            if tractability == Tractability.INTRACTABLE:
                successors = self.get_natural_reductions(current_problem)
                successors.extend(self.get_user_reductions(current_problem))
            else:
                successors = self.get_natural_antireductions(current_problem)
                successors.extend(self.get_user_antireductions(current_problem))

            for succ in successors:
                if succ not in visited:
                    visited[succ] = True
                    stack.append(succ)
                    newly_found.append(succ)

        return newly_found

    # Save and load
    def save(self, name):
        data = {"name": self.name,
                "parameters": self.serialize_frozenset(self.parameters),
                "reductions": self.serialize_dic(self.reductions),
                "antireductions": self.serialize_dic(self.antireductions),
                "tractable": self.serialize_dic(self.tractable),
                "intractable": self.serialize_dic(self.intractable)}

        data_json = json.dumps(data, indent=4)

        try:
            f = open(name, "w+")
            f.write(data_json)
            f.close()
        except (IOError, OSError) as e:
            print(f"Error saving file: {e}")
            return

        print(f"Saved file {name}")

    def load(self, name):
        try:
            f = open(name, "r+")
        except (OSError, IOError):
            print(f"File not found: {name}")
            return

        try:
            data_json = json.loads(f.read())
        except:
            print("Corrupted problem data file")
            return

        self.name = data_json["name"]
        self.parameters = self.deserialize_frozenset(data_json["parameters"])
        self.reductions = self.deserialize_dic(data_json["reductions"])
        self.antireductions = self.deserialize_dic(data_json["antireductions"])
        self.tractable = self.deserialize_dic(data_json["tractable"])
        self.intractable = self.deserialize_dic(data_json["intractable"])

        print(f"Successfully loaded file {name}")



    def serialize_dic(self, dic):
        return self.deep_map_dic(dic, self.serialize_frozenset)

    def serialize_frozenset(self, s):
        return " ".join(sorted(list(s)))

    def deserialize_dic(self, sdic):
        return self.deep_map_dic(sdic, self.deserialize_frozenset)

    def deserialize_frozenset(self, s):
        return frozenset(s.split())

    def deep_map_dic(self, dic, fun):
        new_dic = {}

        for key, val in dic.items():
            new_key = fun(key)
            new_val = val
            if isinstance(val, list):
                # Either we are serializing or deserializing, respectively
                if len(val) > 0 and (isinstance(val[0], frozenset) or isinstance(val[0], str)):
                    new_val = list(map(fun, val))
            new_dic[new_key] = new_val

        return new_dic

    # Utils
    def check_parameters_validity(self, param_list):
        for param in param_list:
            if param not in self.parameters:
                print(f"Error: unknown parameter {param}")
                return False

        return True

    def normalize_parameters(self, params):
        return " ".join(sorted(params))

    def frozenset_prettyprint(self, s):
        content = ", ".join(sorted(list(s)))
        return f"{{{content}}}"


def prompt(yesno=False):
    print("> ", end="")
    line = input()
    while yesno:
        if line.lower() == "no" or line.lower() == "n":
            return False
        elif line.lower() == "yes" or line.lower() == "y" or line == "":
            return True
        else:
            print(f"Invalid value: {line}")
            line = input()
            continue
    return line


def main():
    print(f"Parameterized problem finder v{VERSION}")
    problem = None
    if args.filename:
        problem = ParameterizedProblem()
        problem.load(args.filename)

    while True:
        command = prompt().split()

        if len(command) == 0:
            continue

        if command[0] == "help":
            print("Commands:\n"
                  " init [guided] - Initialize a parameterized problem. Add option \"guided\" for help with the"
                  " syntax\n"
                  " add tractable|intractable|reduction - Specify the tractability of a problem,"
                  "or add a known reduction. You will be prompted the problem or reduction to add.\n"
                  " solve tractable|intractable [params..] - Check if a problem's tractability is known or can be"
                  " deduced\n"
                  " saturate - Try to solve as many problems are possible\n"
                  " open [impact] - Show all open problems, and the consequences of solving them if option \"impact\""
                  " is specified \n"
                  " impact [id|[params..]] - Shows which problems would be solved by solving another problem. If command"
                  " open impact was run before, the id of the problem can be specified. Otherwise, a list of parameters"
                  " can be given"
                  " save filename - Save the current state in a file\n"
                  " load filename - Load a parameterized problem\n"
                  "Format:\n"
                  " [params..] - List of parameters, with whitespace \" \" as separator\n"
                  " [reduction] - List of parameters separated by character \">\""
                  )

        elif command[0] == "init":
            problem = ParameterizedProblem()
            guided = False
            if len(command) > 1 and (command[1] == "g" or command[1] == "guided"):
                guided = True
            problem.manual_initialization(guided=guided)

        elif command[0] == "add":
            if problem is None:
                print("You must initialize the problem first")
                continue

            if len(command) > 1:
                if command[1] == "tractable":
                    print("Problem: ", end="")
                    problem.add_problem(Tractability.TRACTABLE)
                elif command[1] == "intractable":
                    print("Problem: ", end="")
                    problem.add_problem(Tractability.INTRACTABLE)
                elif command[1] == "reduction":
                    problem.add_reduction()
            else:
                print("Usage: add tractable|intractable|reduction")

        elif command[0] == "solve":
            if len(command) > 2:
                current_parameters = frozenset(command[2:])
                if command[1] == "intractable":
                    problem.solve(current_parameters, tractability=Tractability.INTRACTABLE)
                    continue
                elif command[1] == "tractable":
                    problem.solve(current_parameters, tractability=Tractability.TRACTABLE)
                    continue
                else:
                    print(f"Unknown value: {command[1]}")
            else:
                print("Usage: solve tractable|intractable params*")
                continue

        elif command[0] == "saturate":
            if problem is None:
                print("You must initialize the problem first")
                continue
            problem.saturate()

        elif command[0] == "open":
            if problem is None:
                print("You must initialize the problem first")
                continue
            if len(command) > 1 and command[1] == "impact":
                problem.open_problems(impact=True)
            else:
                problem.open_problems()

        elif command[0] == "impact":
            if problem is None:
                print("You must initialize the problem fist")
                continue
            if len(command) > 1:
                if command[1].isdigit():
                    problem.print_known_impact(int(command[1]))
                else:
                    current_parameters = frozenset(command[1:])
                    problem.print_impact(current_parameters)

        elif command[0] == "save":
            if len(command) > 1:
                problem.save(command[1])
            else:
                print("You must specify a file name")

        elif command[0] == "load":
            if len(command) > 1:
                problem = ParameterizedProblem()
                problem.load(command[1])
            else:
                print("You must specify a file name")

        elif command[0] == "exit":
            print("Goodbye!")
            return 0

        else:
            print("Unknown command")


if __name__ == "__main__":
    main()
