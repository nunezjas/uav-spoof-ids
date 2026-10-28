import os, glob, json
import numpy as np
import pandas as pd
from pyulog import ULog

log_dir  = os.path.expanduser("~/uav-spoof-ids/data/raw/px4_logs/")
out_dir  = os.path.expanduser("~/uav-spoof-ids/data/processed/px4/")
os.makedirs(out_dir, exist_ok=True)

logs = sorted(glob.glob(log_dir + "*.ulg"))
print(f"Parsing {len(logs)} logs...")

summary = []
parsed  = 0
skipped = 0

for i, log_path in enumerate(logs):
    uid = os.path.basename(log_path).replace('.ulg','')
    try:
        ulog  = ULog(log_path, disable_str_exceptions=True)
        dur_s = (ulog.last_timestamp - ulog.start_timestamp) / 1e6

        if dur_s < 30:
            skipped += 1
            continue

        params   = ulog.initial_parameters
        mav_type = params.get('MAV_TYPE', -1)
        topics   = {d.name: d for d in ulog.data_list}

        if 'vehicle_gps_position' not in topics:
            skipped += 1
            continue

        dfs = {}

        gps = topics['vehicle_gps_position']
        n   = len(gps.data['timestamp'])
        dfs['gps'] = pd.DataFrame({
            'time_s':        gps.data['timestamp'] / 1e6,
            'gnss_lat_deg':  gps.data['lat'] / 1e7,
            'gnss_lon_deg':  gps.data['lon'] / 1e7,
            'gnss_alt_m':    gps.data['alt'] / 1e3,
            'gnss_vel_n_ms': gps.data.get('vel_n_m_s', np.zeros(n)),
            'gnss_vel_e_ms': gps.data.get('vel_e_m_s', np.zeros(n)),
            'gnss_vel_d_ms': gps.data.get('vel_d_m_s', np.zeros(n)),
            'gnss_hacc_m':   gps.data.get('eph',        np.zeros(n)),
            'gnss_vacc_m':   gps.data.get('epv',        np.zeros(n)),
            'gnss_num_sv':   gps.data.get('satellites_used', np.zeros(n)),
        })

        imu_topic = 'sensor_combined' if 'sensor_combined' in topics else 'vehicle_imu'
        if imu_topic in topics:
            imu = topics[imu_topic]
            if imu_topic == 'sensor_combined':
                dfs['imu'] = pd.DataFrame({
                    'time_s':      imu.data['timestamp'] / 1e6,
                    'imu_ax_ms2':  imu.data['accelerometer_m_s2[0]'],
                    'imu_ay_ms2':  imu.data['accelerometer_m_s2[1]'],
                    'imu_az_ms2':  imu.data['accelerometer_m_s2[2]'],
                    'imu_gx_rads': imu.data['gyro_rad[0]'],
                    'imu_gy_rads': imu.data['gyro_rad[1]'],
                    'imu_gz_rads': imu.data['gyro_rad[2]'],
                })
            else:
                dfs['imu'] = pd.DataFrame({
                    'time_s':      imu.data['timestamp'] / 1e6,
                    'imu_ax_ms2':  imu.data['delta_velocity[0]'],
                    'imu_ay_ms2':  imu.data['delta_velocity[1]'],
                    'imu_az_ms2':  imu.data['delta_velocity[2]'],
                    'imu_gx_rads': imu.data['delta_angle[0]'],
                    'imu_gy_rads': imu.data['delta_angle[1]'],
                    'imu_gz_rads': imu.data['delta_angle[2]'],
                })

        if 'vehicle_air_data' in topics:
            baro = topics['vehicle_air_data']
            dfs['baro'] = pd.DataFrame({
                'time_s':     baro.data['timestamp'] / 1e6,
                'baro_alt_m': baro.data['baro_alt_meter'],
            })

        if 'vehicle_magnetometer' in topics:
            mag = topics['vehicle_magnetometer']
            dfs['mag'] = pd.DataFrame({
                'time_s':      mag.data['timestamp'] / 1e6,
                'mag_x_gauss': mag.data['magnetometer_ga[0]'],
                'mag_y_gauss': mag.data['magnetometer_ga[1]'],
                'mag_z_gauss': mag.data['magnetometer_ga[2]'],
            })

        ekf_topic = 'estimator_innovations' if 'estimator_innovations' in topics else 'ekf2_innovations'
        if ekf_topic in topics:
            ekf = topics[ekf_topic]
            ekf_cols = {'time_s': ekf.data['timestamp'] / 1e6}
            for col in ['vel_pos_innov[0]','vel_pos_innov[1]','vel_pos_innov[2]',
                        'vel_pos_innov[3]','vel_pos_innov[4]','vel_pos_innov[5]',
                        'mag_innov[0]']:
                if col in ekf.data:
                    ekf_cols['ekf_' + col.replace('[','_').replace(']','')] = ekf.data[col]
            dfs['ekf'] = pd.DataFrame(ekf_cols)

        df_out = dfs['gps'].copy()
        for name, df in dfs.items():
            if name == 'gps':
                continue
            df_out = pd.merge_asof(
                df_out.sort_values('time_s'),
                df.sort_values('time_s'),
                on='time_s', direction='nearest', tolerance=0.1
            )

        df_out['source']       = 'PX4'
        df_out['label']        = 0
        df_out['spoof_type']   = 'none'
        df_out['mav_type']     = mav_type
        df_out['vehicle_uuid'] = uid
        df_out['duration_s']   = dur_s

        out_path = f"{out_dir}{uid}.parquet"
        df_out.to_parquet(out_path, index=False)
        parsed += 1

        if parsed % 20 == 0 or parsed == 1:
            print(f"[{i+1}/{len(logs)}] Parsed {parsed} | "
                  f"MAV={mav_type} dur={dur_s:.0f}s rows={len(df_out)}")

        summary.append({
            'uuid': uid, 'mav_type': mav_type,
            'duration_s': dur_s, 'rows': len(df_out),
            'has_imu': 'imu' in dfs, 'has_baro': 'baro' in dfs,
            'has_mag': 'mag' in dfs, 'has_ekf': 'ekf' in dfs,
        })

    except Exception as e:
        skipped += 1
        if skipped <= 5:
            print(f"  SKIP {uid[:20]}: {e}")

print(f"\nDone: {parsed} parsed, {skipped} skipped")
with open(out_dir + "parse_summary.json", 'w') as f:
    json.dump(summary, f, indent=2)
print(f"Summary saved to {out_dir}parse_summary.json")
