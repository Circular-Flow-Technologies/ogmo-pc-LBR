import numpy as np


#-------------------
# PARAMETERS
#-------------------

# inflow mass flow rate [kg/s] (estimated average over one day)
m_dot_in = 10. / (24*3600.)

# evaporation rate [kg/s] (from experiment)
m_dot_evap = 1000. / (1000*3600.)

# peristalitic pumps mass flow rate [kg/s] (from calibration)
m_dot_M0102 =  549. /(1000*60.)
m_dot_M0203 = 1430. /(1000*60.)

# number of intervals (chosen)
N_f_evi  =  6.
N_f_conc =  1.

# evaporator overflow fraction
phi_OF_evi = 0.2

#-------------------
# CALCULATIONS
#-------------------

# input time parameters for evaporator feed pump (M0102) [s]
tau_M0102_runtime  = np.round(24*3600*m_dot_in*(1+phi_OF_evi)/(N_f_evi*m_dot_M0102),0)
tau_M0102_interval = np.round(24*3600/N_f_evi,0)

m_dot_evi = N_f_evi*m_dot_M0102*tau_M0102_runtime/(24*3600)

# input time parameters for concentrate discharge pump (M0203) [s]
tau_M0203_runtime  = np.round(24*3600*(m_dot_evi - m_dot_evap - phi_OF_evi*m_dot_in)/(N_f_conc*m_dot_M0203),0)
tau_M0203_interval = np.round(24*3600/N_f_conc,0)


#-------------------
# PLOTTING
#-------------------

print(f"\ntau_M0102_runtime:  {tau_M0102_runtime}")
print(f"\ntau_M0102_interval: {tau_M0102_interval}")
print(f"\ntau_M0203_runtime:  {tau_M0203_runtime}")
print(f"\ntau_M0203_interval: {tau_M0203_interval}")

