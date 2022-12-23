from itertools import product
from collections import defaultdict
from random import randint, choice, shuffle
from typing import Tuple, Union
import overpass
import string
import json


def generate_names() -> list[str]:
    """
    We are going to choose names for nodes from this list (260 possible names all in all).

    :return: list with all possible names consisting of two capital letters each.
    """
    alphabet = [*string.ascii_uppercase]
    numbers = [str(n) for n in range(10)]
    symbols = [alphabet, numbers]
    names = [''.join(p) for p in product(*symbols)]
    shuffle(names)
    return names


def query_from_OSM(area='Санкт-Петербург') -> Tuple[list, dict[int:list]]:
    """
    Queries data about paths on SPb city-map from OSM.

    :return: ways and nodes connected by them.
    """
    api = overpass.API()

    # OSM query language is very wierd, it is what it is:
    rail_response = api.get(
        f'area[name="{area}"];'
        f'way(area)[highway=path];'
        f'(._;>;);',
        responseformat="json")
    # We might want to read from that in the future
    with open('response.json', 'w') as rf:
        json.dump(rail_response, rf)

    elements = rail_response['elements']
    # way = sequence of connected nodes
    ways = [el for el in elements if 'type' in el and el['type']=='way']
    nodes = {el['id']: el for el in elements if 'type' in el and el['type']=='node'}

    return ways, nodes


def get_node_name(node_id: int, node_name_dict: dict[int: str], names: list[str]) \
        -> Tuple[dict[int: str], str]:
    """
    If there was such a node in the dictionary - return its name,
    if not - take a new name by node number
    (we just count how many names there are already and take the next one from the pre-generated list).

    :param node_id: unique node id;
    :param node_name_dict: dictionary with previously assigned node names;
    :param names: list with all possible names.
    :return: node name (assigned earlier or new) + updated node_name_dict.
    """
    if node_id in node_name_dict.keys():
        return node_name_dict, node_name_dict[node_id]

    node_num = len(node_name_dict)

    # we ran out of names
    if node_num > len(names) - 1:
        return {}, ''

    new_name = names[node_num]
    node_name_dict[node_id] = new_name

    return node_name_dict, new_name


def get_nodes_in_neighbourhood(nodes) -> list:
    """
    Given all the nodes, we randomly choose one and take all
    nodes in its square neighbourhood, assuming that in our region
    lat and lon are proportional to x, y..

    :param nodes: all the nodes,
    :return: randomly chosen node and his neighbours.
    """
    node_num = choice([*nodes.keys()])

    neighbourhood_size = 0.001

    base_node = nodes[node_num]
    base_lat = base_node['lat']
    base_lon = base_node['lon']

    nodes_in_neighbourhood = [identifier for identifier, data in nodes.items() if
                              abs(data['lat'] - base_lat) < neighbourhood_size
                              and
                              abs(data['lon'] - base_lon) < neighbourhood_size]

    return nodes_in_neighbourhood


def create_adj_list(ways, neighbours) -> dict[str: dict[str: dict[str: Union[str, int]]]]:
    """
    Convert OSM-data to our custom formatted adjacency list represented graph.

    :param ways: ways queried from osm;
    :param neighbours: random nodes that are nearby.
    :return: adjacency-list represented graph,
             ex.: {'R2': {'D2': {'weight': '1', 'type': 0}, ...}, ...}.
             Weight isn't used and is always '1', we keep it to satisfy
             Problem API.
    """
    node_name_dict = dict()
    adj_list = defaultdict(dict)

    names = generate_names()

    for way in ways:

        nodes_list = way['nodes']

        for node_num in range(len(nodes_list) - 1):

            first_node_id = nodes_list[node_num]
            second_node_id = nodes_list[node_num + 1]
            if first_node_id in neighbours and second_node_id in neighbours:

                new_name_data = get_node_name(first_node_id, node_name_dict, names)
                if not new_name_data:
                    print(node_num)
                    return 'More nodes than was expected'

                node_name_dict, first_node_name = new_name_data

                new_name_data = get_node_name(nodes_list[node_num + 1], node_name_dict, names)
                if not new_name_data:
                    print(node_name_dict)
                    return 'More nodes than was expected'

                node_name_dict, second_node_name = new_name_data

                edge_type = randint(1, 2)

                adj_list[first_node_name] = {second_node_name: {"type": edge_type, "weight": "1"}}
                adj_list[second_node_name] = {first_node_name: {"type": edge_type, "weight": "1"}}

    return adj_list
