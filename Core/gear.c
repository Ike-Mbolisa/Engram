/* 
__declspec(dllexport) is used to declare what file type this should become when its run
____________________________________
__declspec(dllexport) bruges til at erklære hvilken fil type programmet skal være når den er kompileret

*/
__declspec(dllexport)  

/* declares the data types we are gonna use in this program
We'll use Revolutions, Velocity, tyre circumference, gear ratio and final drive
All of these are important for finding the true gear the car is in
____________________________________
erklære datatyperene der bliver brugt i programmet
Vi skal bruger omdrejninger, hastighed, dæk omkreds, gearforhold og final drive
Alle af dem er vigtig. De er alle sammen double fordi der er ikke garentee at det er hele tal
*/
int estimate_gear(double revolutions, double velocity,
                  double tyre_circumference, double final_drive,
                  double* gear_ratios, int num_gears)
/* 
if velocity is 0, return nothing
____________________________________
hvis hastigheden er nul, så skal der ikke ske noget.
*/
                  {
    if (velocity == 0)
        return 0;

/* 
Convert km/h to m/s, because the math requires m/s but the standard OBD will give km/h
____________________________________
Omskriv km/t til m/s, fordi formlen kræver m/s men OBD sender altid i km/h
*/        
    double velocity_ms = velocity / 3.6;
    double calculated_ratio = (revolutions / 60.0 * tyre_circumference) / (velocity_ms * final_drive);

    int closest_gear = 1;
    double closest_diff = 9999.0;

    for (int i = 0; i < num_gears; i++) {
        double diff = gear_ratios[i] - calculated_ratio;
        if (diff < 0) diff = -diff;
        if (diff < closest_diff) {
            closest_diff = diff;
            closest_gear = i + 1;
        }
    }
/* 
return the closest matching gear
____________________________________
retunere det gear bilen er i
*/
    return closest_gear;
}
