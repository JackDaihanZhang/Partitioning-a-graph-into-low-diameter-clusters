import networkx as nx
import os

# Read files of type .graph
def read_graph(fname):
    with open(fname, "r") as f:

        # Take number of nodes
        line = f.readline().strip().split()
        n = int(line[0])
        
        # Create an empty graph
        G = nx.empty_graph(n)
        edges = []
        vertex = 0
        
        # Iterate through each line
        for _ in range(n):
            line = f.readline().strip().split()
            
            # Populate the edge set
            for neighbor in line:
                if vertex < int(neighbor)-1 and (vertex, int(neighbor)-1) not in edges:
                    edges.append((vertex, int(neighbor)-1))
            vertex += 1
        G.add_edges_from(edges)
    
    return G

# Read files of type .txt
def read_txt(fname):
    with open(fname, "r") as f:
        line = f.readline().strip().split()
        m = int(line[1])
        
        # Create an empty graph
        G = nx.Graph()
        edges = []
        
        # Iterate through each line
        for _ in range(m):
            line = f.readline().strip().split()
            
            # Populate the edge set
            edges.append((int(line[0]), int(line[1])))
        G.add_edges_from(edges)
        G = nx.convert_node_labels_to_integers(G)
    
    return G

# Select the correct function to read the file
def read_files(ext, instance):
    # List all the files
    for file in os.listdir(ext):
        [fname, type] = os.path.splitext(file)
        
        # For the selected instance
        if (fname == instance):
            if (type == ".graph"):
                G = read_graph(ext + instance + type)
            elif (type == ".txt"):
                G = read_txt(ext + instance + type)
            elif (type == ".gml"):
                G = nx.read_gml(ext + instance + type, label="id")
                G = nx.Graph(G)            
            
            return G