from typing import Any, List
import cv2
import insightface
import threading

import roop.globals
import roop.processors.frame.core
from roop.face_analyser import get_one_face, get_many_faces
from roop.utilities import conditional_download, resolve_relative_path

FACE_SWAPPER = None
THREAD_LOCK = threading.Lock()
NAME = 'Face Swapper'


def pre_check() -> None:
    download_directory_path = resolve_relative_path('../models')
    conditional_download(download_directory_path, ['https://huggingface.co/deepinsight/inswapper/resolve/main/inswapper_128.onnx'])


def get_face_swapper() -> None:
    global FACE_SWAPPER

    with THREAD_LOCK:
        if FACE_SWAPPER is None:
            model_path = resolve_relative_path('../models/inswapper_128.onnx')
            FACE_SWAPPER = insightface.model_zoo.get_model(model_path, providers=roop.globals.execution_providers)
    return FACE_SWAPPER


def swap_face(source_face: Any, target_face: Any, temp_frame: Any) -> Any:
    if target_face:
        return get_face_swapper().get(temp_frame, target_face, source_face, paste_back=True)
    return temp_frame


def process_frame(source_face: Any, temp_frame: Any) -> Any:
    if roop.globals.many_faces:
        many_faces = get_many_faces(temp_frame)
        if many_faces:
            for target_face in many_faces:
                temp_frame = swap_face(source_face, target_face, temp_frame)
    else:
        target_face = get_one_face(temp_frame)
        if target_face:
            temp_frame = swap_face(source_face, target_face, temp_frame)
    return temp_frame


def process_frames(source_path: str, temp_frame_paths: List[str], progress=None) -> None:
    source_face = get_one_face(cv2.imread(source_path))
    for temp_frame_path in temp_frame_paths:
        temp_frame = cv2.imread(temp_frame_path)
        result = process_frame(source_face, temp_frame)
        cv2.imwrite(temp_frame_path, result)
        if progress:
            progress.update(1)


def process_image(source_path: str, target_path: str, output_path: str) -> None:
    source_face = get_one_face(cv2.imread(source_path))
    target_frame = cv2.imread(target_path)
    result = process_frame(source_face, target_frame)
    cv2.imwrite(output_path, result)


def process_video(source_path: str, temp_frame_paths: List[str]) -> None:
    roop.processors.frame.core.process_video(source_path, temp_frame_paths, process_frames)
