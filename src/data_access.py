"""Punto unico di accesso al warehouse. Tutto il progetto legge da qui."""
import sqlite3
import pandas as pd


def load_warehouse():
    """Legge la tabella films dal database SQLite e la restituisce come DataFrame."""
    conn = sqlite3.connect("../data/warehouse/color_in_motion.db")
    df = pd.read_sql_query("SELECT * FROM films", conn)
    conn.close()
    return df