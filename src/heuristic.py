import sys
from check_solution import check_solution
import gurobipy as gp
from gurobipy import GRB, LinExpr
import networkx as nx


# The code in this file corresponds to the upper-bound calculation in section 3.2
# When s is even (section 3.2.1)
def calculate_UB_even(G, s):
    # Phase I (the minimum dominating set problem)
    # Initialize the model
    m = gp.Model()

    # Creating the s/2 power graph
    r = int(s / 2)
    G_r = nx.power(G, r)

    # Add the variables
    z = m.addVars(G_r.nodes, vtype=GRB.BINARY)

    # Set the objective function
    m.setObjective(gp.quicksum(z[i] for i in G_r.nodes), GRB.MINIMIZE)

    # Covering constraints
    m.addConstrs(z[i] + gp.quicksum(z[j] for j in G_r.neighbors(i)) >= 1 for i in G_r.nodes)

    # Set the parameters
    m.Params.timeLimit = 60  # 60-second time limit
    m.Params.method = 3  # Concurrent method

    # Optimize the model
    m.optimize()

    # Retrieve the solution if solved to optimality and retrieve the best feasible solution if the
    # time limit is reached
    if m.status == GRB.OPTIMAL or m.status == GRB.TIME_LIMIT:
        # Phase II (algorithm 2, an assignment algorithm)
        nx.set_node_attributes(G, False, "assigned")
        partitions = [[j] for j in G.nodes if z[j].x > 0.5]
        for vertex in G.nodes:
            if z[vertex].x > 0.5:
                G.nodes[vertex]["assigned"] = True
        for i in range(r):
            G_i = nx.power(G, i + 1)
            for partition in partitions:
                for vertex in G_i.neighbors(partition[0]):
                    if not G.nodes[vertex]["assigned"]:
                        partition.append(vertex)
                        G.nodes[vertex]["assigned"] = True

        # Check the solution
        valid_solution = check_solution(G, s, partitions)
        if valid_solution:
            return partitions
        else:
            print("The obtained solution from calculate_UB_even is not feasible")
            sys.exit()
    else:
        print("Unexpected model status from calculate_UB_even")
        sys.exit()


# When s is odd (section 3.2.2)
def calculate_UB_odd(G, s):
    # Solves the IP in Phase I
    # Initialize the model
    m = gp.Model()

    # Find the diameter and take the power graph
    d = s - 2
    H = nx.power(G, d)

    # Create a list of the set of maximal cliques in H
    cliques = list(nx.find_cliques(H))

    # Add the variables
    Y = m.addVars(range(len(cliques)), vtype=GRB.BINARY)

    # Set the objective function
    m.setObjective(gp.quicksum(Y[index] for index in range(len(cliques))), GRB.MINIMIZE)

    # Create a linear expression for every node that corresponds to the LHS of (6b)
    expr = [LinExpr() for _ in G.nodes]
    for index in range(len(cliques)):
        # If the vertex belongs to the clique, add the Y variable corresponding to the clique to the vertex's LinExpr
        for vertex in cliques[index]:
            expr[vertex] += Y[index]
        # If the vertex is connected to the clique in G, add the Y variable corresponding to the clique to vertex's
        # LinExpr
        for vertex in nx.node_boundary(G, cliques[index], None):
            expr[vertex] += Y[index]

    # Add constraint (6b)
    m.addConstrs(expr[i] >= 1 for i in G.nodes)

    # Set the parameters
    m.Params.timeLimit = 60  # 60-second time limit

    # Optimize the model
    m.optimize()

    # Retrieve the solution
    if m.status == GRB.OPTIMAL or m.status == GRB.TIME_LIMIT:
        # Add the attribute "assigned" to the vertices in G
        nx.set_node_attributes(G, False, "assigned")

        # Create the clusters from the solution
        clusters = []
        for index in range(len(cliques)):
            if Y[index].x > 0.5:
                cluster = []
                for vertex in cliques[index]:
                    if not G.nodes[vertex]["assigned"]:
                        cluster.append(vertex)
                        G.nodes[vertex]["assigned"] = True
                clusters.append(cluster)

        # Starts the phase II BFS-like assignment procedure which converts clusters into valid partitions
        partitions = [cluster.copy() for cluster in clusters]

        # Add the clusters' neighbors to the clusters themselves
        for index in range(len(clusters)):
            # For each cluster, add its boundary to itself
            for vertex in clusters[index]:
                for neighbor in G.neighbors(vertex):
                    # If it isn't assigned, add to the cluster and assigns it
                    if not G.nodes[neighbor]["assigned"]:
                        partitions[index].append(neighbor)
                        G.nodes[neighbor]["assigned"] = True

        # Check the solution
        valid_solution = check_solution(G, s, partitions)
        if valid_solution:
            return partitions
        else:
            print("The obtained solution from calculate_UB_odd is not feasible")
            sys.exit()
    else:
        print("Unexpected model status from calculate_UB_odd")
        sys.exit()


'''    
#Iteratively applies the maximum independent union of cliques algorithm
def iteratively_max_IUC(G):
    sub_G = G
    cliques = []
    
    while len(sub_G.nodes) > 0:
        sub_cliques = indep_union_cliques.find_max_IUC(sub_G)
        
        remove_from_sub_G = []
        for sub_clique in sub_cliques:
            remove_from_sub_G.extend(sub_clique)
        nodes = [v for v in sub_G.nodes if v not in remove_from_sub_G]
        
        sub_G = nx.subgraph(G, nodes)
        cliques.extend(sub_cliques)
        
    return cliques
'''

'''
#Brute force correction
def brute_force_correction(G, solution, repetitions, position):
    new_solution = {v: [i for i in solution[v]] for v in list(solution.keys())}
    new_repetitions = [[i for i in repetitions[v]] for v in G.nodes]
    
    print("Position:", position)
    
    if (position != len(repetitions)):
        print(repetitions[position])
        for cluster in repetitions[position]:
            works_flag = True
            for removing_cluster in repetitions[position]:
                if cluster != removing_cluster:
                    new_solution[removing_cluster].remove(position)
                    new_repetitions[position].remove(removing_cluster)
                    
                    testing_graph = G.subgraph(new_solution[removing_cluster])
                    if (nx.is_connected(testing_graph)):
                        if (nx.diameter(testing_graph)) > 3:
                            works_flag = False
                    else:
                        works_flag = False
                       
            if works_flag:
                result = brute_force_correction(G, new_solution, new_repetitions, position+1)
                if result:
                    return result
            
            for removing_cluster in repetitions[position]:
                if cluster != removing_cluster:
                    new_solution[removing_cluster].append(position)
                    new_repetitions[position].append(removing_cluster)
        
        print("Cut!!!")
        return None
    else:
        print("Achieves!!!")
        return new_solution
'''
