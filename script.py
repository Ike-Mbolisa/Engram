import obd
import pandas

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
