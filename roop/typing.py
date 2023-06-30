from typing import Any, List, Iterable

from insightface.app.common import Face
import numpy
from insightface.model_zoo.inswapper import INSwapper

FaceSwapperType = INSwapper
Face = Face
Frame = numpy.ndarray[Any, Any]
NumeratedFrame = tuple[int, Frame]  # the result of frame extracting -> number of the frame and the frame itself
NumeratedFramePath = tuple[int, str]  # the enumerated path to a frame -> number of the frame and a path to the frame
FrameDataType = NumeratedFramePath | int  # type, passed to the process_frames() method, it can be a enumerated path or just number of a frame
FramesDataType = List[NumeratedFramePath] | Iterable[int]  # frames list can be a filled list of enumerated path or just iteration over frames numbers
