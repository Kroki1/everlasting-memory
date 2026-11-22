import streamlit as st
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
import yaml

# Konfiguracja strony
st.set_page_config(page_title="Ku pamięci", layout="centered")

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
col1, col2 = st.columns([1, 2])

with col1:
    zdjecie_path = ustawienia.get("zdjecie_path", "zdjecie.png")
    try:
        st.image(zdjecie_path, use_container_width=True)
    except FileNotFoundError:
        st.info("Zdjęcie taty (dodaj plik ze zdjęciem do folderu projektu).")

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
    df['DataCzas'] = pd.to_datetime(df['Data'] + ' ' + df['Godzina'], format='%d.%m.%Y %H:%M')

    # Filtrowanie przyszłych mszy
    obecny_czas = datetime.now()
    df_przyszle = df[df['DataCzas'] >= obecny_czas].copy()

    if df_przyszle.empty:
        st.write("Wszystkie zaplanowane msze już się odbyły.")
    else:
        df_przyszle = df_przyszle.sort_values(by='DataCzas').reset_index(drop=True)

        st.subheader("Zbliżające się msze")

        # --- MAPA ---
        srodek_lat = df_przyszle['Lat'].mean()
        srodek_lon = df_przyszle['Lon'].mean()
        mapa = folium.Map(location=[srodek_lat, srodek_lon], zoom_start=10)

        najblizsza_id = df_przyszle.index[0]
        lokalizacje = df_przyszle.groupby(['Lat', 'Lon', 'Adres', 'Gdzie'])

        for (lat, lon, adres, gdzie), wiersze in lokalizacje:
            czy_najblizsza = najblizsza_id in wiersze.index
            kolor = "red" if czy_najblizsza else "blue"
            ikona = "star" if czy_najblizsza else "info-sign"

            popup_html = f"<div style='font-family: sans-serif;'><b>{gdzie}</b><br><small>{adres}</small><br><br><b>Msze:</b><br>"
            for idx, row in wiersze.iterrows():
                oznaczenie = "⭐ <b>(Najbliższa)</b> " if idx == najblizsza_id else ""
                popup_html += f"- {oznaczenie}{row['Data']} godz. {row['Godzina']}<br>"
            popup_html += "</div>"

            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=350),
                tooltip="Kliknij, by zobaczyć szczegóły",
                icon=folium.Icon(color=kolor, icon=ikona)
            ).add_to(mapa)

        st_folium(mapa, width=700, height=400, returned_objects=[])

        # --- TABELA ---
        st.write("Szczegóły zaplanowanych mszy:")
        tabela_do_wyswietlenia = df_przyszle[['Data', 'Godzina', 'Gdzie', 'Adres', 'Od kogo']]
        tabela_do_wyswietlenia.index = range(1, len(tabela_do_wyswietlenia) + 1)
        st.table(tabela_do_wyswietlenia)