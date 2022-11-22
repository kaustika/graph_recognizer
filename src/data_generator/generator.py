from src.data_generator.osm_sampler import get_nodes_in_neighbourhood, \
    create_adj_list, \
    query_from_OSM
from src.data_generator.visualize import draw_graph, \
    obtain_node_bboxes, \
    obtain_edge_bboxes
from src.data_generator.annotations import COCO_annotate_image, \
    data_to_pickle
from src.data_generator.connectivity import is_connected
from tqdm import tqdm
import time
import os

MAX_NUMBER_OF_NODES = 13
MIN_NUMBER_OF_NODES = 6


def generate_data(n: int):
    """
    Generate n images with corresponding COCO-annotations and pickled adjacency lists.

    :param n: number of samples to generate.
    :return: 3 files for each of n graphs are written to the file-system.
    """

    ways, nodes = query_from_OSM(area='Москва')

    for i in tqdm(range(n)):
        neighbours = get_nodes_in_neighbourhood(nodes)
        adj_list = create_adj_list(ways, neighbours)

        time_str = time.strftime("%Y%m%d_%H%M%S")
        working_dir = "data"
        file_prefix = "graph_" + time_str + "_"

        filepath = os.path.join(working_dir, file_prefix)

        if MAX_NUMBER_OF_NODES > len(adj_list) > MIN_NUMBER_OF_NODES:

            filepath_cur = filepath + str(i)

            if is_connected(adj_list):
                pos_info = draw_graph(filepath_cur, adj_list)

                node_bboxes = obtain_node_bboxes(filepath_cur, pos_info, True)
                edge_bboxes = obtain_edge_bboxes(filepath_cur, adj_list, pos_info)

                data_to_pickle(filepath_cur, adj_list)
                COCO_annotate_image(filepath_cur, node_bboxes, edge_bboxes)
