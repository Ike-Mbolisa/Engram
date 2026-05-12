import json
import ctypes
import obd
import pandas as pd
from asammdf import MDF

_lib = ctypes.CDLL("./Core/gear.dll")
_lib.estimate_gear.restype = ctypes.c_int
_lib.estimate_gear.argtypes = [
    ctypes.c_double,
    ctypes.c_double,
    ctypes.c_double,
    ctypes.c_double,
    ctypes.POINTER(ctypes.c_double),
    ctypes.c_int
]

'''
Loading the car from the .json file to get the correct gear ratio, final drive and tire size
____________________________________
Indlæser info om bilen fra en .json fil, hvor vi har de rigtige gearforhold, hovedgear og dækstørrelse
'''
def load_car(path: str) -> dict:
    with open(path) as f:
        car = json.load(f)
        print(f"{car['year']} {car['make']} {car['model']}")
        return car

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
    if not connection.is_connected():
        raise ConnectionError("No OBD connection available")
    Revolutions = connection.query(obd.commands.RPM).value.magnitude
    Velocity = connection.query(obd.commands.SPEED).value.to("km/h").magnitude
    return Revolutions, Velocity

def live_gear_estimate(car: dict) -> int:
    Revolutions, Velocity = read_obd()
    return estimate_gear(Revolutions, Velocity, car)

'''
Since OBD does not send gear data, we will estimate with the gear ratio, speed and tyre size
The function itself is in gear.c and gear.dll. what you see is merely a wrapper
____________________________________
Vi gætter på hvilket gear man er i via. gearforhold, fart og dæk størrelse 
Funktionen likker i gear.c og gear.dll. det er er herinde er bare en wrapper
'''
def estimate_gear(Revolutions, Velocity, car: dict):
   ratios = list(car['gear_ratios'].values())
   arr = (ctypes.c_double * len(ratios))(*ratios)
   return _lib.estimate_gear(Revolutions, Velocity,
                              car['tyre_circumference'], car['final_drive'],
                              arr, len(ratios))
'''
The data is exported as a CSV file called output.csv
We define it as coloums in a data set that we'll use to creat the csv structure
____________________________________
Dataen bliver eksporteret som en CSV file der hedder output.csv
we definer kolonnerne, der dermed skal bruges til at oprette csv strukturen
'''
def export_csv(input_file: str, car: dict, output_file: str = 'output.csv'):
    mdf = MDF(input_file)
    
    df = mdf.to_dataframe()
    
    Revolutions_col = next((c for c in df.columns if 'Revolutions' in c.lower()), None)
    Velocity_col = next((c for c in df.columns if 'Velocity' in c.lower()), None)
    
    if Revolutions_col and Velocity_col:
        df['gear'] = df.apply(
            lambda row: estimate_gear(row[Revolutions_col], row[Velocity_col], car), axis=1
        )
    
    df.to_csv(output_file)
    return df

'''
Code runner
____________________________________
Kode kører

'''
if __name__ == "__main__":
    car = load_car("cars/nissan_qashqai_2021.json")
    gear = live_gear_estimate(car)
    print(f"Current gear: {gear}")