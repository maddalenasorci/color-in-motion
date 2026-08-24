import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# titolo
st.title("Color in Motion")
st.write("Do film genres have a colour signature?")

# carichiamo i dati dal warehouse
df = pd.read_csv("data/warehouse/color_features.csv")
st.write("Films analysed:", len(df))

# --- Grafico 1: luminanza media per genere ---
st.header("Average brightness by genre")

# calcoliamo la media per genere, ordinata
brightness_by_genre = df.groupby("genere_principale")["brightness_media"].mean().sort_values()

fig, ax = plt.subplots()
ax.bar(brightness_by_genre.index, brightness_by_genre.values, color="steelblue")
ax.set_ylabel("Average brightness")
ax.set_xlabel("Genre")
st.pyplot(fig)

st.write("Horror is the darkest genre, comedy the lightest — as the theory predicts.")

# --- Interactive: explore films by genre ---
st.header("Explore films by genre")

# menu a tendina per scegliere il genere
generi = df["genere_principale"].unique()
genere_scelto = st.selectbox("Choose a genre:", generi)

# filtriamo i film di quel genere
film_genere = df[df["genere_principale"] == genere_scelto]

st.write("Films in this genre:", len(film_genere))
st.dataframe(film_genere[["primaryTitle", "startYear", "brightness_media", "saturation_media"]])

# --- Barcodes: the colour signature of each genre ---
st.header("Colour signatures (movie barcodes)")

st.write("Each stripe shows how colour moves through a representative trailer of each genre.")
st.image("outputs/barcode_representative.png")

st.write("And the average colour per genre:")
st.image("outputs/barcode_by_genre.png")

st.subheader("What the barcodes reveal")
st.write("""
Look at the Crime barcode: it has a strong, recurring **red** signature —
much more distinctive than the other genres. Yet the classifier fails on Crime.

Why the contradiction? Because the colour features are averages. Crime's red
appears at intervals; averaged with the surrounding dark frames, it becomes an
insignificant brown in the numbers. The eye sees the red in the barcode, but
the model — working only with means — never does.

This shows the information to identify Crime **exists** in the colour, but the
mean-based features throw it away. It's the clearest example of why richer,
time-aware features would be needed to push the classifier further.
""")

# --- Classifier result ---
st.header("Can colour predict the genre?")

st.write("A Random Forest classifier was trained on the 6 colour features.")

# mostriamo i numeri chiave in modo evidente
col1, col2 = st.columns(2)
col1.metric("Classifier accuracy", "55.9%")
col2.metric("Random guessing", "20%")

st.write("""
The classifier predicts genre from colour alone almost 3x better than chance.
But this hides a nuance: it reliably recognises only the visual extremes —
Horror (dark) and Action. The central genres (Comedy, Crime, Drama) share
similar colour signatures and are not separable by colour alone.

**Conclusion:** colour is a strong signal for extreme genres, but not enough
for fine-grained genre classification. Other signals (editing rhythm, audio,
motion) would be needed.
""")