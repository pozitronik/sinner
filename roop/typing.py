from typing import Any, List, Iterable

from insightface.app.common import Face
import numpy
from insightface.model_zoo.inswapper import INSwapper

FaceSwapperType = INSwapper
Face = Face
Frame = numpy.ndarray[Any, Any]
FramesDataType = List[tuple[int, str]] | Iterable[tuple[int, Frame]]
FrameDataType = tuple[int, str] | tuple[int, Frame]
