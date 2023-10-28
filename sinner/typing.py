from typing import Any, List, Tuple

import numpy
from insightface.model_zoo.inswapper import INSwapper

FaceSwapperType = INSwapper
Frame = numpy.ndarray[Any, Any]
NumeratedFramePath = tuple[int, str]  # the enumerated path to a frame -> number of the frame and a path to the frame
FramesList = List[Tuple[Frame, str]]  # list of tuples [frame, frame caption]

UTF8 = "utf-8"
