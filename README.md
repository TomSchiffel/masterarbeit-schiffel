# Dashboard zur Visualisierung von Klimadaten  
## Masterarbeit von Tom Schiffel

### Beschreibung

Dieses Projekt umfasst die Entwicklung eines interaktiven Dashboards zur **Visualisierung von Klimadaten** einer Klimastation.
Das Skript verarbeitet, aggregiert und visualisiert verschiedene Klimavariablen (z. B. Temperatur, Niederschlag, relative Luftfeuchte, solare Einstrahlung) und stellt sie in unterschiedlichen Diagrammtypen dar.
Ziel ist die Erstellung einer verständlichen, zielgruppenorientierten und nutzerfreundlichen Oberfläche zur Exploration von Klimadaten.

### Klimastation

Standort: Kliniken Tal (Innenstadt), Rümelinstraße 23, 72070 Tübingen

### Struktur des Skripts

**Datenimport**   
**HTML-Blöcke**  
**Methoden**

### Datenimport

Um Daten in diesem Dashboard visualisieren zu können, kann **nur** ein csv.file verwendet werden.  
An folgender Stelle kann diese eingesetzt werden:  
```python
# Datensatz einlesen
file_path=('CR300Series wlan_Table1_all_3.csv')
```

**wichtig:**  
Die Werte sollten:  
- Kommaseperatiert vorliegen
- Dezimalstellen mit einem Punkt getrennt

Konfigurationen zum .csv-file können an dieser Stelle angepasst werden:  
```python
df = pd.read_csv(
    file_path,
    skiprows=4,  # Überspringe nur die erste Zeile, wenn diese Metadaten oder ähnliches enthält
    names=["TIMESTAMP", "RECORD", "WindDir", "WS_ms_Avg", "AirTC_Avg", "RH_Avg", "BP_mbar_Avg", "Rain_mm_Avg", "HAmount_Avg", "Rain_mm_2_Tot", "SlrkW_Avg", "SlrMJ_Tot", "QR_Avg"],
    skipinitialspace=True,
    sep=',',
    decimal=".",
    engine='python',
    parse_dates=["TIMESTAMP"]
)
```
### Methoden

```python
def updateGraph(agg, Day, Month, Year)
```

```python
def updateRose(time, Day, Month, Year)
```

```python
def updateSolarMap(time, Day, Month, Year)
```
```python
def displayHumidity(time, Day, Month, Year)
```

Diese Methoden sind das Herz des Skripts. Im Prinzip sind diese sehr ähnlich aufbgebaut. Sie filtern zunächst nach übergebenem Zeitstempel und erzeugen anschließend eine entsprechende Visualisierung (Bsp.: ```python fig_RH = go.Figure()```). Wird ein Input-Wert im ```python @callback``` verändert, so wird die Ausgabe automatisch aktualisiert.

### Zugriff 

Ein öffentlicher Zugriff auf das Dashboard erfolgt durch die folgende URL

URL: https://climate-station-tue-ruem-492515949966.europe-west1.run.app/ 

### Starten (lokal)

- ```python app_BigData.py``` + **CR300Series wlan_Table1_all_3.csv** in den selben (lokalen) Ordner packen.
- Im Terminal in lokalen Ordner navigieren
- ```python python app_BigData.py``` eingeben
- Im Terminal wird *Dash is running on http://127.0.0.1:8050/* bereitgestellt. Unter diesem ist die App zu starten,

### Projektstruktur
├── app_BigData.py                  # Dash-App  
├── README.md                       # Projektbeschreibung  

Für die Bereitstellung des Codes wird der Rohdatensatz (.csv) nicht in das Projekt integriert. 

### Mögliche Probleme

- Sollte das Zoomen in den Diagrammen nicht mehr zurück gestellt werden könnnen, empfielt es sich die Seite neu zu laden

