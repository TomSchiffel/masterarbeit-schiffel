# Import packages
from dash import Dash, html, dash_table, dcc
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3 
import csv
import numpy as np

print("-----------------------------")
print("Programm wird gestartet...")
print("-----------------------------")

print("Daten werden eingelesen..")

# Datensatz einlesen
file_path=('CR300Series wlan_Table1_all_3.csv')

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

df["TIMESTAMP"] = pd.to_datetime(
    df["TIMESTAMP"], format="%Y-%m-%d %H:%M:%S",
    errors="coerce"
)
print("Daten erfolgreich eingelesen")

# Spalten HA-mount_Avg, SlrMJ_Tot und Qr_Avg rauslöschen
df.drop(columns=["HAmount_Avg", "SlrMJ_Tot", "QR_Avg"], inplace=True)

numeric_col = df.columns.drop("TIMESTAMP")
df[numeric_col] = df[numeric_col].replace(",", ".", regex=True).astype(float)

# Timestamp in datetime
df["TIMESTAMP"] = pd.to_datetime(df["TIMESTAMP"], dayfirst=True)
df["WS_ms_Avg"] = pd.to_numeric(df["WS_ms_Avg"], errors="coerce")

# Index setzen
df = df.set_index("TIMESTAMP")
#print(df.head(5).to_string())

# Stündliche Aggregation
# Überall wird der Mittelwert einfach über das Atrithmetische Mittel berechnet.
# Spezialfall: WindDir: hier erst Umwandlung in Einheitsvektor, dann arith. Mittel, dann zurück wandeln
df_hourly = df.resample("h").agg({
    "RECORD": "count",                
    "WindDir": lambda x: np.degrees(np.arctan2(
        np.mean(np.sin(np.radians(x))),
        np.mean(np.cos(np.radians(x)))
    )),  
    "WS_ms_Avg": "mean",
    "AirTC_Avg": "mean",
    "RH_Avg": "mean",
    "BP_mbar_Avg": "mean",
    "Rain_mm_Avg": "sum",
    "Rain_mm_2_Tot": "sum",
    "SlrkW_Avg": "mean"
}).reset_index()

# Windrichtung wieder auf 0-360° anpassen
df_hourly["WindDir"] = (df_hourly["WindDir"] + 360) % 360

# Rudnen auf zwei Nachkommastellen
df_hourly = df_hourly.round(2)
print("Attributstabelle: ")
print("")
print(df.tail(10).to_string())

# Diagramme

# Solare Einstrahlung

fig_solar = px.imshow(
    [[0]],
    labels=dict(x='Monat', y='Stunde', color='Solare Einstrahlung (W/m2)'),
    aspect='auto'
)

# Klimastation

latest_entry = df.loc[df.index.max()]

# Koordinten der Klimastation festlegen
lat = 48.523669
lon = 9.054517

# Karte mit Marker und Tooltip
map = px.scatter_mapbox(
    pd.DataFrame({
        "lat": [lat],
        "lon": [lon],
    }),
    lat="lat",
    lon="lon",
    zoom=11,
) 

map.update_traces(
    marker=dict(
        size=13,
        color="rgba(245,166,35, 0.9)"
    )
)
map.update_layout(
    mapbox_style= "open-street-map",
    mapbox= dict(
        center = {"lat": lat, "lon": lon},
        zoom=11
    ),
    margin={"r":0, "l": 0, "t": 0, "b": 0},
)

# Boxdesign für Map
mapbox_style = dict(
    showarrow= False,
    bgcolor= "rgba(255,255,255, 0.7)",
    borderpad=6,
    bordercolor="rgba(245,166,35, 0.7)",
    borderwidth=1,
    font=dict(color="orange", size=13, family="Arial")
)

# Lufttemperatur
map.add_annotation(
    text=f"{latest_entry['AirTC_Avg']:.0f} °C",
    xref="paper", 
    yref="paper",
    x=0.03,
    y=0.96,
    **mapbox_style
)

# relative Luftfeuchtigkeit
map.add_annotation(
    text=f"{latest_entry['RH_Avg']:.0f} %",
    xref="paper", 
    yref="paper",
    x=0.97,
    y=0.96,
    **mapbox_style
)

# Luftdruck
map.add_annotation(
    text=f"{latest_entry['BP_mbar_Avg']:.0f} mbar",
    xref="paper", 
    yref="paper",
    x=0.03,
    y=0.04,
    **mapbox_style
)

# Initialize the app
app = Dash()

#Anpassung der Spaltennamen
table_columns= [
    {"name": "Datum/Uhrzeit", "id": "TIMESTAMP"},
    {"name": "ID", "id": "RECORD"},
    {"name": "Windrichtung (Winkel)", "id": "WindDir"},
    {"name": "Windgeschwindigkeit (m/s)", "id": "WS_ms_Avg"},
    {"name": "Lufttemperatur (°C)", "id": "AirTC_Avg"},
    {"name": "Relative Luftfeuchtigkeit (%)", "id": "RH_Avg"},
    {"name": "Luftdruck (mbar)", "id": "BP_mbar_Avg"},
    {"name": "Niederschlagsmittel (mm)", "id": "Rain_mm_Avg"},
    {"name": "Niederschlagssume (mm)", "id": "Rain_mm_2_Tot"},
    {"name": "Solare Einstrahlung(W/m²)", "id": "SlrkW_Avg"},
]

# Layout für Kacheln
kachel_layout = {
        "backroundColor": "#FaF9F6",
        "border": "none",
        "borderRadius": "15px",
        "boxShadow": "4px 4px 10px rgba(0,0,0,0.1)",
        "padding": "0.75rem",
        "margin": "0.75rem",
    }

# App layout
app.layout = html.Div(
    style={
        "display": "flex",
        "flexDirection": "column",
        "height": "100vh",
        "overflow": "hidden"
    },
    children=[
        # Hauptbereich mit 3 Spalten
        html.Div(
            style={
                "flex": "1",
                "display": "flex", 
                "justifyContent": "center",
                "alignItems": "stretch",
                #"height": "98vh",
                "overflow": "hidden",
                "gap": "0.4rem",
                "padding": "1rem",
                "boxSizing": "border-box",
                "flexDirection": "row", 
                #"marginBottom": "1.875rem",
                },
            children=[

                # Linke Spalte (flex 3)
                html.Div(
                    style={"flex": "2", "display": "flex", "flexDirection": "column"},
                    children=[
                        # Datums-Auswahl Dropdown
                        html.Div(
                            id="kachel_date",
                            children=[
                                html.H2("Zeitraum", 
                                        style={
                                            "textAlign": "center",
                                            "marginBottom": "0.3rem",
                                            "fontSize": "0.9rem",
                                            "fontWeight": "600"
                                            }
                                        ),
                                dcc.Dropdown(
                                    id="Auswahl-Dropdown",
                                    options=[
                                        {"label": "Tag", "value": "D"},
                                        {"label": "Monat", "value": "M"},
                                        {"label": "Jahr", "value": "Y"},
                                    ],
                                    value="D",
                                    clearable=False,
                                    style={
                                        "marginTop": "0.3rem",
                                        "marginBottom": "0.3rem",
                                        "width": "80%", 
                                        "fontSize": "0.75rem",     
                                        "height": "28px",          
                                        "padding": "0 2px",        
                                        "lineHeight": "1.2",   
                                        "display": "block",     
                                        "textAlign": "center",
                                        }
                                ),
                                
                                dcc.DatePickerSingle(
                                    id="Day",
                                    min_date_allowed= df.index.min().date(),
                                    max_date_allowed= df.index.max().date(),
                                    date=df.index.max().date(),
                                    display_format="YYYY-MM-DD",
                                    style={
                                        "width": "75%",
                                        "transform": "scale(0.75)",
                                        "display": "block"
                                        },
                                ),
                                dcc.DatePickerSingle(
                                    id="Month",
                                    min_date_allowed= df.index.min().date(),
                                    max_date_allowed= df.index.max().date(),
                                    date=df.index.min().date(),
                                    display_format="YYYY-MM",
                                    style={
                                        "width": "100%",
                                        "display": "none"
                                        }
                                ),
                                dcc.Dropdown(
                                    id="Year",
                                    options=[
                                        {"label": str(y), "value": str(y)}
                                        for y in range (df.index.min().year, df.index.max().year + 1 )
                                    ],
                                    value = str(df.index.min().year),
                                    clearable=False,
                                    style={
                                        "width": "80%",
                                        "display": "none"
                                        }
                                )
                            ],
                            style={
                                **kachel_layout,
                                "flex": "2"
                            },
                        ),
                    
                        # Relative Luftfeuchtigkeit
                        html.Div(
                            id="kachel_RH",
                            children=[
                                html.H2("Relative Luftfeuchtigkeit", 
                                        style={"textAlign": "center",
                                            "marginBottom": "0.3rem",
                                            "fontSize": "0.9rem",
                                            "fontWeight": "600",
                                            "flex": "0 0  1px"
                                }),
                                html.Div(
                                    "💡",
                                    id="info_icon_RH",
                                    style= {
                                        "position": "absolute",
                                        "top": "3px",
                                        "right": "6px",
                                        "cursor": "pointer",
                                        "fontSize": "1.1rem",
                                        "zIndex": "10",
                                    }
                                ),
                                dcc.Markdown(
                                    """
                                    **Relative Luftfeuchtigkeit**
                                    In dieser Kachel wird der minimale und maximale Wert (des Tages, Monats, Jahres) der relativen Luftfeuchtigkeit dargestellt. Fahren Sie mit der Maus über einen Balken um genauere Werte zu erhalten. 
                                    """,
                                    id="info_box_RH",
                                    style={
                                        "display": "none",
                                        "position": "relative",
                                        "top": "0",
                                        "right": "0",
                                        "left": "0",
                                        "bottom": "0",
                                        "padding": "1rem",
                                        "backgroundColor": "#f4edae8e",
                                        "zIndex": "9",
                                        "overflowY": "auto",
                                        "borderRadius": "15px"
                                    }
                                ),
                                dcc.Graph(
                                    id="R_Humidity",
                                    responsive=True,
                                    style={"height": "100%", "width": "100%", "flex": "1"}
                                )
                            ],
                            style={
                                **kachel_layout,
                                "flex": "5",
                                "display": "flex",
                                "flexDirection": "column",
                                "position": "relative"
                            },
                        ),

                        # Klimastation
                        html.Div(
                            id="kachel_card",
                            children=[
                                html.H2("Klimastation" + " "+ "(" + str(df.index.max().date()) + ")", 
                                        style={"textAlign": "center",
                                            "marginBottom": "0.3rem",
                                            "fontSize": "0.9rem",
                                            "fontWeight": "600",
                                            "flex": "0 0 1px"
                                            }
                                ),
                                html.Div(
                                    "💡",
                                    id="info_icon",
                                    style= {
                                        "position": "absolute",
                                        "top": "3px",
                                        "right": "6px",
                                        "cursor": "pointer",
                                        "fontSize": "1.1rem",
                                        "zIndex": "10",
                                    }
                                ),
                                dcc.Markdown(
                                    """
                                    **Klimastation**
                                    In dieser Kachel wird der Standort der Klimastation auf der Karte (orangener Punkt) verortet.
                                    Zusätzlich werden die aktuelle **Temperatur** (oben links), die aktuelle ** Relative Luftfeuchtigkeit** (oben rechts) und der aktuelle **Luftdruck** (unten links) angegeben. 
                                    """,
                                    id="info_box",
                                    style={
                                        "display": "none",
                                        "position": "relative",
                                        "top": "0",
                                        "right": "0",
                                        "left": "0",
                                        "bottom": "0",
                                        "padding": "1rem",
                                        "backgroundColor": "#f4edae8e",
                                        "zIndex": "9",
                                        "overflowY": "auto",
                                        "borderRadius": "15px"
                                    }
                                ),
                                dcc.Graph(
                                    id="map",
                                    figure=map,
                                    responsive=True,
                                    style={"height": "120px", "width": "100%", "flex": "1"},
                                    config={"displayModeBar": False,
                                            "scrollZoom": True,
                                            "responsive": True}
                                )
                            ],
                            style={
                                **kachel_layout,
                                "flex": "3",
                                "position": "relative"
                            },
                        )
                    ]
                ),

                # Mittlere Spalte
                html.Div(
                    style={
                        "flex": "6", 
                        "display": "flex", 
                        "flexDirection": "column", 
                        "minWidth": "600px", 
                        "maxWidth": "none", 
                        "height": "auto"
                        },
                    children=[
                        html.Div(
                            children=[
                                html.H1(
                                    "Klimastation Tübingen",
                                    style={"textAlign": "center", "marginBottom": "1rem", "flex": "6"},
                                ),
                            ],
                            style={
                                **kachel_layout,
                                "flex": "1.5",
                                #"flexDirection": "column",
                                "justifyContent": "flex-start",
                                "alignItems": "scretch",
                                "textAlign": "center",
                                "display": "flex", 
                                "flexDirection": "row"
                            },
                        ),
                        html.Div(
                            children=[
                                html.Div(
                                    "💡",
                                    id="info_icon_CL",
                                    style= {
                                        "position": "absolute",
                                        "top": "3px",
                                        "right": "6px",
                                        "cursor": "pointer",
                                        "fontSize": "1.1rem",
                                        "zIndex": "10",
                                    }
                                ),
                                dcc.Markdown(
                                    """
                                    **Auswahl Klimavarialen:**
                                    In dieser Kachel können Sie die Klimavariabeln, welche sie betrachten wollen selektieren.
                                     
                                    """,
                                    id="info_box_CL",
                                    style={
                                        "display": "none",
                                        "position": "relative",
                                        "top": "0",
                                        "right": "0",
                                        "left": "0",
                                        "bottom": "0",
                                        "padding": "1rem",
                                        "backgroundColor": "#f4edae8e",
                                        "zIndex": "9",
                                        "overflowY": "auto",
                                        "borderRadius": "15px"
                                    }
                                ),
                                 # Klimaelemente
                                dcc.Checklist(
                                    id="checklist_variables",
                                    options=[
                                        {"label": "Temperatur und Niederschlag ", "value":"temp_ns"},
                                        {"label": "Relative Luftfeuchtigkeit ", "value":"RH"},
                                        {"label": "Karte ", "value":"card"},
                                        {"label": "Wind ", "value":"wind"},
                                        {"label": "Solare Einstrahlung ", "value":"SR"},
                                        #{"label": "Datum ", "value":"date"},
                                    ],
                                    value=["temp_ns", "RH", "card", "wind", "SR", "date"],
                                    inline=True,
                                    style={"width": "100%", "textAlign": "center", "flex": "4"}
                                ),
                            ],
                            style={
                                **kachel_layout,
                                "flex": "0.5",
                                #"flexDirection": "column",
                                "justifyContent": "flex-start",
                                "alignItems": "scretch",
                                "textAlign": "center",
                                "display": "flex", 
                                "flexDirection": "row",
                                "position": "relative"
                            },
                        ),
                        
                        # Lufttemperatur & Niederschlag
                        html.Div(
                            id="kachel_temp_ns",
                            children=[
                                html.H2("Lufttemperatur und Niederschlag", 
                                        style={"textAlign": "center",
                                            "marginBottom": "0.3rem",
                                            "fontSize": "0.9rem",
                                            "fontWeight": "600",
                                            "flex": "0 0 1px"
                                }),
                                html.Div(
                                    "💡",
                                    id="info_icon_TN",
                                    style= {
                                        "position": "absolute",
                                        "top": "3px",
                                        "right": "6px",
                                        "cursor": "pointer",
                                        "fontSize": "1.1rem",
                                        "zIndex": "10",
                                    }
                                ),
                                dcc.Markdown(
                                    """
                                    **Lufttemperatur und Niederschlag:**
                                    In dieser Kachel werden Lufttemperatur und Niederschlag visualisiert.
                                    **Wichtig**: die Niederschlagssummen stellen nicht den tatsächlichen Wert dar, da die Sensorik des Messinstruments defekt ist.
                                    Eine **Lücke** in der Temperaturkurve bedeutet bspw., dass hier keine Messung stattgefunden hat.

                                    """,
                                    id="info_box_TN",
                                    style={
                                        "display": "none",
                                        "position": "relative",
                                        "top": "0",
                                        "right": "0",
                                        "left": "0",
                                        "bottom": "0",
                                        "padding": "1rem",
                                        "backgroundColor": "#f4edae8e",
                                        "zIndex": "9",
                                        "overflowY": "auto",
                                        "borderRadius": "15px"
                                    }
                                ),
                                dcc.Graph(
                                    id="temperature-graph",
                                    #figure=kachel1,
                                    responsive = True,
                                    style={
                                        "height": "100%", 
                                        "width": "100%",
                                        "padding": "0",
                                        "flex": "1"
                                        }  
                                )
                            ],
                            style={
                                **kachel_layout,
                                "flex": "8.5",
                                "display": "flex",
                                "flexDirection": "column", 
                                "position": "relative"
                            },
                        ),
                    ]
                ),


                # Rechte Spalte (flex 1, flex column)
                html.Div(
                    style={"flex": "3", "display": "flex", "flexDirection": "column"},
                    children=[
                        # Windrose oben
                        html.Div(
                            id="kachel_wind",
                            children=[
                                html.H2("Windrose", 
                                        style={"textAlign": "center",
                                            "marginBottom": "0.1rem",
                                            "fontSize": "0.9rem",
                                            "fontWeight": "600",
                                            "flex": "0 0 1px"
                                }),
                                html.Div(
                                    "💡",
                                    id="info_icon_W",
                                    style= {
                                        "position": "absolute",
                                        "top": "3px",
                                        "right": "6px",
                                        "cursor": "pointer",
                                        "fontSize": "1.1rem",
                                        "zIndex": "10",
                                    }
                                ),
                                dcc.Markdown(
                                    """
                                    **Wind:**
                                    In dieser Kachel wird die Windrichtung und die Windgeschwindigkeit visualisiert.
                                    Umso häufiger eine Windrichtung vorkommt, desto weiter nach Außen in der Windrose geht der Balken.
                                    Die Windgeschwindigkeit wird farblich dargestellt. 
                                    Die Windrichtungen wurden hier stündlich gemittelt und gezählt wie oft eine Windrichtung vorkam. Fährt man mit dem 
                                    Mauszeiger über die Visualisierung, so erhält man unter dem Wert "r:" die Verteilung wie oft der Wind aus der entsprechenden Richtung kommt
                                    und die Verteilung wie oft mit welcher Geschwindigkeit.
                                    
                                     
                                    """,
                                    id="info_box_W",
                                    style={
                                        "display": "none",
                                        "position": "relative",
                                        "top": "0",
                                        "right": "0",
                                        "left": "0",
                                        "bottom": "0",
                                        "padding": "1rem",
                                        "backgroundColor": "#f4edae8e",
                                        "zIndex": "9",
                                        "overflowY": "auto",
                                        "borderRadius": "15px"
                                    }
                                ),
                                dcc.Graph(
                                    id="Windrose",
                                    responsive = True,
                                    style={"height": "100%", "width": "100%", "flex": "1"}
                                )
                            ],
                            style={
                                **kachel_layout,
                                "flex": "6",
                                "display": "flex",
                                "flexDirection": "column",
                                "position": "relative"
                            },
                        ),

                # Solare Einstrahlung
                html.Div(
                    style={"flex": "6", "display": "flex", "flexDirection": "column"},
                    children=[
                        html.Div(
                            id="kachel_SR",
                            children=[
                                html.H2("Solare Einstrahlung", 
                                        style={"textAlign": "center",
                                            "marginBottom": "0.3rem",
                                            "fontSize": "0.9rem",
                                            "fontWeight": "600"
                                }),
                                html.Div(
                                    "💡",
                                    id="info_icon_SE",
                                    style= {
                                        "position": "absolute",
                                        "top": "3px",
                                        "right": "6px",
                                        "cursor": "pointer",
                                        "fontSize": "1.1rem",
                                        "zIndex": "10",
                                    }
                                ),
                                dcc.Markdown(
                                    """
                                    **Solare Einstrahlung:**
                                    Diese Visualisierung zeigt wie viel kW/qm zum jeweiligen Zeitpunkt von der Klimastation erfasst wurden.
                                    Weiße Stellen in der Darstellung zeigen Lücken in der Datenerhebung
                                    **Achtung** 0kW/qm wird hier in hellgelb dargestellt!
                                    

                                    """,
                                    id="info_box_SE",
                                    style={
                                        "display": "none",
                                        "position": "relative",
                                        "top": "0",
                                        "right": "0",
                                        "left": "0",
                                        "bottom": "0",
                                        "padding": "1rem",
                                        "backgroundColor": "#f4edae8e",
                                        "zIndex": "9",
                                        "overflowY": "auto",
                                        "borderRadius": "15px"
                                    }
                                ),
                                dcc.Graph(
                                    id="HM-solar",
                                    figure=fig_solar,
                                    responsive=True,
                                    style={"height": "90%", "width": "100%"}
                                )
                            ],
                            style={
                                **kachel_layout,
                                "flex": "4",
                                "position": "relative"
                            },
                        )
                    ]
                ),
                    ]
                )
            ]
        ),
    ])

# Callback Checkliste für Klimavariablen

@app.callback(
        [
            Output("kachel_temp_ns", "style"),
            Output("kachel_RH", "style"),
            Output("kachel_card", "style"),
            Output("kachel_wind", "style"),
            Output("kachel_SR", "style"),
            Output("kachel_date", "style")
        ], 
        Input("checklist_variables", "value"),
        [
            State("kachel_temp_ns", "style"),
            State("kachel_RH", "style"),
            State("kachel_card", "style"),
            State("kachel_wind", "style"),
            State("kachel_SR", "style"),
            State("kachel_date", "style")
        ],
        prevent_initial_call=False
)

# Methode für Auswahl der Klimavariablen

def updateVariables(selected, temp_ns_style, RH_style, card_style, wind_style, SR_style, date_style):
    blured={
        "filter": "blur(4px)",
        "opacity": "0.25",
        "transition": "0.3s"
    }

    showed={
        "filter": "none",
        "opacity": "1",
        "transition": "0.3s"
    }
    def apply(style_dict, climate_variable):
        base=dict(style_dict or {})
        if climate_variable in selected:
            base.update(showed)
        else:
            base.update(blured)
        return base

    return[
        apply(temp_ns_style, "temp_ns"),
        apply(RH_style, "RH"),
        apply(card_style, "card"),
        apply(wind_style, "wind"),
        apply(SR_style, "SR"),
        apply(date_style, "date")
    ]

# Callback Dropdown Datumsauswahl
@app.callback(
        Output("Day", "style"),
        Output("Month", "style"),
        Output("Year", "style"),
        Input("Auswahl-Dropdown", "value")
)

# Methode für Dropdown

def calender(zeitraum):
    hidden = {"display": "none", "width": "100%"} 
    visible = {"display": "block", "width": "100%"}
    if zeitraum == 'D':
        return visible, hidden, hidden
    elif zeitraum == 'M':
        return hidden, visible, hidden
    else:
        return hidden, hidden, visible

# Callback Dropdown Diagramm

@app.callback(
        Output("temperature-graph", "figure"),
        Input("Auswahl-Dropdown", "value"),
        Input("Day", "date"),
        Input("Month", "date"),
        Input("Year", "value")
)
# Methode für Temperatur und Niederschlag

def updateGraph(agg, Day, Month, Year):
    if agg == 'D':
        df_new = df[df.index.date == pd.to_datetime(Day).date()]
    elif agg == 'M':
        year = pd.to_datetime(Month).year
        month = pd.to_datetime(Month).month
        df_new = df[(df.index.year == year) & (df.index.month == month)]
    elif agg == 'Y':
        year = int(Year)
        df_new = df[df.index.year == year]

    # zweite if-Anweisung für Monatliche und jährlich Aggregation

    if agg == 'M':
        df_new = df_new.resample('D').agg({
            'AirTC_Avg': 'mean',
            'Rain_mm_Avg': 'sum'
        })
    elif agg == 'Y':
        df_new = df_new.resample('M').agg({
            'AirTC_Avg': 'mean',
            'Rain_mm_Avg': 'sum'
        })
    elif agg == 'D':
        df_new = df_new
    df_new = df_new.reset_index()

    fig_new = go.Figure()

    # Temperatur
    fig_new.add_trace(go.Scatter(
        x=df_new["TIMESTAMP"],
        y=df_new["AirTC_Avg"],
        name="Lufttemperatur (°C)",
        line=dict(color="#FB8C00", width=3),
        yaxis="y"
    ))

    # Niederschlag 
    if "Rain_mm_Avg" in df_new.columns:
        fig_new.add_trace(go.Bar(
            x=df_new["TIMESTAMP"],
            y=df_new["Rain_mm_Avg"],
            name="Niederschlag (mm)",
            marker_color="#79ABE5",
            marker = dict(
                color="#79ABE5"
            ),
            opacity=0.3,
            yaxis="y2"
        ))

    # Layout Täglich
    if agg == 'D':
        fig_new.update_layout(
            #title="Lufttemperatur und Niederschlag",
            xaxis_title="Datum / Uhrzeit",
            yaxis=dict(
                title="Temperatur (°C)",
                side="left",
                range=[-10,35]
            ),
            yaxis2=dict(
                title="Niederschlag (mm)",
                overlaying="y",
                side="right",
                range=[-10,35]
                
            ),
            legend=dict(x=0.01, y=0.99),
            margin=dict(l=0,r=0,t=20,b=0),
            template="plotly_white"
        )
    
    elif agg == 'M':
        fig_new.update_layout(
            #title="Lufttemperatur und Niederschlag",
            xaxis_title="Datum / Uhrzeit",
            yaxis=dict(
                title="Temperatur (°C)",
                side="left",
                range=[-10,35]
            ),
            yaxis2=dict(
                title="Niederschlag (mm)",
                overlaying="y",
                side="right",
                range=[-20,70]
                
            ),
            legend=dict(x=0.01, y=0.99),
            margin=dict(l=0,r=0,t=20,b=0),
            template="plotly_white"
        )
    
    elif agg == 'Y':
        fig_new.update_layout(
            #title="Lufttemperatur und Niederschlag",
            xaxis_title="Datum / Uhrzeit",
            yaxis=dict(
                title="Temperatur (°C)",
                side="left",
                range=[-10,35]
            ),
            yaxis2=dict(
                title="Niederschlag (mm)",
                overlaying="y",
                side="right",
                range=[-10,100]
                
            ),
            margin=dict(l=0,r=0,t=20,b=0),
            legend=dict(x=0.01, y=0.99),
            template="plotly_white"
        )

    fig_new.update_traces(offsetgroup=0)
    return fig_new
    

    return kachel1_new

# callback Wind
@app.callback(
    Output("Windrose", "figure"),
    [
        Input("Auswahl-Dropdown", "value"),
        Input("Day", "date"),
        Input("Month", "date"),
        Input("Year", "value")
    ]
)

# Methode für Windrose

def updateRose(time, Day, Month, Year):
    data = df_hourly.copy()
    data["TIMESTAMP"]= pd.to_datetime(data['TIMESTAMP'])

    max_Wind_v= data["WS_ms_Avg"].max()
    #print("Wind: ")
    #print(max_Wind_v)

    # Filter nach Zeitraum
    if time == 'D' and Day is not None:
        Day_t = pd.to_datetime(Day)
        data = data.loc[data['TIMESTAMP'].dt.date == Day_t.date()]
    elif time == 'M' and Month is not None:
        Month_t = pd.to_datetime(Month)
        data = data.loc[(data['TIMESTAMP'].dt.year == Month_t.year) &
                        (data['TIMESTAMP'].dt.month == Month_t.month)]
    elif time == 'Y' and Month is not None:
        year = pd.to_datetime(Year)
        data = data.loc[data['TIMESTAMP'].dt.year == year.year]

    if data.empty:
        # Wenn keine Daten vorhanden, leere Windrose zurückgeben
        return px.bar_polar(
            r=[0],
            theta=[0],
            template="plotly_white"
        )

    # Windrichtungen in 30°-Sektoren
    bins = list(range(0, 361, 22))
    labels = ["N", "NNO", "NO", "ONO", "O", "OSO", "SO", "SSO", "S", "SSW", "SW", "WWS", "W", "WWN", "NW", "NNW" ]
    data["WindDir_bins"] = pd.cut(data["WindDir"], bins=bins, labels=labels, right=False, include_lowest=True)
    counts = data["WindDir_bins"].value_counts().reset_index()
    counts.columns = ["dir", "count"]

    # Windgeschwindikeit
    v_bins = [0,0.2,0.5,1,3]
    v_labels=["0-0.2m/s","0.2-0.5m/s", "0.5-1m/s", "1-3m/s"]
    data["Wind_v_bins"] = pd.cut(data["WS_ms_Avg"], bins=v_bins, labels=v_labels, right=False, include_lowest=True)
    speed=(data.groupby(["WindDir_bins", "Wind_v_bins"]).size().reset_index(name="count"))

    # Richtige Ausrichtung der Windrose
    counts["dir"] = pd.Categorical(counts["dir"], categories=labels, ordered=True)
    counts = counts.sort_values("dir")

    fig_wind = go.Figure()

    wind_colors= ["#ccecff", "#66b2ff", "#1f78b4", "#08306b"]

    for label, color in zip(v_labels, wind_colors):
        sub = speed[speed["Wind_v_bins"] == label]

        fig_wind.add_trace(go.Barpolar(
            r=sub["count"],
            theta=sub["WindDir_bins"],
            name=label,
            marker=dict(color=color),
            opacity=0.9
        ))
    
    fig_wind.update_layout(
        template="plotly_white",
        legend=dict(font=dict(size=8),orientation="h", y=-0.15, x=0.5, xanchor="center"),
        margin=dict(l=0,r=0,t=0,b=30),
        polar=dict(
            angularaxis=dict(direction="clockwise", tickmode="array", tickvals=["N", "NO", "O", "SO", "S", "SW", "W", "NW"], ticks="", ticktext=["N", "NO", "O", "SO", "S", "SW", "W", "NW"] ,tickfont=dict(size=10)),
            radialaxis=dict(showticklabels=False, ticks="")
        )
    )

    return fig_wind

# callback Solare Einstrahlung
@app.callback(
        Output("HM-solar", "figure"),
        [
            Input("Auswahl-Dropdown", "value"),
            Input("Day", "date"),
            Input("Month", "date"),
            Input("Year", "value")
        ]  
)
# Methode für Solare Einstrahlung

def updateSolarMap(time, Day, Month, Year):
    data = df_hourly.copy()
    data["TIMESTAMP"] = pd.to_datetime(data["TIMESTAMP"])

    # Minimal und Maximalwert berechnen
    min = data["SlrkW_Avg"].dropna().min()
    max = data["SlrkW_Avg"].dropna().max()
    
    if time == 'D' and Day is not None:
        Day_t = pd.to_datetime(Day)
        data = data.loc[data['TIMESTAMP'].dt.date == Day_t.date()]

    elif time == 'M' and Month is not None:
        Month_t = pd.to_datetime(Month)
        data = data.loc[(data['TIMESTAMP'].dt.year == Month_t.year) &
                        (data['TIMESTAMP'].dt.month == Month_t.month)]
    elif time == 'Y' and Month is not None:
        year = pd.to_datetime(Year)
        data = data.loc[data['TIMESTAMP'].dt.year == year.year]

    if data.empty or data["SlrkW_Avg"].dropna().empty:
        return px.imshow(
            [[np.nan]],
            labels=dict(x="Zeit", y="Stunde", color="Solare Einstrahlung in kW/m^2"),
            aspect="auto",
            color_continous_scale="YlOrRd",
            template="plotly_white"
        )

    data["hour"]= data["TIMESTAMP"].dt.hour
    data["day"]= data["TIMESTAMP"].dt.day
    data["month"]= data["TIMESTAMP"].dt.month

    # Zeitebene für y-Achse bauen
    if time == 'Y':
        pivo_elem = data.pivot_table(values="SlrkW_Avg", index="hour", columns="month", aggfunc="mean")
        x_label = "Monat"
    else:
        pivo_elem=data.pivot_table(values="SlrkW_Avg", index="hour", columns="day", aggfunc="mean")
        x_label="Tag"
    if time == 'D':
        full_hours = pd.Index(range(24), name="hour")
        pivo_elem = pivo_elem.reindex(full_hours)


    colorscale = [
        [0.0, "white"],
        [0.05, "#fff8cc"],
        [0.1, "#ffec99"],
        [0.2, "#ffe066"],
        [0.3, "#ffd43b"],
        [0.4, "#ffb347"],
        [0.5, "#ffa94d"],
        [0.6, "#ff922b"],
        [0.7, "#ff6b08"],
        [0.8, "#fa4d0f"],
        [0.9, "#e03131"]
         
    ]

    fig_new = px.imshow(
        pivo_elem,
        labels=dict(x=x_label, y="Stunde", color="kW/m²"),
        color_continuous_scale="YlOrRd",
        zmin = min,
        zmax = max,
        template="plotly_white",
        aspect="auto"
    )
    #fig_new.update_traces(nancolor="lightgrey")

    fig_new.update_layout(
        #title="Solare Einstrahlung",
        #legend=dict(font=dict(size=8),orientation="h", y=-0.15, x=0.5, xanchor="center"),
        xaxis=dict(showticklabels=True, tickfont=dict(size=10), ticks="outside", automargin=True),
        yaxis=dict(title=dict(text="Stunden des Tages", font=dict(size=12)), tickfont=dict(size=11)),
        margin=dict(l=0, r=15, t=10, b=0),
        coloraxis_showscale=True,
        #autosize=True
    )
    fig_new.update_xaxes(
        tickmode="array",
        tickvals=list(range(len(pivo_elem.columns))),
        ticktext=[str(c) for c in pivo_elem.columns]
    )

    return fig_new

# callback für Relative Luftfeuchtigkeit
@app.callback(
        Output("R_Humidity", "figure"),
        [
            Input("Auswahl-Dropdown", "value"),
            Input("Day", "date"),
            Input("Month", "date"),
            Input("Year", "value")
        ]  
)

# Methode für Relative Luftfeuchtigkeit

def displayHumidity(time, Day, Month, Year):
    data = df_hourly.copy()
    data["TIMESTAMP"] = pd.to_datetime(data["TIMESTAMP"])
    
    if time == 'D' and Day is not None:
        Day_t = pd.to_datetime(Day)
        data = data.loc[data['TIMESTAMP'].dt.date == Day_t.date()]
    elif time == 'M' and Month is not None:
        Month_t = pd.to_datetime(Month)
        data = data.loc[(data['TIMESTAMP'].dt.year == Month_t.year) &
                        (data['TIMESTAMP'].dt.month == Month_t.month)]
    elif time == 'Y' and Year is not None:
        year = pd.to_datetime(Year)
        data = data.loc[data['TIMESTAMP'].dt.year == year.year]

    if data.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Keine Daten verfügbar",
            x=0.5, y=0.5, showarrow=False, font=dict(size=14),
            xref="paper", yref="paper"
        )
        return fig_RH
    
    min_RH= data["RH_Avg"].min()
    max_RH= data["RH_Avg"].max()

    fig_RH = go.Figure()
    fig_RH.add_bar(
        x=["Min", "Max"],
        y=[100, 100],
        marker_color="rgba(200,200,200,0.3)",
        marker_line_color="black",
        marker_line_width=1.5,
        width=0.5,
        hoverinfo="skip",
    )
    
    fig_RH.add_bar(
        x=["Min", "Max"],
        y=[min_RH, max_RH],
        marker= dict(
            color=["rgba(30,144,255,0.8)", "rgba(30,144,255,0.8)"],
            line=dict(color="black", width=2)
        ),
        width=0.5,
        hovertemplate="%{x}: %{y:.1f}%<extra></extra>"
    )

    # layout
    fig_RH.update_layout(
        #title="",
        yaxis=dict(range=[0,100], title=dict(text="Relative<br>Luftfeuchtigkeit [%]", font=dict(size=12)), tickfont=dict(size=11)),
        xaxis=dict(title=""),
        barmode="overlay",
        plot_bgcolor="white",
        paper_bgcolor="white",
        bargap=0.3,
        margin=dict(r=0, l=0, t=20, b=20),
        showlegend=False
    )

    return fig_RH

# Infobox Relative Luftfeuchtigkeit

@app.callback(
    Output("info_box_RH", "style"),
    Input("info_icon_RH", "n_clicks"),
    State("info_box_RH", "style"),
    prevent_initial_call=True
)

# Methode für Info Box RH
def displayInfoBox_RH(n_clicks, style):
    if style["display"] == "none":
        style["display"] = "block"
    else:
        style["display"] = "none"
    return style


# Infobox Klimastation
@app.callback(
    Output("info_box", "style"),
    Input("info_icon", "n_clicks"),
    State("info_box", "style"),
    prevent_initial_call=True
)

# Methode für Info box Klimastation

def displayInfoBox_CL(n_clicks, style):
    if style["display"] == "none":
        style["display"] = "block"
    else:
        style["display"] = "none"
    return style

# Infobox Checkbox
@app.callback(
    Output("info_box_CL", "style"),
    Input("info_icon_CL", "n_clicks"),
    State("info_box_CL", "style"),
    prevent_initial_call=True
)

# Methode für Info box Checkbox

def displayInfoBox(n_clicks, style):
    if style["display"] == "none":
        style["display"] = "block"
    else:
        style["display"] = "none"
    return style

# Infobox Temperatur und Niederschlag
@app.callback(
    Output("info_box_TN", "style"),
    Input("info_icon_TN", "n_clicks"),
    State("info_box_TN", "style"),
    prevent_initial_call=True
)

# Methode für Info box Temperatur und Niederschlag

def displayInfoBox_TN(n_clicks, style):
    if style["display"] == "none":
        style["display"] = "block"
    else:
        style["display"] = "none"
    return style

# Infobox Wind
@app.callback(
    Output("info_box_W", "style"),
    Input("info_icon_W", "n_clicks"),
    State("info_box_W", "style"),
    prevent_initial_call=True
)

# Methode für Info box Wind

def displayInfoBox_W(n_clicks, style):
    if style["display"] == "none":
        style["display"] = "block"
    else:
        style["display"] = "none"
    return style

# Infobox Solare EInstrahlung
@app.callback(
    Output("info_box_SE", "style"),
    Input("info_icon_SE", "n_clicks"),
    State("info_box_SE", "style"),
    prevent_initial_call=True
)

# Methode für Info box Solare Einstrahlung

def displayInfoBox_SE(n_clicks, style):
    if style["display"] == "none":
        style["display"] = "block"
    else:
        style["display"] = "none"
    return style


# App 
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=False,
            )


