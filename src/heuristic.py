import sys
from check_solution import check_solution
import gurobipy as gp
from gurobipy import GRB, LinExpr
import networkx as nx
import copy


# The code in this file corresponds to the upper-bound calculation in section 3.2
# When s is even (section 3.2.1)
def calculate_UB_even(G, s, UB_mode, problem):
    # Creating the s/2 power graph
    r = int(s / 2)
    H = nx.power(G, r)

    if UB_mode == "IP":
        # Phase I (the minimum dominating set problem)
        # Initialize the model
        m = gp.Model()

        # Add the variables
        z = m.addVars(H.nodes, vtype=GRB.BINARY)

        # Set the objective function
        m.setObjective(gp.quicksum(z[i] for i in H.nodes), GRB.MINIMIZE)

        # Covering constraints
        m.addConstrs(z[i] + gp.quicksum(z[j] for j in H.neighbors(i)) >= 1 for i in H.nodes)

        # Set the parameters
        m.Params.timeLimit = 60  # 60-second time limit
        m.Params.method = 3  # Concurrent method
        m.Params.Presolve = 1

        # Optimize the model
        m.optimize()

        # Retrieve the solution if solved to optimality and retrieve the best feasible solution if the
        # time limit is reached
        if m.status == GRB.OPTIMAL or m.status == GRB.TIME_LIMIT:
            # Create the set D
            D = [j for j in G.nodes if z[j].x > 0.5]
        else:
            print("Unexpected model status from calculate_UB_even")
            sys.exit()
    elif UB_mode == "APX":
        U = set(G.nodes())
        D = []
        remaining_vertices = copy.deepcopy(list(G.nodes()))
        while U:
            print("U: ", U)
            # Step 4: Pick a vertex that maximizes |NH[v] ∩ U|
            best_vertex = None
            max_intersection_size = -1

            # Find all maximal cliques in the graph
            for v in remaining_vertices:

                closed_neighborhood = {v}.union(nx.node_boundary(H, {v}))

                # Compute the intersection with U
                intersection_size = len(closed_neighborhood.intersection(U))

                # Keep track of the clique with the maximum intersection
                if intersection_size > max_intersection_size:
                    best_vertex = v
                    max_intersection_size = intersection_size

            # Step 5: Add the selected maximal clique to cliques_list
            if best_vertex is not None:
                D.append(best_vertex)
            remaining_vertices.remove(best_vertex)

            # Step 6: Update U by removing all vertices in NH[v] from U
            closed_neighborhood_best_vertex = {best_vertex}.union(nx.node_boundary(H, {best_vertex}))
            # print("closed_neighborhood: ", closed_neighborhood_best_clique)
            U.difference_update(closed_neighborhood_best_vertex)

    else:
        print("Invalid UB_mode")
        sys.exit()
    # Starts the phase II BFS-like assignment to create valid partitions
    # Copy the graph and perform the BFS on the new copied graph
    G_new = copy.deepcopy(G)
    G_new.add_node('r')
    for i in D:
        G_new.add_edge('r', i)
    bfs_tree = nx.bfs_tree(G_new, source='r')
    # Create the partitions from the BFS tree
    T_minus_r = bfs_tree.copy()
    T_minus_r.remove_node('r')
    T_minus_r_undirected = T_minus_r.to_undirected()
    partitions = list(nx.connected_components(T_minus_r_undirected))
    partitions = [list(partition) for partition in partitions]
    # Check the solution
    valid_solution = check_solution(G, s, partitions, problem)
    if valid_solution:
        return partitions
    else:
        print("The obtained solution from calculate_UB_even is not feasible")
        sys.exit()


# When s is odd (section 3.2.2)
def calculate_UB_odd(G, s, UB_mode, problem):
    # Find the diameter and take the power graph
    d = (s - 1) // 2
    H = nx.power(G, d)

    # Create a list of the set of maximal cliques in H
    cliques = list(nx.find_cliques(G))

    selected_clique_list = []

    if UB_mode == "IP":
        # Solves the IP in Phase I
        # Initialize the model
        m = gp.Model()

        # Add the variables
        z = m.addVars(range(len(cliques)), vtype=GRB.BINARY)

        # Set the objective function
        m.setObjective(gp.quicksum(z[index] for index in range(len(cliques))), GRB.MINIMIZE)

        # Create a linear expression for every node that corresponds to the LHS of (6b)
        expr = [LinExpr() for _ in G.nodes]
        for index in range(len(cliques)):
            # If the vertex belongs to the clique, add the z variable corresponding to the clique to the vertex's LinExpr
            for vertex in cliques[index]:
                expr[vertex] += z[index]
            # If the vertex is connected to the clique in H, add the z variable corresponding to the clique to vertex's
            # LinExpr
            for vertex in nx.node_boundary(H, cliques[index], None):
                expr[vertex] += z[index]

        # Add constraint (6b)
        m.addConstrs(expr[i] >= 1 for i in G.nodes)

        # Set the parameters
        m.Params.timeLimit = 60  # 60-second time limit
        m.Params.method = 3  # Concurrent method
        m.Params.Presolve = 1

        # Optimize the model
        m.optimize()

        # Retrieve the solution
        if m.status == GRB.OPTIMAL or m.status == GRB.TIME_LIMIT:
            # Add the attribute "assigned" to the vertices in G
            nx.set_node_attributes(G, False, "assigned")

            # Create the cliques from the solution
            for index in range(len(cliques)):
                if z[index].x > 0.5:
                    clique = []
                    for vertex in cliques[index]:
                        if not G.nodes[vertex]["assigned"]:
                            clique.append(vertex)
                            G.nodes[vertex]["assigned"] = True
                    selected_clique_list.append(clique)
        else:
            print("Unexpected model status from calculate_UB_odd")
            sys.exit()

    elif UB_mode == "GRE":
        U = set(G.nodes())
        seen_vertices = set()
        remaining_clique_list = copy.deepcopy(cliques)
        while U:
            # Step 4: Pick a maximal clique Q that maximizes |NH[Q] ∩ U|
            best_clique = None
            max_intersection_size = -1

            # Find all maximal cliques in the graph
            for clique in remaining_clique_list:
                # Convert the clique to a set for easier operations
                clique_set = set(clique)

                # Find NH[Q] (the closed neighborhood of Q)
                closed_neighborhood = set(clique_set).union(nx.node_boundary(H, clique_set))

                # Compute the intersection with U
                intersection_size = len(closed_neighborhood.intersection(U))

                # Keep track of the clique with the maximum intersection
                if intersection_size > max_intersection_size:
                    best_clique_list = clique
                    best_clique = clique_set
                    best_clique_filtered = clique_set - seen_vertices
                    max_intersection_size = intersection_size

            # Step 5: Add the selected maximal clique to cliques_list
            if best_clique is not None:
                selected_clique_list.append(best_clique_filtered)
            remaining_clique_list.remove(best_clique_list)

            # Step 6: Update U by removing all vertices in NH[Q] from U
            closed_neighborhood_best_clique = set(best_clique).union(nx.node_boundary(H, best_clique))
            U.difference_update(closed_neighborhood_best_clique)

    else:
        print("Invalid UB_mode")
        sys.exit()

    # Starts the phase II BFS-like assignment procedure which converts clusters into valid partitions
    # Copy the graph and perform the BFS on the new copied graph
    G_new = copy.deepcopy(G)
    G_new.add_node('r')
    V_Q = []
    for idx, clique in enumerate(selected_clique_list):
        # Create a new vertex v_Q for each clique
        v_Q = f'v_{idx}'
        V_Q.append(v_Q)
        G_new.add_node(v_Q)
        G_new.add_edge(v_Q, 'r')
        # Connect v_{Q} to all vertices in its corresponding clique
        for vertex in clique:
            G_new.add_edge(v_Q, vertex)
    bfs_tree = nx.bfs_tree(G_new, source='r')
    # Create the partitions from the BFS tree
    T_minus_r = bfs_tree.copy()
    T_minus_r.remove_node('r')
    T_minus_r_undirected = T_minus_r.to_undirected()
    partitions = list(nx.connected_components(T_minus_r_undirected))
    partitions = [list(partition) for partition in partitions]
    partitions =[[v for v in partition if v not in V_Q] for partition in partitions]

    # Check the solution
    valid_solution = check_solution(G, s, partitions, problem)
    if valid_solution:
        return partitions
    else:
        print("The obtained solution from calculate_UB_odd is not feasible")
        sys.exit()
