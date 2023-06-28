from typing import Any

from insightface.app.common import Face
import numpy
from insightface.model_zoo import Landmark, Attribute, RetinaFace, ArcFaceONNX
from insightface.model_zoo.inswapper import INSwapper

FaceSwapperType = INSwapper
Face = Face
Frame = numpy.ndarray[Any, Any]
