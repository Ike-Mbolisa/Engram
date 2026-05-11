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
def estimate_gear(rpm, speed_kmh):
   if speed_kmh == 0:
       return 0
   speed_ms = speed_kmh / 3.6
   calculated_ratio = (rpm / 60 * TYRE) / (speed_ms * FINAL_DRIVE)
   closest_gear = min(GEAR_RATIOS, key=lambda g: abs(GEAR_RATIOS[g] - calculated_ratio))
   return closest_gear

def export_csv(input_file: str, output_file: str = 'output.csv'):
    mdf = MDF(input_file)
    
    df = mdf.to_dataframe()
    
    rpm_col = next((c for c in df.columns if 'rpm' in c.lower()), None)
    speed_col = next((c for c in df.columns if 'speed' in c.lower()), None)
    
    if rpm_col and speed_col:
        df['gear'] = df.apply(
            lambda row: estimate_gear(row[rpm_col], row[speed_col]), axis=1
        )
    
    df.to_csv(output_file)
    return df
