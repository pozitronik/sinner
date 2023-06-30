from typing import Any, List, Iterable

from insightface.app.common import Face
import numpy
from insightface.model_zoo.inswapper import INSwapper

FaceSwapperType = INSwapper
Face = Face
Frame = numpy.ndarray[Any, Any]
NumeratedFrame = tuple[int, Frame]
FramesDataType = List[tuple[int, str]] | Iterable[NumeratedFrame]
FrameDataType = tuple[int, str] | NumeratedFrame
