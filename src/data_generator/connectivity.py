import networkx as nx


def adj_to_networkX(adj_list: dict[str: list[str]]) -> nx.Graph:
    """
    Converts our custom adjacency list (sampled from OSM) formatted graph to networkX graph.
    OSM - open street map.
    :param adj_list: adjacency-list represented graph,
                     ex.: {'R2': ['D2', ...], ...}.
    :return: graph in networkX format.
    """
    G = nx.Graph()
    for node1, adj in adj_list.items():
        for node2 in adj:
            G.add_edge(node1, node2)
    return G


def is_connected(adj_list) -> bool:
    """
    Checks if our custom adjacency list (sampled from OSM) is connected.
    OSM - open street map.
    :param adj_list: adjacency-list represented graph,
                     ex.: {'R2': ['D2', ...], ...}.
    :return: whether or not the graph is connected.
    """
    G = adj_to_networkX(adj_list)
    return nx.is_connected(G) if G else False
