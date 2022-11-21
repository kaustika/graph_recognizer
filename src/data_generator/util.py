from enum import IntEnum


class Ratio(IntEnum):
    """
    Unit ratios.

    Graphviz coordinate(points) transformation to pixels is done
    according to https://graphviz.org/faq/#FaqCoordTransformation.
    """
    INCH_TO_PIXEL = 96  # 1 inch = 96 pixels
    INCH_TO_GVIZ_POINT = 72  # 1 point = 1/72 inch
    POINT_TO_PIXEL = INCH_TO_PIXEL / INCH_TO_GVIZ_POINT


class CategoryId(IntEnum):
    """
    Category to number mapping.
    """
    NODE = 0
    # i made the numeration compatible with Julia's
    EDGE_TYPE_1 = 2  # one line
    EDGE_TYPE_2 = 1  # two lines


class Shift(IntEnum):
    """
    Values to correct bbox borders.
    """
    UPPER_EXPANSION = 3
    LOWER_EXPANSION = 9
    SHIFT_FROM_BORDER = 1
    PUSH_APART = 20
