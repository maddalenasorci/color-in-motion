# Color in Motion

Analisi della grammatica cromatica dei trailer cinematografici:
come il colore si muove nel tempo e come cambia per genere.

Progetto per il Master in Business Intelligence & Big Data Analytics.

## Domanda di ricerca
Un horror e una commedia hanno curve cromatiche di forma diversa?
E questa differenza e abbastanza netta da riconoscere il genere
dal solo andamento del colore?

## Pipeline
1. Campionamento film per genere (IMDb + TMDB)
2. Download trailer (yt-dlp) ed estrazione frame (OpenCV)
3. Estrazione metriche colore nel tempo (spazio CIELAB)
4. Storage: source tables, staging area, data warehouse
5. Analisi e classificatore di genere
6. Dashboard di visualizzazione

## Tecnologie
Python, yt-dlp, OpenCV, scikit-image, scikit-learn, MongoDB, SQL, Power BI