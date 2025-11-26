# masterarbeit-schiffel
Files für die Masterarbeit von Tom Schiffel

## Beschreibung

Dieses Projekt umfasst die Entwicklung eines interaktiven Dashboards zur **Visualisierung von Klimadaten** einer Klimastation.
Das Skript verarbeitet, aggregiert und visualisiert verschiedene Klimavariablen (z. B. Temperatur, Niederschlag, relative Luftfeuchte, solare Einstrahlung) und stellt sie in unterschiedlichen Diagrammtypen dar.
Ziel ist die Erstellung einer verständlichen, zielgruppenorientierten und nutzerfreundlichen Oberfläche zur Exploration von Klimadaten.

## Klimastation

Standort: Kliniken Tal (Innenstadt), Rümelinstraße 23, 72070 Tübingen

## Struktur des Skripts

**Datenimport**:
**HTML-Blöcke**
**Methoden**

## wichitge Methoden

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

## Zugriff 

Ein öffentlicher Zugriff auf das Dashboard erfolgt durch die folgende URL

URL: https://climate-station-tue-ruem-492515949966.europe-west1.run.app/ 

## Projektstruktur
├── app_BigData.py                # Dash-App
├── README.md                     # Diese Projektbeschreibung

Für die Bereitstellung des Codes wird der Rohdatensatz (.csv) nicht in das Projekt integriert. 


