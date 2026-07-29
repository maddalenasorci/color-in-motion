"""Estrazione di frame da un file video."""
import cv2


def extract_frames(video_path, per_second=1):
    """Apre un video ed estrae `per_second` frame per ogni secondo.
    Restituisce una lista di frame in formato RGB."""
    video = cv2.VideoCapture(video_path)
    fps = video.get(cv2.CAP_PROP_FPS)
    step = max(int(fps / per_second), 1)

    frames = []
    count = 0
    while True:
        ok, frame = video.read()
        if not ok:
            break
        if count % step == 0:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        count += 1
    video.release()
    return frames