import gurobipy as gp
from gurobipy import GRB
import networkx as nx
import sys
from check_solution import check_solution


def solve_s_club_with_sasha(G, s, potential_roots, feasible_partitions, max_k):
    # Construct the s-power graph
    H = nx.power(G, s)

    # Calculate the distance between nodes, which will be used in the constraints
    distance = {}
    for i in G.nodes:
        distance[i] = nx.single_source_dijkstra_path_length(G, i)

    try:
        m = gp.Model()

        # set the time limit
        m.Params.TimeLimit = 3600

        # Create the variables
        X = m.addVars(G.nodes, max_k, vtype=GRB.BINARY)
        U = m.addVars(G.nodes, G.nodes, s + 1, lb=0.0, ub=1.0, vtype=GRB.CONTINUOUS)
        Z = m.addVar(vtype=GRB.CONTINUOUS)

        # Set the objetive function - (2.a)
        m.setObjective(Z, GRB.MINIMIZE)

        # Add the assignment constraints - (2.b and 2.c)
        m.addConstrs(gp.quicksum(X[i, k] for k in range(max_k)) == 1 for i in G.nodes)
        m.addConstrs(Z >= (k + 1) * X[i, k] for i in G.nodes for k in range(max_k))

        for i in G.nodes:
            for j in G.nodes:
                if i < j:
                    # Add the s-club constraints - (2.d and 2.e)
                    m.addConstrs(
                        X[i, k] + X[j, k] <= 1 + U[i, j, s] for k in range(max_k) if distance[i][j] in range(2, s + 1))
                    m.addConstrs(X[i, k] + X[j, k] <= 1 for k in range(max_k) if distance[i][j] >= s + 1)

                    # Add the u-variables continuity constraints - (2.f)
                    m.addConstrs(U[i, j, l] <= gp.quicksum(
                        U[t, j, l - 1] for t in G.neighbors(i) if (t < j and distance[j][t] <= l - 1)) + gp.quicksum(
                        U[j, t, l - 1] for t in G.neighbors(i) if (j < t and distance[j][t] <= l - 1)) for l in
                                 range(distance[i][j], s + 1) if distance[i][j] in range(2, s + 1))

                    # Add the u-function restriction constraints - (2.g and 2.h)
                    m.addConstrs(
                        U[i, j, l] <= X[i, k] - X[j, k] + 1 for k in range(max_k) for l in range(distance[i][j], s + 1)
                        if distance[i][j] in range(1, s + 1))
                    m.addConstrs(
                        U[i, j, l] <= X[j, k] - X[i, k] + 1 for k in range(max_k) for l in range(distance[i][j], s + 1)
                        if distance[i][j] in range(1, s + 1))

                    # Fix the u variables when l is out of (d_ij_G, s)
                    for l in range(min(distance[i][j], s + 1)):
                        U[i, j, l].ub = 0

                else:
                    # Fix the u variables to zero when j <= i
                    for l in range(s + 1):
                        U[i, j, l].ub = 0

        # Fix the potential roots as independent s-clubs
        for k in range(len(potential_roots)):
            X[potential_roots[k], k].lb = 1

        # Fix the assignment of the vertices far away from the potential roots to zero (F_1)
        for k in range(len(potential_roots)):
            for vertex in G.nodes:
                if vertex not in H.neighbors(potential_roots[k]) and vertex != potential_roots[k]:
                    X[vertex, k].ub = 0

        # Warm-start MIP with clusters (obtained by running heuristic.py)
        # Start the warm-start with nodes belong to partitions containing potential root
        partition_index = len(potential_roots)
        if len(feasible_partitions) != 0:
            for partition in feasible_partitions:
                flag = False
                # If there is a potential root in the cluster, assign every other vertex to the same s-club as the
                # potential root
                for j in range(len(potential_roots)):
                    if potential_roots[j] in partition:
                        flag = True
                        for vertex in partition:
                            X[vertex, j].start = 1
                            print("Assign vertex", vertex, "to partition", j)

                # Else, assign all vertices to the same partition labeled by partition_index
                if not flag:
                    for vertex in partition:
                        X[vertex, partition_index].start = 1
                        print("Assign vertex", vertex, "to partition", partition_index)
                    partition_index += 1

        m.Params.lazyConstraints = 1
        m.optimize()

    # Handle the out-of-memory exception
    except gp.GurobiError as e:
        if e.errno == 10005:  # Error code for out-of-memory
            print("Out of memory error encountered, taking the best incumbent solution")

    # Construct the final partition if there is at least one feasible solution found
    if m.Status in [GRB.OPTIMAL, GRB.SUBOPTIMAL]:
        final_partitions = []
        for k in range(round(Z.x)):
            partition = []
            for i in G.nodes:
                if X[i, k].x >= 0.9:
                    partition.append(i)
            final_partitions.append(partition)

        # Check the solution
        valid_solution = check_solution(G, s, final_partitions)
        if valid_solution:
            return m.objVal, m.ObjBound, m.Status
        else:
            print("The solution obtained from solve_s_club_with_sasha is invalid")
            sys.exit()
    else:
        print("The Sasha model has not found a feasible solution within the time limit, returning"
              "the original lower and upper bounds")
        return max_k, len(potential_roots), m.Status
