import networkx as nx


# Checks whether a returned solution is a valid s-club partition given G and s
def check_solution(G, s, partitions):
    valid_solution = True
    is_partition = nx.algorithms.community.is_partition(G, partitions)
    print("Does the solution form a partition?", is_partition)
    if not is_partition:
        valid_solution = False
    else:
        for cluster in partitions:
            subgraph = G.subgraph(cluster)
            is_connected = nx.is_connected(subgraph)
            valid_diameter = (nx.diameter(subgraph) <= s)
            print("Is the current s-club connected? ", is_connected)
            print("Does the current s-club have a valid diameter? ", valid_diameter)
            print("The diameter of the subgraph: ", nx.diameter(subgraph))
            if not is_connected or not valid_diameter:
                valid_solution = False
    return valid_solution
