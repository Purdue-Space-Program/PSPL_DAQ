import synnax as sy
import numpy as np
import time

sy_client = sy.Synnax(
    host='sedsdaq.ecn.purdue.edu',
    port=2701,
    username='Bill',
    password='Bill',
    secure=False,
)

HEATER_ENABLE  = 0
HEATER_DISABLE = 1

HEATER_CHANNEL = 'TEST-01_cmd'
TEMP_CHANNEL = 'TC-BATTERY'

PID_KP = 20
PID_KI = 0.1
PID_KD = 5
PID_SETPOINT = 280.0

PWM_CYCLE_SEC = 2.0

class PIDController:
    def __init__(self, target_temp, kp, ki, kd):
        self.target_temp = target_temp
        self.kp = kp
        self.ki = ki
        self.kd = kd
        
        self.integral = 0.0
        self.last_error = 0.0

    def calculate(self, current_temp: float, dt: float) -> float:
        if dt <= 0:
            dt = 0.001 

        error = self.target_temp - current_temp
        
        P = self.kp * error
        
        self.integral += error * dt
        I = self.ki * self.integral
        
        derivative = (error - self.last_error) / dt
        D = self.kd * derivative
        
        self.last_error = error
        
        total_power = P + I + D
        
        if total_power > 100.0 or total_power < 0.0:
            self.integral -= error * dt 
        
        return max(0.0, min(100.0, total_power))

def run_heater_control(sy_client, HEATER_CHANNEL, TEMP_CHANNEL, HEATER_ENABLE, HEATER_DISABLE):
    
    pid_controller = PIDController(PID_SETPOINT, PID_KP, PID_KI, PID_KD)
    
    with sy_client.control.acquire(
        'Heater Control',
        write=[HEATER_CHANNEL],
        read=[TEMP_CHANNEL],
        write_authorities=[120],
    ) as ctrl:
        
        temps = []
        last_time = time.time()

        print(f"Starting PID Control. Target: {PID_SETPOINT}K")

        while True:
            ctrl.wait_until_defined(TEMP_CHANNEL)
            latest_temp = ctrl[TEMP_CHANNEL]
            temps.append(latest_temp)

            if len(temps) >= 10:
                averaged_temp = np.sum(temps) / len(temps)
                
                now = time.time()
                dt = now - last_time
                if dt <= 0: dt = 0.001
                last_time = now

                target_power_percent = pid_controller.calculate(averaged_temp, dt)

                cycle_position = now % PWM_CYCLE_SEC
                
                on_duration = (target_power_percent / 100.0) * PWM_CYCLE_SEC
                
                if cycle_position < on_duration:
                    ctrl[HEATER_CHANNEL] = HEATER_ENABLE
                else:
                    ctrl[HEATER_CHANNEL] = HEATER_DISABLE
                
                print(f"Temp: {averaged_temp:.2f}K | Error: {PID_SETPOINT - averaged_temp:.2f}K | Power: {target_power_percent:.1f}%")

                temps = temps[1:]
                
            time.sleep(0.1)

if __name__ == '__main__':
    try:
        run_heater_control(sy_client, HEATER_CHANNEL, TEMP_CHANNEL, HEATER_ENABLE, HEATER_DISABLE)
    except KeyboardInterrupt:
        pass
