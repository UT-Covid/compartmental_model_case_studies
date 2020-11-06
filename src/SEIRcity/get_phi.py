#!/usr/bin/env python


def get_phi(c_reduction, interval_per_day, phi_all, phi_school,
            phi_work, phi_home):
    """contact matrices"""
    phi = dict()
    phi_all_per_int = phi_all / interval_per_day
    phi_school_per_int = phi_school / interval_per_day
    phi_work_per_int = phi_work / interval_per_day
    phi_home_per_int = phi_home / interval_per_day
    phi_other_per_int = phi_all_per_int - phi_school_per_int - phi_work_per_int - phi_home_per_int

    phi_open_weekday = phi_all_per_int
    phi_open_weekend = phi_home_per_int + phi_other_per_int
    phi_open_weekday_holiday = phi_open_weekend
    phi_close_weekday = phi_home_per_int + (1 - c_reduction) * (phi_work_per_int + phi_other_per_int)
    phi_close_weekend = phi_home_per_int + (1 - c_reduction) * phi_other_per_int
    phi_close_weekday_holiday = phi_close_weekend
    phi_open = [phi_open_weekday, phi_open_weekend, phi_open_weekday_holiday]
    phi_close = [phi_close_weekday, phi_close_weekend, phi_close_weekday_holiday]
    
    phi['open'] = phi_open
    phi['close'] = phi_close
    return phi
