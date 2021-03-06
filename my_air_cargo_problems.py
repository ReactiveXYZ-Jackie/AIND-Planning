from aimacode.logic import PropKB
from aimacode.planning import Action
from aimacode.search import (
    Node, Problem,
)
from aimacode.utils import expr
from lp_utils import (
    FluentState, encode_state, decode_state,
)
from my_planning_graph import PlanningGraph


class AirCargoProblem(Problem):
    def __init__(self, cargos, planes, airports, initial: FluentState, goal: list):
        """

        :param cargos: list of str
            cargos in the problem
        :param planes: list of str
            planes in the problem
        :param airports: list of str
            airports in the problem
        :param initial: FluentState object
            positive and negative literal fluents (as expr) describing initial state
        :param goal: list of expr
            literal fluents required for goal test
        """
        self.state_map = initial.pos + initial.neg
        self.initial_state_TF = encode_state(initial, self.state_map)
        Problem.__init__(self, self.initial_state_TF, goal=goal)
        self.cargos = cargos
        self.planes = planes
        self.airports = airports
        self.actions_list = self.get_actions()

    def get_actions(self):
        '''
        This method creates concrete actions (no variables) for all actions in the problem
        domain action schema and turns them into complete Action objects as defined in the
        aimacode.planning module. It is computationally expensive to call this method directly;
        however, it is called in the constructor and the results cached in the `actions_list` property.

        Returns:
        ----------
        list<Action>
            list of Action objects
        '''

        # TODO create concrete Action objects based on the domain action schema for: Load, Unload, and Fly
        # concrete actions definition: specific literal action that does not include variables as with the schema
        # for example, the action schema 'Load(c, p, a)' can represent the concrete actions 'Load(C1, P1, SFO)'
        # or 'Load(C2, P2, JFK)'.  The actions for the planning problem must be concrete because the problems in
        # forward search and Planning Graphs must use Propositional Logic

        def load_actions():
            '''Create all concrete Load actions and return a list

            :return: list of Action objects
            '''
            loads = []
            # TODO create all load ground actions from the domain Load action
            
            # for all airport
            for airport in self.airports:
                # for all planes
                for plane in self.planes:
                    # for all cargos:
                    for cargo in self.cargos:
                        # init precondition
                        # At(cargo, a) and At(plane, airport)
                        precond_pos = [
                            expr("At({}, {})".format(cargo, airport)),
                            expr("At({}, {})".format(plane, airport))
                        ]
                        precond_neg = []
                        # init effects
                        # In(cargo, plane)
                        effect_pos = [
                            expr("In({}, {})".format(cargo, plane))
                        ]
                        # not At(cargo, airport)
                        effect_neg = [
                            expr("At({}, {})".format(cargo, airport))
                        ]
                        # init action
                        load = Action(
                                expr("Load({}, {}, {})".format(cargo, plane, airport)),
                                [ precond_pos, precond_neg ],
                                [ effect_pos, effect_neg ]
                            )
                        # append action to loads
                        loads.append(load);

            return loads

        def unload_actions():
            '''Create all concrete Unload actions and return a list

            :return: list of Action objects
            '''
            unloads = []
            # TODO create all Unload ground actions from the domain Unload action
            
            # for all airports
            for airport in self.airports:
                # for all planes
                for plane in self.planes:
                    # for all cargos
                    for cargo in self.cargos:
                        # init preconditions
                        # In(cargo, plane) and At(plane, airport)
                        precond_pos = [
                            expr("In({}, {})".format(cargo, plane)),
                            expr("At({}, {})".format(plane, airport))
                        ]
                        precond_neg = []
                        # init effects 
                        # At(cargo, airport)
                        effect_pos = [
                            expr("At({}, {})".format(cargo, airport))
                        ]
                        # not In(cargo, plane)
                        effect_neg = [
                            expr("In({}, {})".format(cargo, plane))
                        ]
                        # init action
                        unload = Action(
                                expr("Unload({}, {}, {})".format(cargo, plane, airport)),
                                [ precond_pos, precond_neg ],
                                [ effect_pos, effect_neg ]
                            )
                        # append action to unloads
                        unloads.append(unload)
            
            return unloads

        def fly_actions():
            '''Create all concrete Fly actions and return a list

            :return: list of Action objects
            '''
            flys = []
            for fr in self.airports:
                for to in self.airports:
                    if fr != to:
                        for p in self.planes:
                            precond_pos = [expr("At({}, {})".format(p, fr)),
                                           ]
                            precond_neg = []
                            effect_add = [expr("At({}, {})".format(p, to))]
                            effect_rem = [expr("At({}, {})".format(p, fr))]
                            fly = Action(expr("Fly({}, {}, {})".format(p, fr, to)),
                                         [precond_pos, precond_neg],
                                         [effect_add, effect_rem])
                            flys.append(fly)
            return flys

        return load_actions() + unload_actions() + fly_actions()

    def actions(self, state: str) -> list:
        """ Return the actions that can be executed in the given state.

        :param state: str
            state represented as T/F string of mapped fluents (state variables)
            e.g. 'FTTTFF'
        :return: list of Action objects
        """
        # decode current state
        current_state = decode_state(state, self.state_map)
        # extract current boolean statuses
        current_pos = current_state.pos
        current_neg = current_state.neg

        def check_precond(action): 
            # check if current state has satisfied the preconditions of this action
            for condition in action.precond_pos:
                if condition not in current_pos:
                    return False
            for condition in action.precond_neg:
                if condition not in current_neg:
                    return False
            return True

        return [action for action in self.actions_list if check_precond(action)]

    def result(self, state: str, action: Action):
        """ Return the state that results from executing the given
        action in the given state. The action must be one of
        self.actions(state).

        :param state: state entering node
        :param action: Action applied
        :return: resulting state after action
        """
        # decode the previous state
        previous_state = decode_state(state, self.state_map)
        previous_pos = previous_state.pos
        previous_neg = previous_state.neg
        # try modify previous boolean conjunctions with the effect of action
        for added in action.effect_add:
            previous_pos.append(added)
            if added in previous_neg:
                previous_neg.remove(added)
        for removed in action.effect_rem:
            if removed in previous_pos:
                previous_pos.remove(removed)
            previous_neg.append(removed)
        # construct new FluentState from modified data
        return encode_state(FluentState(previous_pos, previous_neg), self.state_map)

    def goal_test(self, state: str) -> bool:
        """ Test the state to see if goal is reached

        :param state: str representing state
        :return: bool
        """
        # decode the previous state
        previous_state = decode_state(state, self.state_map).pos
        # check if the previous state satifies the goal state
        for condition in self.goal:
            if condition not in previous_state:
                return False
        return True


    def h_1(self, node: Node):
        # note that this is not a true heuristic
        h_const = 1
        return h_const

    def h_pg_levelsum(self, node: Node):
        '''
        This heuristic uses a planning graph representation of the problem
        state space to estimate the sum of all actions that must be carried
        out from the current state in order to satisfy each individual goal
        condition.
        '''
        pg = PlanningGraph(self, node.state)
        pg_levelsum = pg.h_levelsum()
        return pg_levelsum

    def h_ignore_preconditions(self, node: Node):
        '''
        This heuristic estimates the minimum number of actions that must be
        carried out from the current state in order to satisfy all of the goal
        conditions by ignoring the preconditions required for an action to be
        executed.
        '''

        # extract all queries that are in the goal and are not positive
        # TODO: try implementing the greedy set cover algorithm
        queries = [ q for q in self.goal if q not in decode_state(node.state, self.state_map).pos]

        return len(queries)


def air_cargo_p1() -> AirCargoProblem:
    cargos = ['C1', 'C2']
    planes = ['P1', 'P2']
    airports = ['JFK', 'SFO']
    pos = [
            expr('At(C1, SFO)'),
            expr('At(C2, JFK)'),
            expr('At(P1, SFO)'),
            expr('At(P2, JFK)'),
        ]
    neg = [
            expr('At(C2, SFO)'),
            expr('In(C2, P1)'),
            expr('In(C2, P2)'),
            expr('At(C1, JFK)'),
            expr('In(C1, P1)'),
            expr('In(C1, P2)'),
            expr('At(P1, JFK)'),
            expr('At(P2, SFO)'),
        ]
    init = FluentState(pos, neg)
    goal = [
            expr('At(C1, JFK)'),
            expr('At(C2, SFO)'),
        ]
    return AirCargoProblem(cargos, planes, airports, init, goal)


def air_cargo_p2() -> AirCargoProblem:
    cargos = ['C1', 'C2', 'C3']
    planes = ['P1', 'P2', 'P3']
    airports = ['JFK', 'SFO', 'ATL']
    pos = [
            expr('At(C1, SFO)'),
            expr('At(C2, JFK)'),
            expr('At(C3, ATL)'),
            expr('At(P1, SFO)'),
            expr('At(P2, JFK)'),
            expr('At(P3, ATL)')
        ]
    neg = [
            expr('At(C2, SFO)'),
            expr('At(C2, ATL)'),
            expr('In(C2, P1)'),
            expr('In(C2, P2)'),
            expr('In(C2, P3)'),
            expr('At(C1, JFK)'),
            expr('At(C1, ATL)'),
            expr('In(C1, P1)'),
            expr('In(C1, P2)'),
            expr('In(C1, P3)'),
            expr('At(C3, JFK)'),
            expr('At(C3, SFO)'),
            expr('In(C3, P1)'),
            expr('In(C3, P2)'),
            expr('In(C3, P3)'),
            expr('At(P1, ATL)'),
            expr('At(P1, ATL)'),
            expr('At(P2, SFO)'),
            expr('At(P2, ATL)'),
            expr('At(P3, JFK)'),
            expr('At(P3, SFO)')
           ]
    init = FluentState(pos, neg)
    goal = [
            expr('At(C1, JFK)'),
            expr('At(C2, SFO)'),
            expr('At(C3, SFO)')
        ]

    return AirCargoProblem(cargos, planes, airports, init, goal)


def air_cargo_p3() -> AirCargoProblem:
    cargos = ['C1', 'C2', 'C3', 'C4']
    planes = ['P1', 'P2', ]
    airports = ['SFO', 'JFK', 'ATL', 'ORD']
    pos = [
            expr('At(C1, SFO)'),
            expr('At(C2, JFK)'),
            expr('At(C3, ATL)'),
            expr('At(C4, ORD)'),
            expr('At(P1, SFO)'),
            expr('At(P2, JFK)'),
        ]
    neg = [
            expr('At(C1,JFK)'),
            expr('At(C1,ATL)'),
            expr('At(C1,ORD)'),
            expr('In(C1,P1)'),
            expr('In(C1,P2)'),
            expr('At(C2,SFO)'),
            expr('At(C2,ATL)'),
            expr('At(C2,ORD)'),
            expr('In(C2,P1)'),
            expr('In(C2,P2)'),
            expr('At(C3,SFO)'),
            expr('At(C3,JFK)'),
            expr('At(C3,ORD)'),
            expr('In(C3,P1)'),
            expr('In(C3,P2)'),
            expr('At(C4,SFO)'),
            expr('At(C4,JFK)'),
            expr('At(C4,ATL)'),
            expr('In(C4,P1)'),
            expr('In(C4,P2)'),
            expr('At(P1,JFK)'),
            expr('At(P1,ATL)'),
            expr('At(P1,ORD)'),
            expr('At(P2,SFO)'),
            expr('At(P2,ATL)'),
            expr('At(P2,ORD)'),
        ]
    init = FluentState(pos, neg)
    goal = [
            expr('At(C1,JFK)'),
            expr('At(C2,SFO)'),
            expr('At(C3,JFK)'),
            expr('At(C4,SFO)'),
        ]
    return AirCargoProblem(cargos, planes, airports, init, goal)
