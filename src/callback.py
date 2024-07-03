import networkx as nx
import gurobipy as gp
from gurobipy import GRB


# This function is an implementation of Algorithm 1 from "Thinning out Steiner trees:
# a node-based model for uniform edge costs"
def find_fischetti_separator(DG, component, b):
    # Find component boundary
    neighbors_component = list(nx.node_boundary(DG, component, None))

    # Start Breadth-First Search (BFS)
    visited = [False for i in DG.nodes]
    visited[b] = True
    child = [b]

    while child:
        # Child becomes the parent
        parent = child

        # Search for new children
        child = []
        for i in parent:
            if i not in neighbors_component:
                for j in DG.neighbors(i):
                    if not visited[j]:
                        child.append(j)
                        visited[j] = True

    C = [i for i in neighbors_component if visited[i]]

    return C


# Implementation of Algorithm 1 (Section 2.3)
def labeling_callback(m, where):
    if where == GRB.Callback.MIPSOL:
        # Get the variables
        xval = m.cbGetSolution(m._X)
        yval = m.cbGetSolution(m._Y)

        # Retrieve parameters
        G = m._graph
        s = m._s
        k = m._k

        # Find the directed graph of G (DG) to use at Fischetti's Algorithm
        DG = G.to_directed()

        for j in range(k):
            # If the j is not a cluster
            if yval[j] < 0.5: continue

            # Nodes linked on club j
            V_j = [vertex for vertex in G.nodes() if xval[vertex, j] > 0.5]
            if not V_j: continue  # If it's empty

            # Induced subgraph DG[V_j]
            subgraph_j = DG.subgraph(V_j)

            # Check if the number of components of subgraph_j is more than one
            if not nx.is_strongly_connected(subgraph_j):
                # Select the smallest connected component
                smallest = min(nx.strongly_connected_components(subgraph_j), key=len)

                # Take a node as b
                b = list(smallest)[0]

                # For each connected component
                for component in nx.strongly_connected_components(subgraph_j):
                    # If the component doesn't contain b
                    if b in component: continue

                    # Take a node as a
                    a = list(component)[0]

                    # Get minimal a,b-separator
                    C = find_fischetti_separator(DG, component, b)
                    drop_from_C = []

                    # Starts making it a minimal *length-s* a,b-separator
                    for (u, v) in DG.edges():
                        DG[u][v]['separator-weight'] = 1

                    # "Remove" C from graph
                    for c in C:
                        for node in DG.neighbors(c):
                            DG[c][node]['separator-weight'] = s + 1

                    # Is C\{c} a length-s a,b-separator still? If so, remove c from C
                    for c in C:
                        # Temporarily add c back to graph (i.e., "remove" c from cut C)
                        for node in DG.neighbors(c):
                            DG[c][node]['separator-weight'] = 1

                        # What is distance from a to b in G-C?
                        distance_from_a = nx.single_source_dijkstra_path_length(DG, a, weight='separator-weight')

                        if distance_from_a[b] > s:
                            # Delete c from C. It was not needed in the cut C
                            drop_from_C.append(c)
                        else:
                            # Keep c in C. Revert arc weights back to "infinity"
                            for node in DG.neighbors(c):
                                DG[c][node]['separator-weight'] = s + 1

                    minC = [c for c in C if c not in drop_from_C]

                    # Add lazy cut constraints - (3.d)
                    m.cbLazy(m._X[a, j] + m._X[b, j] <= m._Y[j] + gp.quicksum(m._X[c, j] for c in minC))

            else:
                # Induced subgraph G[V_b]
                G_j = G.subgraph(V_j)

                # If diameter is bounded by s, everything is ok
                if nx.diameter(G_j) <= s: continue

                # We first minimalize V \ V_j. Start with S' = V \ V_j.
                S_prime = list(set(G.nodes) - set(V_j))
                for a in V_j:
                    distance_from_a = nx.single_source_dijkstra_path_length(G_j, a)
                    for vertex in distance_from_a:
                        b = vertex
                        if a < b and distance_from_a[b] > s:
                            distance_from_a_in_G = nx.single_source_dijkstra_path_length(G, a)
                            distance_from_b_in_G = nx.single_source_dijkstra_path_length(G, b)
                            remove_from_S_prime = []
                            for v in S_prime:
                                if distance_from_a_in_G[v] + distance_from_b_in_G[v] > s:
                                    remove_from_S_prime.append(v)
                            minimal_S_prime = [node for node in S_prime if node not in remove_from_S_prime]

                            # Now we define C as a length-s a,b separator and we minimalize it
                            C = minimal_S_prime
                            remove_from_C = []

                            for u, v in G.edges():
                                G[u][v]['sep-weight'] = 1

                            # "Remove" C from graph
                            for c in C:
                                for neighbor in G.neighbors(c):
                                    G[c][neighbor]['sep-weight'] = s + 1

                            # Is C\{c} a length-s a,b-separator still? If so, remove c from C
                            for c in C:
                                for neighbor in G.neighbors(c):
                                    G[c][neighbor]['sep-weight'] = 1

                                # What is distance from a to b in G-C?
                                distance_from_a = nx.single_source_dijkstra_path_length(G, a, weight='sep-weight')

                                if distance_from_a[b] > s:
                                    # Delete c from C. It was not needed in the cut C
                                    remove_from_C.append(c)
                                else:
                                    # Keep c in C. Revert arc weights back to "infinity"
                                    for neighbor in G.neighbors(c):
                                        G[c][neighbor]['sep-weight'] = s + 1

                            minC = [c for c in C if c not in remove_from_C]

                            # Add lazy cut constraints - (3.d)
                            m.cbLazy(m._X[a, j] + m._X[b, j] <= m._Y[j] + gp.quicksum(m._X[c, j] for c in minC))


# Input restrictions on labeling_callback function
def restricted_labeling_callback(m, where):
    if where == GRB.Callback.MIPSOL:
        # Get the variables
        xval = m.cbGetSolution(m._X)

        # Retrieve parameters
        G = m._graph
        s = m._s
        k = m._k

        # Find the directed graph of G (DG) to use at Fischetti's Algorithm
        DG = G.to_directed()

        for j in range(k):
            # Nodes linked on club j
            V_j = [vertex for vertex in G.nodes() if xval[vertex, j] > 0.5]
            if not V_j: continue  # If it's empty

            # Induced subgraph DG[V_j]
            subgraph_j = DG.subgraph(V_j)

            # Check if the number of components of subgraph_j is more than one
            if not nx.is_strongly_connected(subgraph_j):
                # Select the smallest connected component
                smallest = min(nx.strongly_connected_components(subgraph_j), key=len)

                # Take a node as b
                b = list(smallest)[0]

                # For each connected component
                for component in nx.strongly_connected_components(subgraph_j):
                    # If the component doesn't contain b
                    if b in component: continue

                    # Take a node as a
                    a = list(component)[0]

                    # Get minimal a,b-separator
                    C = find_fischetti_separator(DG, component, b)

                    # Make it a minimal *length-s* a,b-separator
                    for (u, v) in DG.edges():
                        DG[u][v]['separator-weight'] = 1

                    # "Remove" C from graph
                    for c in C:
                        for node in DG.neighbors(c):
                            DG[c][node]['separator-weight'] = s + 1

                            # Is C\{c} a length-s a,b-separator still? If so, remove c from C
                    drop_from_C = []
                    for c in C:
                        # Temporarily add c back to graph (i.e., "remove" c from cut C)
                        for node in DG.neighbors(c):
                            DG[c][node]['separator-weight'] = 1

                        # What is distance from a to b in G-C?
                        distance_from_a = nx.single_source_dijkstra_path_length(DG, a, weight='separator-weight')

                        if distance_from_a[b] > s:
                            # Delete c from C. It was not needed in the cut C.
                            drop_from_C.append(c)
                        else:
                            # Keep c in C. revert arc weights back to "infinity"
                            for node in DG.neighbors(c):
                                DG[c][node]['separator-weight'] = s + 1

                    minC = [c for c in C if c not in drop_from_C]

                    # Add lazy cut constraints - (3.d)
                    m.cbLazy(m._X[a, j] + m._X[b, j] <= 1 + gp.quicksum(m._X[c, j] for c in minC))

            else:
                # Induced subgraph G[V_b]
                G_j = G.subgraph(V_j)

                # If diameter is bounded by s, everything is ok
                if nx.diameter(G_j) <= s: continue

                # We first minimalize V \ V_j. Start with S' = V \ V_j.
                S_prime = list(set(G.nodes) - set(V_j))
                for a in V_j:
                    distance_from_a = nx.single_source_dijkstra_path_length(G_j, a)
                    for vertex in distance_from_a:
                        b = vertex
                        if a < b and distance_from_a[b] > s:
                            distance_from_a_in_G = nx.single_source_dijkstra_path_length(G, a)
                            distance_from_b_in_G = nx.single_source_dijkstra_path_length(G, b)
                            remove_from_S_prime = []
                            for v in S_prime:
                                if distance_from_a_in_G[v] + distance_from_b_in_G[v] > s:
                                    remove_from_S_prime.append(v)
                            minimal_S_prime = [node for node in S_prime if node not in remove_from_S_prime]

                            # Now we define C as a length-s a,b separator and we minimalize it
                            C = minimal_S_prime
                            remove_from_C = []

                            for u, v in G.edges():
                                G[u][v]['sep-weight'] = 1

                            # "Remove" C from graph
                            for c in C:
                                for neighbor in G.neighbors(c):
                                    G[c][neighbor]['sep-weight'] = s + 1

                            # Is C\{c} a length-s a,b-separator still? If so, remove c from C
                            for c in C:
                                for neighbor in G.neighbors(c):
                                    G[c][neighbor]['sep-weight'] = 1

                                # What is distance from a to b in G-C?
                                distance_from_a = nx.single_source_dijkstra_path_length(G, a, weight='sep-weight')

                                if distance_from_a[b] > s:
                                    # Delete c from C. It was not needed in the cut C
                                    remove_from_C.append(c)
                                else:
                                    # Keep c in C. Revert arc weights back to "infinity"
                                    for neighbor in G.neighbors(c):
                                        G[c][neighbor]['sep-weight'] = s + 1

                            minC = [c for c in C if c not in remove_from_C]

                            # Add lazy cut constraints - (3.d)
                            m.cbLazy(m._X[a, j] + m._X[b, j] <= 1 + gp.quicksum(m._X[c, j] for c in minC))


# Implementation of Algorithm 1 (Section 2.3)
def centering_callback(m, where):
    if where == GRB.Callback.MIPSOL:
        # Get the variables
        xval = m.cbGetSolution(m._X)

        # Retrieve parameters
        G = m._graph
        s = m._s

        # Find the directed graph of G (DG) to use at Fischetti's Algorithm
        DG = G.to_directed()

        for b in G.nodes:
            # If the b is not a center
            if xval[b, b] < 0.5: continue

            # Nodes linked to center b
            V_b = [vertex for vertex in G.nodes if xval[vertex, b] > 0.5]
            if not V_b: continue  # If it's empty

            # Induced subgraph DG[V_b]
            subgraph_b = DG.subgraph(V_b)

            # Check if the number of components of subgraph_b is more than one
            if not nx.is_strongly_connected(subgraph_b):
                # For each connected component
                for component in nx.strongly_connected_components(subgraph_b):
                    # If the component doesn't contain b
                    if b in component: continue

                    # Take a node as a
                    a = list(component)[0]

                    # Get minimal a,b-separator
                    C = find_fischetti_separator(DG, component, b)
                    drop_from_C = []

                    # Starts making it a minimal *length-s* a,b-separator
                    for (u, v) in DG.edges():
                        DG[u][v]['separator-weight'] = 1

                    # "Remove" C from graph
                    for c in C:
                        for node in DG.neighbors(c):
                            DG[c][node]['separator-weight'] = s + 1

                    # Is C\{c} a length-s a,b-separator still? If so, remove c from C
                    for c in C:
                        # Temporarily add c back to graph (i.e., "remove" c from cut C)
                        for node in DG.neighbors(c):
                            DG[c][node]['separator-weight'] = 1

                        # What is distance from a to b in G-C?
                        distance_from_a = nx.single_source_dijkstra_path_length(DG, a, weight='separator-weight')

                        if distance_from_a[b] > s:
                            # Delete c from C. It was not needed in the cut C
                            drop_from_C.append(c)
                        else:
                            # Keep c in C. Revert arc weights back to "infinity"
                            for node in DG.neighbors(c):
                                DG[c][node]['separator-weight'] = s + 1

                    minC = [c for c in C if c not in drop_from_C]

                    # Add lazy cut constraints - (5.c)
                    m.cbLazy(m._X[a, b] <= gp.quicksum(m._X[c, b] for c in minC))

            else:
                # Induced subgraph G[V_b]
                G_b = G.subgraph(V_b)

                # If diameter is bounded by s, everything is ok
                if nx.diameter(G_b) <= s: continue

                # We first minimalize V \ V_b. Start with S' = V \ V_b.
                S_prime = [i for i in G.nodes if i not in V_b]
                for u in V_b:
                    distance_from_u = nx.single_source_dijkstra_path_length(G_b, u)
                    for v in distance_from_u:
                        if u < v and distance_from_u[v] > s:
                            distance_from_u_in_G = nx.single_source_dijkstra_path_length(G, u)
                            distance_from_v_in_G = nx.single_source_dijkstra_path_length(G, v)
                            remove_from_S_prime = []
                            for vertex in S_prime:
                                if distance_from_u_in_G[vertex] + distance_from_v_in_G[vertex] > s:
                                    remove_from_S_prime.append(vertex)
                            minimal_S_prime = [node for node in S_prime if node not in remove_from_S_prime]

                            # Now we define C as a length-s a,b separator and we minimalize it
                            C = minimal_S_prime
                            remove_from_C = []

                            # Starts making it a minimal
                            for p, q in G.edges():
                                G[p][q]['sep-weight'] = 1

                            # "Remove" C from graph
                            for c in C:
                                for neighbor in G.neighbors(c):
                                    G[c][neighbor]['sep-weight'] = s + 1

                            # Is C\{c} a length-s a,b-separator still? If so, remove c from C
                            for c in C:
                                # Temporarily add c back to graph (i.e., "remove" c from cut C)
                                for neighbor in G.neighbors(c):
                                    G[c][neighbor]['sep-weight'] = 1

                                # What is distance from u to v in G-C?
                                distance_from_u = nx.single_source_dijkstra_path_length(G, u, weight='sep-weight')

                                if distance_from_u[v] > s:
                                    # Delete c from C. It was not needed in the cut C
                                    remove_from_C.append(c)
                                else:
                                    # Keep c in C. Revert arc weights back to "infinity"
                                    for neighbor in G.neighbors(c):
                                        G[c][neighbor]['sep-weight'] = s + 1

                            minC = [c for c in C if c not in remove_from_C]

                            # Add lazy cut constraints - (5.c)
                            m.cbLazy(m._X[u, b] + m._X[v, b] <= m._X[b, b] + gp.quicksum(m._X[c, b] for c in minC))


# Implementation of Benders Approach
def benders_callback(m, where):
    if where == GRB.Callback.MIPSOL:
        # Retrieve partial solutions
        xval = m.cbGetSolution(m._X)

        # Retrieve parameters
        T_star = m._T_star
        s = m._s
        G = m._graph

        # Find the directed graph of G (DG) to use at Fischetti's Algorithm
        DG = G.to_directed()

        for j in T_star:
            # Nodes assigned to j
            V_j = [vertex for vertex in G.nodes() if xval[vertex, j] > 0.5]

            # If not empty
            if not V_j: continue

            # Take the subgrapgh
            subgraph_j = DG.subgraph(V_j)

            # Check if the number of components of subgraph_j is more than one
            if not nx.is_strongly_connected(subgraph_j):
                # Choose a vertex at the smallest component
                smallest = min(nx.strongly_connected_components(subgraph_j), key=len)
                b = list(smallest)[0]

                # For each component
                for component in nx.strongly_connected_components(subgraph_j):
                    if b in component: continue

                    # Take a node at the component
                    a = list(component)[0]

                    # Get minimal a,b-separator
                    C = find_fischetti_separator(DG, component, b)

                    # Make it a minimal *length-s* a,b-separator
                    for (u, v) in DG.edges():
                        DG[u][v]['separator-weight'] = 1

                    # "Remove" C from graph
                    for c in C:
                        for node in DG.neighbors(c):
                            DG[c][node]['separator-weight'] = s + 1

                            # Is C\{c} a length-s a,b-separator still? If so, remove c from C
                    drop_from_C = []
                    for c in C:
                        # Temporarily add c back to graph (i.e., "remove" c from cut C)
                        for node in DG.neighbors(c):
                            DG[c][node]['separator-weight'] = 1

                        # What is distance from a to b in G-C ?
                        distance_from_a = nx.single_source_dijkstra_path_length(DG, a, weight='separator-weight')

                        # If c was not needed in cut C
                        if distance_from_a[b] > s:
                            # Delete c from C
                            drop_from_C.append(c)
                        else:
                            # Keep c in C. Revert arc weights back to "infinity"
                            for node in DG.neighbors(c):
                                DG[c][node]['separator-weight'] = s + 1

                                # Add lazy cut
                    minC = [c for c in C if c not in drop_from_C]
                    m.cbLazy(m._X[a, j] + m._X[b, j] <= 1 + gp.quicksum(m._X[c, j] for c in minC))

            else:
                # Take G subgraph
                G_j = G.subgraph(V_j)

                # If the diameter is less than s, it is a s-club
                if nx.diameter(G_j) <= s: continue

                # We first minimalize V \ V_j. Start with S' = V \ V_j.
                S_prime = list(set(G.nodes) - set(V_j))
                for a in V_j:
                    distance_from_a = nx.single_source_dijkstra_path_length(G_j, a)
                    for vertex in distance_from_a:
                        b = vertex
                        if a < b and distance_from_a[b] > s:
                            distance_from_a_in_G = nx.single_source_dijkstra_path_length(G, a)
                            distance_from_b_in_G = nx.single_source_dijkstra_path_length(G, b)
                            remove_from_S_prime = []
                            for v in S_prime:
                                if distance_from_a_in_G[v] + distance_from_b_in_G[v] > s:
                                    remove_from_S_prime.append(v)
                            minimal_S_prime = [node for node in S_prime if node not in remove_from_S_prime]

                            # Now we define C as a length-s a,b separator and we minimalize it
                            C = minimal_S_prime
                            remove_from_C = []

                            for u, v in G.edges():
                                G[u][v]['sep-weight'] = 1

                            for c in C:
                                for neighbor in G.neighbors(c):
                                    G[c][neighbor]['sep-weight'] = s + 1

                            for c in C:
                                for neighbor in G.neighbors(c):
                                    G[c][neighbor]['sep-weight'] = 1

                                distance_from_a = nx.single_source_dijkstra_path_length(G, a, weight='sep-weight')

                                if distance_from_a[b] > s:
                                    remove_from_C.append(c)
                                else:
                                    for neighbor in G.neighbors(c):
                                        G[c][neighbor]['sep-weight'] = s + 1

                            minC = [c for c in C if c not in remove_from_C]
                            m.cbLazy(m._X[a, j] + m._X[b, j] <= 1 + gp.quicksum(m._X[c, j] for c in minC))
