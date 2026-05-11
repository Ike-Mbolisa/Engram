import obd
import pandas as pd
from asammdf import MDF

TYRE = 2.154  # meters
FINAL_DRIVE = 4.214
GEAR_RATIOS = {
   1: 3.727,
   2: 1.947,
   3: 1.323,
   4: 0.975,
   5: 0.763,
   6: 0.638
}
def read_obd() -> tuple[float, float]:
    connection = obd.OBD()
    Revolutions = connection.query(obd.commands.RPM).value.magnitude
    Velocity = connection.query(obd.commands.SPEED).value.to("km/h").magnitude
    return Revolutions, Velocity

def live_gear_estimate() -> int:
    Revolutions, Velocity = read_obd()
    return estimate_gear(Revolutions, Velocity)

def estimate_gear(Revolutions, Velocity):
   if Velocity == 0:
       return 0
   Velocity_ms = Velocity / 3.6
   calculated_ratio = (Revolutions / 60 * TYRE) / (Velocity_ms * FINAL_DRIVE)
   closest_gear = min(GEAR_RATIOS, key=lambda g: abs(GEAR_RATIOS[g] - calculated_ratio))
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
