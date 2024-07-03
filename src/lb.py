import time
import gurobipy as gp
from gurobipy import GRB, LinExpr
import networkx as nx


# Solve the maximum independent set problem
def find_max_indep_set(H):
    # Initialize the model
    m = gp.Model()

    # Add variables
    y = m.addVars(H.nodes, vtype=GRB.BINARY)

    # Set objective function
    m.setObjective(gp.quicksum(y), GRB.MAXIMIZE)

    # Add constraints
    m.addConstrs(y[i] + y[j] <= 1 for (i, j) in H.edges)

    # Set parameters
    m.Params.timeLimit = 180  # 60-second time limit

    # Optimize model
    m.optimize()

    if m.status == GRB.OPTIMAL or m.status == GRB.TIME_LIMIT:
        # Get the solution
        return [i for i in H.nodes if y[i].x > 0.5]
    else:
        return "Model status != optimal"

'''
# solve minimum clique covering problem (Formulation 11 - Section 4.1.1)
def find_min_union_cliques(H):
    # Set model
    m = gp.Model()
    clique_finding_start = time.time()
    # Find all maximal clique list
    C = list(nx.find_cliques(H))
    # Delete this line after experiments
    num_max_clique = len(C)
    clique_finding_end = time.time()
    clique_finding_time = clique_finding_end - clique_finding_start
    # Add variables - (11.c)
    Y = m.addVars(range(len(C)), vtype=GRB.BINARY)

    # Set objective function - (11.a)
    m.setObjective(gp.quicksum(Y[index] for index in range(len(C))), GRB.MINIMIZE)

    # Create a linear expression for every node
    expr = [LinExpr() for _ in H.nodes]

    # Cover constraints - (11.b)
    for index_clique in range(len(C)):
        for vertex in C[index_clique]:
            expr[vertex] += Y[index_clique]
    m.addConstrs(expr[i] >= 1 for i in H.nodes)

    # Set parameters
    m.Params.timeLimit = 180  # 180-second time limit

    # Optimize model
    clique_cover_start = time.time()
    m.optimize()
    clique_cover_end = time.time()
    # Get rid of this if decided to be unnecessary after the experiments
    clique_cover_time = clique_cover_end - clique_cover_start

    if m.status == GRB.OPTIMAL or m.status == GRB.TIME_LIMIT:
        # Get the solution
        return min(m.objVal, int(m.ObjBound)), clique_finding_time, clique_cover_time, num_max_clique
    else:
        return "Model status != optimal"
'''
