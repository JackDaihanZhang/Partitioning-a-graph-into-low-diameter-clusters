import gurobipy as gp
from gurobipy import GRB


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
