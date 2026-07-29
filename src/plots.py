"""Grafici: curve di colore nel tempo e movie barcode."""
import numpy as np
import matplotlib.pyplot as plt


def plot_curves_and_barcode(brightness, temperature, colours, save_path=None):
    """Disegna le due curve e il barcode. Se save_path e dato, salva l'immagine."""
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 8))

    ax1.plot(brightness, color="black")
    ax1.set_title("Brightness over time (higher = lighter)")
    ax1.set_xlabel("seconds")

    ax2.plot(temperature, color="orangered")
    ax2.set_title("Colour temperature over time (higher = warmer)")
    ax2.set_xlabel("seconds")

    barcode = np.array(colours).reshape(1, len(colours), 3)
    ax3.imshow(barcode, aspect="auto")
    ax3.set_title("Movie barcode")
    ax3.set_yticks([])

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=100)
    plt.show()