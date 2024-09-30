import sys
import gurobipy as gp
from gurobipy import GRB
import networkx as nx
import callback
from check_solution import check_solution


# The implementation of the extended labeling formulation in section 4 with the
# diameter-bounding constraint being inequality (10) in section 4.1
def solve_s_club_ext_label(G, s, potential_roots, clusters, max_k, problem):
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
    if problem == "Partitioning":
        m.addConstrs(gp.quicksum(m._X[v, j] for j in range(max_k)) == 1 for v in G.nodes)
    else:
        m.addConstrs(gp.quicksum(m._X[v, j] for j in range(max_k)) >= 1 for v in G.nodes)

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