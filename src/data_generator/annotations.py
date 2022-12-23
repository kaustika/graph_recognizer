from src.data_generator.util import CategoryId
from typing import Union, Tuple
from cv2 import imread
import pickle
import pathlib
import time
import json
import os


def data_to_pickle(file_prefix: Union[str, pathlib.Path],
                   graph_adj_list: dict[str: dict[str: dict[str: Union[str, int]]]]) -> None:
    """
    Saves adjacency list represented graph to binary format for the Checker.

    :param file_prefix: name prefix of the respective png file;
    :param graph_adj_list: adjacency-list represented graph,
                           ex.: {'R2': {'D2': {'weight': '1', 'type': 0}, ...}, ...}.
                           Weight isn't used and is always '1', we keep it to satisfy
                           Problem API.
    :return: pickle is written to the file-system.
    """
    filename = file_prefix + "_src_dict.pickle"
    with open(filename, "wb") as handle:
        pickle.dump(graph_adj_list, handle, protocol=pickle.HIGHEST_PROTOCOL)


def COCO_annotate_image(filepath: Union[str, pathlib.Path],
                        node_bboxes: list[dict[str: Tuple[int, int]]],
                        edge_bboxes: list[dict[str: Union[Tuple[int, int]], int]]) -> None:
    """
    Joins all info for model training in COCO-formatted json.

    :param filepath: name prefix of the respective png file;
    :param node_bboxes: node boundboxes as list of dictionaries
                        in this form [{"upper_left": (x1, y1), "lower_right": (x2, y2)}]
    :param edge_bboxes: edge boundboxes as list of dictionaries
                        in this form [{"type": <edge_type>,
                                       "upper_left": (x1, y1), "lower_right": (x2, y2)}]
    :return: pickle is written to the file-system.
    """
    img = imread(os.path.abspath(filepath + ".png"))

    coco_obj = {'file_name': filepath + ".png",
                'width': len(img[0]),
                'height': len(img),
                'image_id': os.path.basename(filepath),
                'annotations': []}

    # Create annotations
    for node_bbox in node_bboxes:
        annot = {}
        x1, y1 = node_bbox["upper_left"]
        x2, y2 = node_bbox["lower_right"]
        annot['bbox'] = [x1, y1, x2, y2]
        annot['bbox_mode'] = 0  # BoxMode.XYXY_ABS
        annot['category_id'] = CategoryId.NODE
        coco_obj['annotations'].append(annot)

    for edge_bbox in edge_bboxes:
        annot = {}
        x1, y1 = edge_bbox["upper_left"]
        x2, y2 = edge_bbox["lower_right"]
        annot['bbox'] = [x1, y1, x2, y2]
        annot['bbox_mode'] = 0  # BoxMode.XYXY_ABS
        annot['category_id'] = CategoryId.EDGE_TYPE_1 if edge_bbox["type"]==1 else CategoryId.EDGE_TYPE_2
        coco_obj['annotations'].append(annot)

    with open(filepath + '.json', 'w') as fp:
        json.dump(coco_obj, fp)