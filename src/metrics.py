"""Metriche di colore su singoli frame, nello spazio CIELAB."""
import numpy as np
from skimage import color


def frame_metrics(frame):
    """Da un frame RGB calcola luminanza, temperatura e colore medio."""
    lab = color.rgb2lab(frame / 255.0)
    L = lab[:, :, 0].mean()          # luminanza
    b = lab[:, :, 2].mean()          # temperatura: + caldo, - freddo
    mean_colour = frame.reshape(-1, 3).mean(axis=0) / 255.0
    return {"brightness": L, "temperature": b, "mean_colour": mean_colour}


def curve_from_frames(frames):
    """Applica frame_metrics a tutti i frame e restituisce tre liste."""
    brightness, temperature, colours = [], [], []
    for f in frames:
        m = frame_metrics(f)
        brightness.append(m["brightness"])
        temperature.append(m["temperature"])
        colours.append(m["mean_colour"])
    return brightness, temperature, colours