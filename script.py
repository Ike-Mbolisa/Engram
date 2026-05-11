import json
import obd
import pandas as pd
from asammdf import MDF

'''
Loading the car from the .json file to get the correct gear ratio, final drive and tire size
____________________________________
Indlæser info om bilen fra en .json fil, hvor vi har de rigtige gearforhold, hovedgear og dækstørrelse
'''
def load_car(path: str) -> dict:
    with open(path) as f: 
        print(json.make + json.model + json.year)
        return json.load(f)

'''
Function for loading the carWe group all the sensor data into function, 
Only 1 connection is opened at a time

It establishes a connection and sends query requests for rpm and speed.
These will be used in the rest of the functions
____________________________________
Alt sensor data hænger under denne funktion
Programmet kan kun lave 1 forbindelse af gangen

Den opretter forbindelse og derefter sender anmodninger via query
Her får vi rpm og fart data, som der bliver brugt i andre funktioner
'''
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

'''
Since OBD does not send gear data, we will estimate with the gear ratio, speed and tyre size
____________________________________
Vi gætter på hvilket gear man er i via. gearforhold, fart og dæk størrelse 
'''
def estimate_gear(Revolutions, Velocity): 
   if Velocity == 0:
       return 0
   Velocity_ms = Velocity / 3.6
   calculated_ratio = (Revolutions / 60 * json.tyre_circumference) / (Velocity_ms * json.final_drive)
   closest_gear = min(json.gear_ratio, key=lambda g: abs(json.gear_ratio[g] - calculated_ratio))
   return closest_gear
'''
The data is exported as a CSV file called output.csv
We define it as coloums in a data set that we'll use to creat the csv structure
____________________________________
Dataen bliver eksporteret som en CSV file der hedder output.csv
we definer kolonnerne, der dermed skal bruges til at oprette csv strukturen
'''
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
