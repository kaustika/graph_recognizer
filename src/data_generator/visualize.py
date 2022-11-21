from src.data_generator.util import Shift, CategoryId, Ratio
from collections import defaultdict
from cv2 import imread, rectangle
from typing import Union, Tuple
import matplotlib.pyplot as plt
import pygraphviz as pgv
import pathlib


# detectron2 is hard to install, at this point im hardcoding BoxMode enum values
# from detectron2.structures import BoxMode

def AGraph(directed: bool = False,
           strict: bool = True,
           name: str = '', **args) \
        -> pgv.AGraph:
    """
    Fixed AGraph constructor.

    pgv.AGraph is bugged and ignores directed=False, we fix it
    by following https://stackoverflow.com/a/20277281.
    We use this instead of pgv.AGraph.

    :return: fixed AGraph constructor, which respects directed argument.
    """

    graph = '{0} {1} {2} {{}}'.format(
        'strict' if strict else '',
        'digraph' if directed else 'graph',
        name
    )
    return pgv.AGraph(graph, **args)


def get_pos_info(graph: AGraph) -> dict[str: dict[str: float]]:
    """
    Gets node positioning info needed for bbox-building.

    :param graph: pgv.Agraph-represented graph structure;
    :return: extracted node positioning info in pixels
             in this form {
             <node_name>: {"pos_x": <x coordinate of node center in pixels>,
                           "pos_y": <x coordinate of node center in pixels>,
                           "height": <height of node's boundbox in pixels>,
                           "width": <width of node's boundbox in pixels>}
                           }
             NB: Here pixels are considered to be continuous, after a couple
                 operations they will become integer.
    """
    graph.layout(prog="sfdp")

    pos_info = {}
    for n in graph.nodes():
        x_in_points, y_in_points = n.attr['pos'].split(sep=",")
        pos_info[n] = {"pos_x": float(x_in_points) * Ratio.POINT_TO_PIXEL,
                       "pos_y": float(y_in_points) * Ratio.POINT_TO_PIXEL,
                       "height": float(n.attr['height']) * Ratio.INCH_TO_PIXEL,
                       "width": float(n.attr['width']) * Ratio.INCH_TO_PIXEL
                       }
    return pos_info


def draw_graph(filename: Union[str, pathlib.Path],
               graph_adj_list: dict[str: dict[str: dict[str: Union[str, int]]]]) \
        -> dict[str: dict[str: float]]:
    """
    Draws graph using its adjacency list representation,
    returns node positioning info needed for bbox-building.

    :param filename: desired name prefix of the png file;
    :param graph_adj_list: adjacency-list represented graph,
                           ex.: {'R2': {'D2': {'weight': '1', 'type': 0}, ...}, ...}.
                           Weight isn't used and is always '1', we keep it to satisfy
                           Problem API.
    :return: png of the graph + info about its node positioning on the image
             in this form {
             <node_name>: {"pos_x": <x coordinate of node center in pixels>,
                           "pos_y": <x coordinate of node center in pixels>,
                           "height": <height of node's boundbox in pixels>,
                           "width": <width of node's boundbox in pixels>}
                           }
            NB: Here pixels are considered to be continuous, after a couple
                operations they will become integer.
    """

    # we need to mark visited nodes so as not to draw two edges
    # while traversing the adjacency list:
    visited = dict()
    for node_one, _ in graph_adj_list.items():
        visited[node_one] = defaultdict(int)

    def edge_not_drawn(n_1: str, n_2: str):
        return visited[n_1][n_2]!=1 and visited[n_2][n_1]!=1

    def set_edge_drawn(n_1: str, n_2: str):
        visited[n_1][n_2] = 1
        visited[n_2][n_1] = 1

    dot = AGraph()
    dot.node_attr["shape"] = "circle"
    dot.node_attr["fontname"] = "Tahoma"
    dot.node_attr["fontcolor"] = "black"
    dot.node_attr["color"] = "black"

    # remember the structure: {'R2': {'D2': {'weight': '1', 'type': 0}, ...}, ...}
    for node_1, node_adj_list in graph_adj_list.items():
        for node_2, info in node_adj_list.items():
            if edge_not_drawn(node_1, node_2):
                if info["type"]==CategoryId.EDGE_TYPE_2:
                    dot.add_edge(node_1, node_2, color="black:invis:black", min_len=10)
                if info["type"]==CategoryId.EDGE_TYPE_1:
                    dot.add_edge(node_1, node_2, min_len=10)
                set_edge_drawn(node_1, node_2)

    # sfdp - layout engine
    dot.draw(filename + ".png", prog="sfdp")
    pos_info = get_pos_info(dot)

    return pos_info


def obtain_node_bboxes(filename: Union[str, pathlib.Path],
                       pos_info: dict[str: dict[str: float]],
                       visualize: bool = False) \
        -> list[dict[str: Tuple[int, int]]]:
    """
    Transform node center positions and bbox width to bbox coordinates in pixels.

    :param filename: name prefix of the png file;
    :param pos_info: info about node positioning on the image
                     in this form {
                     <node_name>: {"pos_x": <x coordinate of node center in pixels>,
                                   "pos_y": <x coordinate of node center in pixels>,
                                   "height": <height of node's boundbox in pixels>,
                                   "width": <width of node's boundbox in pixels>}
                                   };
    :param visualize: whether or not to show bboxes on the image.
    :return: node boundboxes as list of dictionaries
             in this form [{"upper_left": (x1, y1), "lower_right": (x2, y2)}].
    """
    img = imread(filename + ".png")
    img_max_y = len(img)
    img_max_x = len(img[0])

    bboxes = []
    for node, info in pos_info.items():
        pos_x = info["pos_x"]
        pos_y = info["pos_y"]
        height = info["height"]
        width = info["width"]

        x1 = int(pos_x - 0.5 * width)
        x2 = int(pos_x + 0.5 * width)
        y1 = img_max_y - int(pos_y - 0.5 * height)
        y2 = img_max_y - int(pos_y + 0.5 * height)

        # We correct bbox borders by expanding them.
        # We don't expand further than 1 pixel from img border,
        # coordinates must be inside the image.
        x1 = min(max(Shift.SHIFT_FROM_BORDER,
            int(x1) - Shift.UPPER_EXPANSION),
            img_max_x - Shift.SHIFT_FROM_BORDER)
        x2 = min(max(Shift.SHIFT_FROM_BORDER,
            int(x2) + Shift.LOWER_EXPANSION),
            img_max_x - Shift.SHIFT_FROM_BORDER)
        y1 = min(max(Shift.SHIFT_FROM_BORDER,
            int(y1) + Shift.UPPER_EXPANSION),
            img_max_y - Shift.SHIFT_FROM_BORDER)
        y2 = min(max(Shift.SHIFT_FROM_BORDER,
            int(y2) - Shift.LOWER_EXPANSION),
            img_max_y - Shift.SHIFT_FROM_BORDER)

        bboxes.append({"upper_left": (x1, y1),
                       "lower_right": (x2, y2)})
        if visualize:
            rectangle(img, (x1, y1), (x2, y2), (0, 255, 0))
    if visualize:
        plt.axis('off')
        plt.imshow(img)
    return bboxes


def obtain_edge_bboxes(filename: Union[str, pathlib.Path],
                       graph_adj_list: dict[str: dict[str: dict[str: Union[str, int]]]],
                       pos_info: dict[str: dict[str: float]],
                       visualize: bool = False) \
        -> list[dict[str: Union[Tuple[int, int]], int]]:
    """
    Obtains edge bboxes based on node center positions.
    To do this node centers are connected and the connecting
    line is treated as a diagonal of the bbox.
    For vertical and horizontal edges node centers are shifted
    (pushed apart) for the diagonal approach to be applicable.

    :param filename: name prefix of the png file;
    :param graph_adj_list: adjacency-list represented graph,
                           ex.: {'R2': {'D2': {'weight': '1', 'type': 0}, ...}, ...}.
                           Weight isn't used and is always '1', we keep it to satisfy
                           Problem API;
    :param pos_info: info about node positioning on the image
                     in this form {
                     <node_name>: {"pos_x": <x coordinate of node center in pixels>,
                                   "pos_y": <x coordinate of node center in pixels>,
                                   "height": <height of node's boundbox in pixels>,
                                   "width": <width of node's boundbox in pixels>}
                                   };
    :param visualize: whether or not to show bboxes on the image.
    :return: edge boundboxes as list of dictionaries
             in this form [{"type": <edge_type>,
                            "upper_left": (x1, y1), "lower_right": (x2, y2)}].
    """
    img = imread(filename + ".png")
    img_max_y = len(img)

    def too_close(pos1, pos2):
        return abs(pos1 - pos2) <= 10

    bboxes = []
    for node_1, node_adj_list in graph_adj_list.items():
        for node_2, info in node_adj_list.items():
            # node_1-------node_2 = edge
            pos_x1 = pos_info[node_1]["pos_x"]
            pos_x2 = pos_info[node_2]["pos_x"]

            pos_y1 = pos_info[node_1]["pos_y"]
            pos_y2 = pos_info[node_2]["pos_y"]

            if too_close(pos_x1, pos_x2):
                # this needs to be checked as rectangle
                # is defined by its upper left and lower right vertices.
                if pos_y1 < pos_y2:
                    pos_x1 -= Shift.PUSH_APART
                    pos_x2 += Shift.PUSH_APART
                else:
                    pos_x2 -= Shift.PUSH_APART
                    pos_x1 += Shift.PUSH_APART

            if too_close(pos_y1, pos_y2):
                if pos_x1 < pos_x2:
                    pos_y1 -= Shift.PUSH_APART
                    pos_y2 += Shift.PUSH_APART
                else:
                    pos_y2 -= Shift.PUSH_APART
                    pos_y1 += Shift.PUSH_APART

            x1 = int(pos_x1)
            x2 = int(pos_x2)
            y1 = img_max_y - int(pos_y1)
            y2 = img_max_y - int(pos_y2)

            edge_type = info["type"]
            bboxes.append({"type": edge_type,
                           "upper_left": (x1, y1),
                           "lower_right": (x2, y2)})
            if visualize:
                rectangle(img, (x1, y1), (x2, y2), (255, 0, 0))
    if visualize:
        plt.axis('off')
        plt.imshow(img)
    return bboxes
