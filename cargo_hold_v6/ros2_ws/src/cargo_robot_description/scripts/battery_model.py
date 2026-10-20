"""Pure energy arithmetic for an assumed power model, not a BMS driver."""
def update_soc(soc,bus_power_W,dt_s,nominal_Wh,capacity_derate,distribution_efficiency):
    if min(nominal_Wh,capacity_derate,distribution_efficiency)<=0:raise ValueError('Invalid battery capacity')
    used=max(0,bus_power_W)*max(0,dt_s)/(3600*nominal_Wh*capacity_derate*distribution_efficiency)
    return max(0,min(1,soc-used))
