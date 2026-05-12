__declspec(dllexport)
int estimate_gear(double revolutions, double velocity,
                  double tyre_circumference, double final_drive,
                  double* gear_ratios, int num_gears)
{
    if (velocity == 0)
        return 0;

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

    return closest_gear;
}
