import networkx as nx


# Checks whether a returned solution is a valid s-club partition given G and s
def check_solution(G, s, clusters, problem):
    valid_solution = True
    if problem == "Partitioning":
        is_partition = nx.algorithms.community.is_partition(G, clusters)
        print("Does the solution form a partition?", is_partition)
        partition_or_cover = is_partition
    else:
        union_clusters = set(vertex for cluster in clusters for vertex in cluster)
        vertex_set = set(G.nodes)
        is_cover = union_clusters == vertex_set
        print("Does the solution form a cover?", is_cover)
        partition_or_cover = is_cover
    if not partition_or_cover:
        valid_solution = False
    else:
        for cluster in clusters:
            subgraph = G.subgraph(cluster)
            is_connected = nx.is_connected(subgraph)
            valid_diameter = (nx.diameter(subgraph) <= s)
            print("Is the current s-club connected? ", is_connected)
            print("Does the current s-club have a valid diameter? ", valid_diameter)
            print("The diameter of the subgraph: ", nx.diameter(subgraph))
            if not is_connected or not valid_diameter:
                valid_solution = False
    return valid_solution
