"""Metriche di colore su singoli frame, nello spazio CIELAB."""
import numpy as np
from skimage import color


def frame_metrics(frame):
    """Da un frame RGB calcola luminanza, temperatura, saturazione e colore medio."""
    lab = color.rgb2lab(frame / 255.0)
    L = lab[:, :, 0].mean()          # luminanza
    b = lab[:, :, 2].mean()          # temperatura: + caldo, - freddo

    # saturazione: convertiamo in HSV e prendiamo la media del canale S
    hsv = color.rgb2hsv(frame / 255.0)
    s = hsv[:, :, 1].mean()          # saturazione: 0 = smorto, 1 = vivido

    mean_colour = frame.reshape(-1, 3).mean(axis=0) / 255.0
    return {"brightness": L, "temperature": b, "saturation": s, "mean_colour": mean_colour}


def curve_from_frames(frames):
    """Applica frame_metrics a tutti i frame e restituisce quattro liste."""
    brightness, temperature, saturation, colours = [], [], [], []
    for f in frames:
        m = frame_metrics(f)
        brightness.append(m["brightness"])
        temperature.append(m["temperature"])
        saturation.append(m["saturation"])
        colours.append(m["mean_colour"])
    return brightness, temperature, saturation, colours