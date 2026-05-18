#include <stddef.h>

/*
__declspec(dllexport) is used to declare what file type this should become when its run
____________________________________
__declspec(dllexport) bruges til at erklære hvilken fil type programmet skal være når den er kompileret
*/

/*
estimate_gear finds the closest matching gear by comparing the calculated ratio
against each gear ratio. confidence_out receives the difference from the best
match — pass NULL to ignore it.
____________________________________
estimate_gear finder det nærmeste gear ved at sammenligne det beregnede forhold
med hvert gearforhold. confidence_out får forskellen fra det bedste match — send NULL for at ignorere.
*/
__declspec(dllexport)
int estimate_gear(double revolutions, double velocity,
                  double tyre_circumference, double final_drive,
                  double* gear_ratios, int num_gears,
                  double* confidence_out)
{
    if (velocity == 0) {
        if (confidence_out != NULL) *confidence_out = 9999.0;
        return 0;
    }

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

    if (confidence_out != NULL)
        *confidence_out = closest_diff;

    return closest_gear;
}

/*
smooth_signal is a moving average over a ring buffer of size `size`.
The caller owns the buffer and head index so state persists across calls.
____________________________________
smooth_signal er et glidende gennemsnit over en ringbuffer af størrelsen `size`.
Kalderen ejer bufferen og head-indekset, så tilstanden bevares mellem kald.
*/
__declspec(dllexport)
double smooth_signal(double* buffer, int* head, int size, double new_sample)
{
    buffer[*head % size] = new_sample;
    (*head)++;
    int count = *head < size ? *head : size;
    double sum = 0.0;
    for (int i = 0; i < count; i++)
        sum += buffer[i];
    return sum / count;
}

/*
estimate_gear_batch runs estimate_gear over full arrays of RPM and speed,
writing results into output[]. Faster than calling per-row from Python.
____________________________________
estimate_gear_batch kører estimate_gear over fulde arrays af omdrejninger og hastighed
og skriver resultaterne i output[]. Hurtigere end at kalde per række fra Python.
*/
__declspec(dllexport)
void estimate_gear_batch(double* revolutions, double* velocities, int count,
                         double tyre_circumference, double final_drive,
                         double* gear_ratios, int num_gears, int* output)
{
    for (int i = 0; i < count; i++) {
        output[i] = estimate_gear(revolutions[i], velocities[i],
                                   tyre_circumference, final_drive,
                                   gear_ratios, num_gears, NULL);
    }
}
