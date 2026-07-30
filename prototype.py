"""Fase 0: prototipo su un singolo trailer, usando le funzioni in src/."""
from src.frames import extract_frames
from src.metrics import curve_from_frames
from src.plots import plot_curves_and_barcode

frames = extract_frames("test-trailer.mp4", per_second=1)
print(f"Estratti {len(frames)} frame")

brightness, temperature, colours = curve_from_frames(frames)

plot_curves_and_barcode(brightness, temperature, colours, save_path="fase0-result.png")
print("Fatto!")

