import streamlit as st
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
import yaml

# Konfiguracja strony
st.set_page_config(page_title="Ku pamięci", layout="centered")

# --- STYLIZACJA (Tło dopasowane do zdjęcia #f3f2e6 + czytelność na telefonach) ---
st.markdown(
    """
    <style>
    /* Główne tło aplikacji i górnego paska */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #f3f2e6 !important;
        color: #2b2925 !important;
    }

    /* Wymuszenie ciemnego, czytelnego tekstu (również przy włączonym Dark Mode w telefonie) */
    h1, h2, h3, p, span, div, label, td, th {
        color: #2b2925 !important;
    }

    /* Delikatna linia oddzielająca w kolorze ramki ze zdjęcia */
    hr {
        border-color: #9d967f !important;
        opacity: 0.5;
    }

    /* Estetyczne obramowanie tabeli na kremowym tle */
    table {
        background-color: #faf9f2 !important;
        border-radius: 8px;
        overflow: hidden;
    }
    th {
        background-color: #ebe8d8 !important;
        font-weight: 600 !important;
    }
    td, th {
        border-color: #dcd7c3 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Wczytanie danych z pliku YAML
try:
    with open("dane.yaml", "r", encoding="utf-8") as file:
        dane = yaml.safe_load(file)
except FileNotFoundError:
    st.error("Brak pliku dane.yaml. Utwórz go, aby strona mogła działać.")
    st.stop()

ustawienia = dane.get("ustawienia", {})
lista_mszy = dane.get("msze", [])

# --- NAGŁÓWEK STRONY ---
col1, col2 = st.columns([1, 2], vertical_alignment="center")

with col1:
    zdjecie_path = ustawienia.get("zdjecie_path", "zdjecie.png")
    try:
        st.image(zdjecie_path, use_container_width=True)
    except FileNotFoundError:
        st.info(f"Dodaj plik '{zdjecie_path}' do folderu projektu.")

with col2:
    st.title(ustawienia.get("imie_nazwisko", "Imię i Nazwisko"))
    st.subheader(ustawienia.get("data_ur_sm", "Daty"))
    st.write(ustawienia.get("wstep_tekst", "Tekst wspominkowy"))

st.divider()

# --- PRZETWARZANIE DANYCH O MSZACH ---
if not lista_mszy:
    st.write("Brak wprowadzonych intencji mszalnych.")
else:
    df = pd.DataFrame(lista_mszy)

    # Utworzenie pełnej daty do porównania z dniem dzisiejszym
    df["DataCzas"] = pd.to_datetime(
        df["Data"] + " " + df["Godzina"], format="%d.%m.%Y %H:%M"
    )

    # Filtrowanie przyszłych mszy
    obecny_czas = datetime.now()
    df_przyszle = df[df["DataCzas"] >= obecny_czas].copy()

    if df_przyszle.empty:
        st.write("Wszystkie zaplanowane msze już się odbyły.")
    else:
        df_przyszle = df_przyszle.sort_values(by="DataCzas").reset_index(drop=True)

        st.subheader("Zbliżające się msze")
        st.caption(
            "Dotknij pinezki na mapie, aby zobaczyć godziny mszy i otworzyć dojazd w Google Maps."
        )

        # --- MAPA ---
        srodek_lat = df_przyszle["Lat"].mean()
        srodek_lon = df_przyszle["Lon"].mean()
        mapa = folium.Map(location=[srodek_lat, srodek_lon], zoom_start=10)

        najblizsza_id = df_przyszle.index[0]
        lokalizacje = df_przyszle.groupby(["Lat", "Lon", "Adres", "Gdzie"])

        for (lat, lon, adres, gdzie), wiersze in lokalizacje:
            czy_najblizsza = najblizsza_id in wiersze.index
            kolor = "red" if czy_najblizsza else "blue"
            ikona = "star" if czy_najblizsza else "info-sign"

            # Link otwierający nawigację bezpośrednio w Google Maps na telefonie
            google_maps_url = (
                f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"
            )

            popup_html = f"""
            <div style='font-family: sans-serif; color: #2b2925; min-width: 200px;'>
                <b style='font-size: 14px;'>{gdzie}</b><br>
                <small style='color: #555;'>{adres}</small><br><br>
                <b>Zaplanowane msze:</b><br>
            """
            for idx, row in wiersze.iterrows():
                oznaczenie = "⭐ <b>(Najbliższa)</b> " if idx == najblizsza_id else ""
                popup_html += f"• {oznaczenie}{row['Data']} godz. {row['Godzina']}<br>"

            popup_html += f"""
                <div style='margin-top: 12px; text-align: center;'>
                    <a href='{google_maps_url}' target='_blank' rel='noopener noreferrer'
                       style='display: inline-block; padding: 8px 12px; background-color: #8a7d60; 
                              color: #ffffff; text-decoration: none; border-radius: 6px; 
                              font-weight: bold; font-size: 13px;'>
                       🧭 Wyznacz trasę w Google Maps
                    </a>
                </div>
            </div>
            """

            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=320),
                tooltip="Dotknij, aby zobaczyć szczegóły i dojazd",
                icon=folium.Icon(color=kolor, icon=ikona),
            ).add_to(mapa)

        st_folium(mapa, use_container_width=True, height=400, returned_objects=[])

        # --- TABELA ---
        st.write("Szczegóły zaplanowanych mszy:")
        tabela_do_wyswietlenia = df_przyszle[
            ["Data", "Godzina", "Gdzie", "Adres", "Od kogo"]
        ]
        tabela_do_wyswietlenia.index = range(1, len(tabela_do_wyswietlenia) + 1)
        st.table(tabela_do_wyswietlenia)
