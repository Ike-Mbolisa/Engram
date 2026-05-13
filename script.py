import json
import math
import ctypes
import os
import obd
from asammdf import MDF
'''
ctypes are used here because it's impossible for python to read raw C or compiled C on its own.
ctypes is simply a library that can read compiled C code in the form of .dll files.
The data types used in the file is declared here, so that the "estimate_gear" can read the right data
____________________________________
ctypes bruges fordi det er umuligt for Python at læse normal eller kompileret C kode
ctypes er bare en library der kan læse kompileret C kode i .dll filer, men ikke normal C filer
Dataen der bliver brugt i filen skal 

'''
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
        t = car['tyre']
        sidewall_mm = t['width'] * (t['aspect'] / 100)
        diameter_mm = t['rim'] * 25.4 + 2 * sidewall_mm
        car['tyre_circumference'] = math.pi * diameter_mm / 1000
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
'''
The function prompts the program to read the Revolutions and velocity of the car. 
Upon reading it returns said values and sends them to the next function
____________________________________
Funktionen får programmet til at læse hvor mange hurtig bilen er og hvor mange omdregninger moteren laver
Når det er bleven læst, så sendes dataen til den næste funktion

'''
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
    for file in os.listdir(r"cars/"):
        car = load_car(f"cars/{file}")
        print(f"{car['year']} {car['make']} {car['model']}")