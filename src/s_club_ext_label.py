import sys
import gurobipy as gp
from gurobipy import GRB
import networkx as nx
import callback
from check_solution import check_solution


# The implementation of the extended labeling formulation in section 4 with the
# diameter-bounding constraint being inequality (10) in section 4.1
def solve_s_club_ext_label(G, s, potential_roots, clusters, max_k):
    # Calculate power graph and its complement
    H = nx.power(G, s)
    H_c = nx.complement(H)

    # Initialize the model
    m = gp.Model()

    # Set the time limit
    m.Params.TimeLimit = 3600

    # Attach parameters to the model
    m._graph = G
    m._s = s
    m._k = max_k

    # Initialize the variables - (7.f)
    m._X = m.addVars(G.nodes, range(max_k), vtype=GRB.BINARY)
    m._Y = m.addVars(range(max_k), vtype=GRB.CONTINUOUS)

    # Set the objective function - (7.a)
    m.setObjective(gp.quicksum(m._Y), GRB.MINIMIZE)

    # Assignment constraints - (7.b)
    m.addConstrs(gp.quicksum(m._X[v, j] for j in range(max_k)) == 1 for v in G.nodes)

    # Coupling constraints - (7.c)
    m.addConstrs(m._X[v, j] <= m._Y[j] for v in G.nodes for j in range(max_k))

    # Sequential constraints - (7.d)
    m._Y[0].ub = 1
    m.addConstrs(m._Y[j] >= m._Y[j + 1] for j in range(max_k - 1))

    ###########################################################################################
    # Fixing and ordering procedures
    ###########################################################################################
    # One-fixing
    for j in range(len(potential_roots)):
        m._Y[j].lb = 1
        m._X[potential_roots[j], j].lb = 1
    for j in range(len(potential_roots)):
        m._Y[j].lb = 1

    # Zero-fixing
    for j in range(len(potential_roots)):
        for vertex in G.nodes:
            if vertex in H_c.neighbors(potential_roots[j]):
                m._X[vertex, j].ub = 0

    ###########################################################################################
    # Warm start MIP with variable clusters calculated by using heuristic.py
    ###########################################################################################

    # Warm starting with nodes belonging to partitions containing potential root
    if len(clusters) != 0:
        index_of_clusters = len(potential_roots) - 1

        for cluster in clusters:
            flag = False

            # If there is a potential root inside the cluster, this number does not grow
            for j in range(len(potential_roots)):
                if potential_roots[j] in cluster:
                    flag = True
                    for vertex in cluster:
                        m._X[vertex, j].start = 1

            # If it's not, create a new one
            if not flag:
                index_of_clusters += 1
                for vertex in cluster:
                    m._X[vertex, index_of_clusters].start = 1

    ###########################################################################################
    # Solve the MIP and check the solution
    ###########################################################################################

    # Optimize the model
    m.Params.MIPFocus = 3
    m.Params.lazyConstraints = 1
    m.optimize(callback.labeling_callback)

    if m.solCount > 0:
        # Check the solution
        partitions = [[vertex for vertex in G.nodes if m._X[vertex, j].x > 0.5] for j in range(max_k) if m._Y[j].x > 0.5]
        valid_solution = check_solution(G, s, partitions)
        if valid_solution:
            return m.objVal, m.ObjBound, m.Status
        else:
            print("The obtained solution from solve_s_club_ext_label is invalid")
            sys.exit()


# Implements the extended labeling formulation with divide and conquer
def solve_s_club_ext_label_with_divide_and_conquer(G, s, potential_roots, max_k):
    # Create a power graph and its complement
    H = nx.power(G, s)
    H_c = nx.complement(H)

    # Initialize the model
    m = gp.Model()

    # Set the parameters
    m.Params.TimeLimit = 3600
    m.Params.MIPFocus = 3

    # Attach the parameters to the model
    m._graph = G
    m._s = s
    m._max_k = max_k

    # Add variables - (7.f)
    m._X = m.addVars(G.nodes, max_k, vtype=GRB.BINARY)

    # Set modified objective function - (7.a)
    m.setObjective(gp.quicksum(m._X), GRB.MAXIMIZE)

    # Assignment constraints - (7.b)
    m.addConstrs(gp.quicksum(m._X[v, j] for j in range(max_k)) == 1 for v in G.nodes)

    ###########################################################################################
    # Fixing and ordering procedures
    ###########################################################################################

    # One-fixing
    for j in range(len(potential_roots)):
        m._X[potential_roots[j], j].lb = 1

    # Zero-fixing
    for j in range(len(potential_roots)):
        for vertex in G.nodes:
            if vertex in H_c.neighbors(potential_roots[j]):
                m._X[vertex, j].ub = 0

    # Initialize a boolean variable indicating whether optimality has been reached in the divide-and-
    # conquer procedure
    flag = False

    # Initialize the variable "first" as the lower bound minus one and the variable "last" as the
    # upper bound
    first = len(potential_roots) - 1
    last = max_k

    # Define a counter variable for the binary-search iterations that returns at least one feasible solution
    feasible_counter = 0

    # Define a variable storing the partition corresponding to the current best objective
    current_best_partition = []

    # While the optimal objective has not been found
    while not flag:
        # Take the middle point
        middle = int((last + first) / 2)

        # Print iteration values
        print("First:", first)
        print("Middle:", middle)
        print("Last:", last)

        # Try to solve the restricted problem with the objective fixed to the value of the variable "middle"
        partitions_new_iter, status = solve_restricted_s_club_label(m, middle)

        # Update the variables if the iteration finds at least one feasible solution
        if len(partitions_new_iter) > 0:
            current_best_partition = partitions_new_iter
            feasible_counter += 1
        # Update the binary search parameters
        if status == GRB.INFEASIBLE:
            first = middle  # If middle is impossible, update first
        elif status == GRB.OPTIMAL:
            last = middle  # If middle is possible, update last
        elif status == GRB.TIME_LIMIT:
            flag = True  # If time limit was reached, ends the iteration

        if last - first <= 1: flag = True


    # Check the solution
    if status in [GRB.INFEASIBLE, GRB.OPTIMAL, GRB.TIME_LIMIT]:
        if feasible_counter > 0:
            valid_solution = check_solution(G, s, current_best_partition)
            if not valid_solution:
                print("The solution obtained from solve_s_club_ext_label_with_divide_and_conquer is invalid.")
                sys.exit()
        return last, first, status
    else:
        print("Invalid model status in solve_s_club_ext_label_with_divide_and_conquer")
        sys.exit()


# Solved the extended labeling formulation for a given objective valud (solve for feasibility)
def solve_restricted_s_club_label(m, k):
    # Retrieve the parameters
    G = m._graph
    max_k = m._max_k
    m._k = k

    # Adding constraints to ensure that the objective is fixed to the given one
    restriction = m.addConstrs(gp.quicksum(m._X[v, j] for v in G.nodes) >= 1 for j in range(k))
    for v in G.nodes:
        for j in range(k, max_k):
            m._X[v, j].ub = 0

    # Optimize the model
    m.Params.lazyConstraints = 1
    m.optimize(callback.restricted_labeling_callback)
    status = m.Status

    if m.solCount > 0:
        partitions = [[v for v in G.nodes if m._X[v, j].x > 0.5] for j in range(k)]
    else:
        partitions = []

    # Remove the added constraints and update the model
    for v in G.nodes:
        for j in range(k, max_k):
            m._X[v, j].ub = 1
    m.remove(restriction)
    m.update()

    return partitions, status
