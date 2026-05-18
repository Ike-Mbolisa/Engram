import json
import math
import ctypes
import os
import threading
import obd
from asammdf import MDF
import dearpygui.dearpygui as dpg


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
    ctypes.c_double,                   # revolutions
    ctypes.c_double,                   # velocity
    ctypes.c_double,                   # tyre_circumference
    ctypes.c_double,                   # final_drive
    ctypes.POINTER(ctypes.c_double),   # gear_ratios
    ctypes.c_int,                      # num_gears
    ctypes.POINTER(ctypes.c_double),   # confidence_out (nullable)
]

_lib.smooth_signal.restype = ctypes.c_double
_lib.smooth_signal.argtypes = [
    ctypes.POINTER(ctypes.c_double),   # buffer
    ctypes.POINTER(ctypes.c_int),      # head
    ctypes.c_int,                      # size
    ctypes.c_double,                   # new_sample
]

_lib.estimate_gear_batch.restype = None
_lib.estimate_gear_batch.argtypes = [
    ctypes.POINTER(ctypes.c_double),   # revolutions
    ctypes.POINTER(ctypes.c_double),   # velocities
    ctypes.c_int,                      # count
    ctypes.c_double,                   # tyre_circumference
    ctypes.c_double,                   # final_drive
    ctypes.POINTER(ctypes.c_double),   # gear_ratios
    ctypes.c_int,                      # num_gears
    ctypes.POINTER(ctypes.c_int),      # output
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
    gear, _ = estimate_gear(Revolutions, Velocity, car)
    return gear

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
    confidence = ctypes.c_double(0.0)
    gear = _lib.estimate_gear(Revolutions, Velocity,
                               car['tyre_circumference'], car['final_drive'],
                               arr, len(ratios), ctypes.byref(confidence))
    return gear, confidence.value
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

    Revolutions_col = next((c for c in df.columns if 'revolutions' in c.lower()), None)
    Velocity_col = next((c for c in df.columns if 'velocity' in c.lower()), None)

    if Revolutions_col and Velocity_col:
        ratios = list(car['gear_ratios'].values())
        ratio_arr = (ctypes.c_double * len(ratios))(*ratios)
        n = len(df)
        rpm_arr = (ctypes.c_double * n)(*df[Revolutions_col].tolist())
        vel_arr = (ctypes.c_double * n)(*df[Velocity_col].tolist())
        out_arr = (ctypes.c_int * n)()
        _lib.estimate_gear_batch(rpm_arr, vel_arr, ctypes.c_int(n),
                                  car['tyre_circumference'], car['final_drive'],
                                  ratio_arr, ctypes.c_int(len(ratios)), out_arr)
        df['gear'] = list(out_arr)

    df.to_csv(output_file)
    return df

'''
Code runner
____________________________________
Kode kører

'''
if __name__ == "__main__":
    # Pre-load all cars from the directory
    car_files = os.listdir("cars/")
    cars = [load_car(f"cars/{f}") for f in car_files]
    car_labels = [f"{c['year']} {c['make']} {c['model']}" for c in cars]

    def on_start():
        dpg.configure_item("start_menu", show=False)
        dpg.configure_item("selection_menu", show=True)

    def on_create():
        dpg.configure_item("start_menu", show=False)
        dpg.configure_item("create_menu", show=True)

    def obd_loop(car):
        SMOOTH_SIZE = 5
        rpm_buf  = (ctypes.c_double * SMOOTH_SIZE)(*([0.0] * SMOOTH_SIZE))
        rpm_head = ctypes.c_int(0)
        spd_buf  = (ctypes.c_double * SMOOTH_SIZE)(*([0.0] * SMOOTH_SIZE))
        spd_head = ctypes.c_int(0)
        while dpg.is_dearpygui_running():
            try:
                rpm, speed = read_obd()
                smooth_rpm   = _lib.smooth_signal(rpm_buf,  ctypes.byref(rpm_head),  SMOOTH_SIZE, rpm)
                smooth_speed = _lib.smooth_signal(spd_buf,  ctypes.byref(spd_head),  SMOOTH_SIZE, speed)
                gear, confidence = estimate_gear(smooth_rpm, smooth_speed, car)
                dpg.set_value("rpm_plot",     [smooth_rpm])
                dpg.set_value("speed_plot",   [smooth_speed])
                dpg.set_value("gear_display", f"Gear: {gear}  (confidence: {confidence:.3f})")
            except Exception:
                pass

    def on_confirm_select():
        selected_label = dpg.get_value("car_combo")
        idx = car_labels.index(selected_label)
        car = cars[idx]
        dpg.configure_item("selection_menu", show=False)
        dpg.configure_item("Revolutions", show=True)
        dpg.configure_item("Velocity", show=True)
        threading.Thread(target=obd_loop, args=(car,), daemon=True).start()

    def on_confirm_create():
        make        = dpg.get_value("input_make")
        model       = dpg.get_value("input_model")
        year        = dpg.get_value("input_year")
        tyre_width  = dpg.get_value("input_tyre_width")
        tyre_aspect = dpg.get_value("input_tyre_aspect")
        tyre_rim    = round(dpg.get_value("input_tyre_rim"), 1)
        final_drive = round(dpg.get_value("input_final_drive"), 4)
        num_gears   = dpg.get_value("input_num_gears")
        gear_ratios = {str(i): round(dpg.get_value(f"input_gear_{i}"), 4) for i in range(1, num_gears + 1)}

        car_data = {
            "make": make,
            "model": model,
            "year": year,
            "tyre": {"width": tyre_width, "aspect": tyre_aspect, "rim": tyre_rim},
            "final_drive": final_drive,
            "gear_ratios": gear_ratios
        }

        filename = f"cars/{make.lower()}_{model.lower()}_{year}.json"
        with open(filename, "w") as f:
            json.dump(car_data, f, indent=2)

        new_car = load_car(filename)
        cars.append(new_car)
        car_labels.append(f"{year} {make} {model}")
        dpg.configure_item("car_combo", items=car_labels)

        dpg.configure_item("create_menu", show=False)
        dpg.configure_item("start_menu", show=True)

    dpg.create_context()
    dpg.create_viewport()
    dpg.setup_dearpygui()

    with dpg.window(label="Start Menu", tag="start_menu"):
        dpg.add_text("Welcome to Sprygan")
        dpg.add_button(label="Start", callback=on_start)
        dpg.add_button(label="Create Car Profile", callback=on_create)

    with dpg.window(label="Select Car", tag="selection_menu", show=False):
        dpg.add_text("Choose your car")
        dpg.add_combo(car_labels, label="Car", tag="car_combo")
        dpg.add_button(label="Confirm", callback=on_confirm_select)

    with dpg.window(label="Create Car profile", tag="create_menu", show=False,width=500):
        dpg.add_text("Car Info")
        dpg.add_input_text(label="Make",  tag="input_make")
        dpg.add_input_text(label="Model", tag="input_model")
        dpg.add_input_int( label="Year",  tag="input_year")
        dpg.add_separator()
        dpg.add_text("Tyre")
        dpg.add_input_int(  label="Width (mm)",   tag="input_tyre_width")
        dpg.add_input_int(  label="Aspect (%)",   tag="input_tyre_aspect")
        dpg.add_input_float(label="Rim (inches)", tag="input_tyre_rim")
        dpg.add_separator()
        dpg.add_text("Drivetrain")
        dpg.add_input_float(label="Final Drive Ratio", tag="input_final_drive")
        dpg.add_input_int(  label="Number of Gears",   tag="input_num_gears", default_value=6, min_value=4, max_value=8)
        dpg.add_separator()
        dpg.add_text("Gear Ratios")
        for i in range(1, 9):
            dpg.add_input_float(label=f"Gear {i}", tag=f"input_gear_{i}")
        dpg.add_separator()
        dpg.add_button(label="Confirm", callback=on_confirm_create)
        dpg.add_button(label="Cancel",  callback=lambda: (dpg.configure_item("create_menu", show=False), dpg.configure_item("start_menu", show=True)))

    with dpg.window(label="Revolutions", tag="Revolutions", show=False):
        dpg.add_text("RPM")
        dpg.add_text("Gear: --", tag="gear_display")
        dpg.add_simple_plot(label="RPM Plot", tag="rpm_plot", default_value=(0.3, 0.9, 0.5, 0.3), height=300)
        dpg.add_simple_plot(label="RPM Histogram", default_value=(0.3, 0.9, 2.5, 8.9), overlay="Overlaying", height=180,
                        histogram=True)

    with dpg.window(label="Velocity", tag="Velocity", show=False):
        dpg.add_text("Velocity")
        dpg.add_simple_plot(label="Speed Plot", tag="speed_plot", default_value=(0.3, 0.9, 0.5, 0.3), height=300)
        dpg.add_simple_plot(label="Speed Histogram", default_value=(0.3, 0.9, 2.5, 8.9), overlay="Overlaying", height=180,
                        histogram=True)

    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

'''
This is how the CLI version of main looks
____________________________________
Det her er hvordan CLI versionen af main ser ud


    files = os.listdir("cars/")
    for i, file in enumerate(files):
        car = load_car(f"cars/{file}")
        print(f"{i + 1}. {car['year']} {car['make']} {car['model']}")

    selection = int(input("Select car: ")) - 1
    car = load_car(f"cars/{files[selection]}")
    print(f"Selected: {car['year']} {car['make']} {car['model']}")
    live_gear_estimate(car) '''
