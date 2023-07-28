from typing import Any

from insightface.app.common import Face
import numpy
from insightface.model_zoo.inswapper import INSwapper

FaceSwapperType = INSwapper
Face = Face
Frame = numpy.ndarray[Any, Any]
NumeratedFrame = tuple[int, Frame]  # type: ignore[valid-type] #todo: check this # the result of frame extracting -> number of the frame and the frame itself
NumeratedFramePath = tuple[int, str]  # the enumerated path to a frame -> number of the frame and a path to the frame
