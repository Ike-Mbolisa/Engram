import json
import obd
import pandas as pd
from asammdf import MDF

def load_car(path: str) -> dict:
    with open(path) as f:
        print(json.make + json.model + json.year)
        return json.load(f)

def read_obd() -> tuple[float, float]:
    connection = obd.OBD()
    Revolutions = connection.query(obd.commands.RPM).value.magnitude
    Velocity = connection.query(obd.commands.SPEED).value.to("km/h").magnitude
    if connection == False:
        export_csv()    
    
    return Revolutions, Velocity

def live_gear_estimate() -> int:
    Revolutions, Velocity = read_obd()
    return estimate_gear(Revolutions, Velocity)

def estimate_gear(Revolutions, Velocity):
   if Velocity == 0:
       return 0
   Velocity_ms = Velocity / 3.6
   calculated_ratio = (Revolutions / 60 * json.tyre_circumference) / (Velocity_ms * json.final_drive)
   closest_gear = min(json.gear_ratio, key=lambda g: abs(json.gear_ratio[g] - calculated_ratio))
   return closest_gear

def export_csv(input_file: str, output_file: str = 'output.csv'):
    mdf = MDF(input_file)
    
    df = mdf.to_dataframe()
    
    Revolutions_col = next((c for c in df.columns if 'Revolutions' in c.lower()), None)
    Velocity_col = next((c for c in df.columns if 'Velocity' in c.lower()), None)
    
    if Revolutions_col and Velocity_col:
        df['gear'] = df.apply(
            lambda row: estimate_gear(row[Revolutions_col], row[Velocity_col]), axis=1
        )
    
    df.to_csv(output_file)
    return df
