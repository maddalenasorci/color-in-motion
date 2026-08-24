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

def frame_hue_family(frame):
    """Da un frame RGB dice a quale famiglia di colore appartiene.
    I frame scuri o poco saturi finiscono in 'dark_neutral'."""
    hsv = color.rgb2hsv(frame / 255.0)
    h = hsv[:, :, 0].mean()   # tinta media (0-1)
    s = hsv[:, :, 1].mean()   # saturazione media
    v = hsv[:, :, 2].mean()   # luminosita media

    # se e troppo scuro o troppo poco saturo, non ha una tinta vera
    if v < 0.2 or s < 0.15:
        return "dark_neutral"

    # altrimenti classifichiamo in base alla tinta (h va da 0 a 1)
    gradi = h * 360
    if gradi < 20 or gradi >= 340:
        return "red"
    elif gradi < 45:
        return "orange"
    elif gradi < 70:
        return "yellow"
    elif gradi < 150:
        return "green"
    elif gradi < 260:
        return "blue"
    else:
        return "purple"


def color_distribution(frames):
    """Per una lista di frame, conta la percentuale di ogni famiglia di colore."""
    famiglie = ["red", "orange", "yellow", "green", "blue", "purple", "dark_neutral"]

    # contiamo quanti frame per famiglia
    conteggi = {}
    for f in famiglie:
        conteggi[f] = 0

    for frame in frames:
        famiglia = frame_hue_family(frame)
        conteggi[famiglia] = conteggi[famiglia] + 1

    # trasformiamo i conteggi in percentuali
    totale = len(frames)
    percentuali = {}
    for f in famiglie:
        percentuali[f] = conteggi[f] / totale

    return percentuali