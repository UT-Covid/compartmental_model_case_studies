# Shell helpers for TApis jobs
. lib/runtime.sh

# Tell Tapis to skip archiving these dynamically-generated paths
for F in __pycache__ src data
do
    noarchive ${F}
done

for D in outputs
do
    mkdir -p $D
done

# Unzip 
unzip -nq static.zip

# Set up Python environment (since we're not in a container)
python3 -B -m pip --disable-pip-version-check -q install --user -r requirements.txt -q

# Run the config generator
python3 -B -m src.SEIRcity.cli -O config.yml ${ASYMP_RATE} ${CITY} ${CONTACT_REDUCTION} ${DATA_FOLDER} ${DOUBLE_TIME} ${D_RELATIVE_RISK_IN_HIGH} ${GROWTH_RATE_LIST} ${HIGH_RISK_RATIO} ${H_FATALITY_RATIO} ${H_RELATIVE_RISK_IN_HIGH} ${INFECTION_FATALITY_RATIO} ${NUM_SIM} ${NUM_SIM_FIT} ${OVERALL_H_RATIO} ${PROP_TRANS_IN_E} ${R0} ${RESULTS_DIR} ${START_CONDITION} ${T_EXPOSED_DIST} ${T_EXPOSED_PARA} ${T_H_TO_D} ${T_H_TO_R} ${T_ONSET_TO_H} ${T_Y_TO_R_DIST} ${T_Y_TO_R_PARA} ${beta0_dict} ${deterministic} ${hosp_data_fp} ${interval_per_day} ${is_fitting} ${monitor_lag} ${n_risk} ${report_rate} ${sd_date} ${shift_week} ${time_begin_sim} ${total_time} ${trigger_type} ${verbose}

# Run the simulation
python3 -B -m src.SEIRcity --threads 8 --out-fp outputs/output.pckl --config-yaml config.yml

exit 0
