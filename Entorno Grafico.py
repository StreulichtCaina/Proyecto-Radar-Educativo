import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import serial, sys, glob
import serial.tools.list_ports as COMs
import time

############################################
# Configuración
############################################
FADE_TIME = 3.0
MAX_DISTANCE = 120.0

############################################
# Encontrar puerto del micro:bit
############################################

def find_microbit_port():
    ports = COMs.comports()
    for port in ports:
        if ('SERIAL' in port.description.upper() or 
            'USB' in port.description.upper()):
            print(f"Puerto encontrado: {port.device} - {port.description}")
            return port.device
    return None

port1 = find_microbit_port()
if not port1:
    print("No se encontró micro:bit.")
    sys.exit(1)

print(f"Conectando al puerto: {port1}")
try:
    ser = serial.Serial(port1, baudrate=115200, timeout=1)
    ser.flush()
    print("Conexión establecida correctamente")
except Exception as e:
    print(f"Error al conectar: {e}")
    sys.exit(1)

############################################
# Configuración del plot
############################################
fig, ax = plt.subplots(subplot_kw={'polar': True}, facecolor='k', figsize=(10, 8))
ax.set_facecolor('#006d70')
ax.set_ylim(0, MAX_DISTANCE)
ax.set_xlim(0, np.pi)
ax.tick_params(colors='w')
ax.grid(color='w', alpha=0.3)

angles = np.arange(0, 181, 1)
theta = angles * (np.pi / 180.0)
all_dists = np.full(181, MAX_DISTANCE)
point_times = np.zeros(181)

# Plot inicial
points, = ax.plot([], [], 'wo', markersize=8, alpha=0.9, markeredgecolor='#EFEFEF', markeredgewidth=1.0)
line, = ax.plot([0, 0], [0, MAX_DISTANCE], 'w-', linewidth=4.0)  # Línea más gruesa

debug_text = ax.text(0.02, 0.95, '', transform=ax.transAxes, color='white', 
                    fontsize=10, verticalalignment='top')

plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.15)
fig.canvas.manager.set_window_title('Microbit Radar - Sincronizado')

############################################
# Botones de control
############################################
stop_bool = False
data_received = 0
last_data_time = time.time()

def stop_event(event):
    global stop_bool
    stop_bool = True
    print("Deteniendo programa...")

def clear_event(event):
    global all_dists, point_times
    all_dists = np.full(181, MAX_DISTANCE)
    point_times = np.zeros(181)
    print("Datos limpiados")

ax_stop = plt.axes([0.85, 0.05, 0.1, 0.04])
btn_stop = Button(ax_stop, 'Stop', color='lightcoral', hovercolor='red')
btn_stop.on_clicked(stop_event)

ax_clear = plt.axes([0.85, 0.10, 0.1, 0.04])
btn_clear = Button(ax_clear, 'Clear', color='lightblue', hovercolor='blue')
btn_clear.on_clicked(clear_event)

plt.ion()
plt.show()

############################################
# Loop principal - SINCRONIZADO
############################################
print("Esperando datos del micro:bit...")
print("La línea seguirá el ángulo REAL del micro:bit")
print("-----------------------------------------------")

last_update = time.time()
last_angle = 0  # Último ángulo recibido del micro:bit

try:
    while not stop_bool:
        current_time = time.time()
        delta_time = current_time - last_update
        
        # Actualizar desvanecimiento
        if delta_time > 0.1:
            visible_theta = []
            visible_dists = []
            points_visible = 0
            
            for i in range(181):
                if point_times[i] > 0:
                    elapsed = current_time - point_times[i]
                    if elapsed > FADE_TIME:
                        all_dists[i] = MAX_DISTANCE
                    else:
                        if all_dists[i] < MAX_DISTANCE:
                            visible_theta.append(theta[i])
                            visible_dists.append(all_dists[i])
                            points_visible += 1
            
            # Actualizar puntos
            points.set_data(visible_theta, visible_dists)
            
            # Mantener la línea en el último ángulo recibido
            if last_angle != 0:
                line_angle_rad = last_angle * np.pi / 180.0
                line.set_data([line_angle_rad, line_angle_rad], [0, MAX_DISTANCE])
            
            # Debug info
            time_since_last_data = current_time - last_data_time
            debug_info = f"Datos: {data_received}\nPuntos: {points_visible}\nÁngulo: {last_angle}°\nÚltimo: {time_since_last_data:.1f}s"
            debug_text.set_text(debug_info)
            
            plt.draw()
            plt.pause(0.01)
            last_update = current_time
        
        # Leer datos seriales - SINCRONIZACIÓN REAL
        if ser.in_waiting > 0:
            try:
                raw_data = ser.readline()
                data = raw_data.decode('utf-8', errors='ignore').strip()
                
                if "Radar Start" in data:
                    print("Escaneo iniciado desde micro:bit")
                    continue
                elif "Radar Stop" in data:
                    print("Escaneo detenido desde micro:bit")
                    continue
                elif "System Ready" in data:
                    print("Micro:bit listo")
                    continue
                
                if ',' in data:
                    parts = data.split(',')
                    if len(parts) >= 2:
                        angle = int(float(parts[0]))
                        distance = float(parts[1])
                        
                        if 0 <= angle <= 180 and 0 < distance <= MAX_DISTANCE:
                            # ACTUALIZAR ÁNGULO ACTUAL (sincronización real)
                            last_angle = angle
                            
                            all_dists[angle] = distance
                            point_times[angle] = current_time
                            data_received += 1
                            last_data_time = current_time
                            
                            # Actualizar línea inmediatamente con el ángulo REAL
                            line_angle_rad = angle * np.pi / 180.0
                            line.set_data([line_angle_rad, line_angle_rad], [0, MAX_DISTANCE])
                            
                            # Debug: mostrar cada dato
                            print(f"Ángulo: {angle}°, Distancia: {distance}cm")
                            
                            # Actualizar plot inmediatamente para feedback rápido
                            visible_theta = []
                            visible_dists = []
                            for i in range(181):
                                if point_times[i] > 0 and current_time - point_times[i] <= FADE_TIME and all_dists[i] < MAX_DISTANCE:
                                    visible_theta.append(theta[i])
                                    visible_dists.append(all_dists[i])
                            
                            points.set_data(visible_theta, visible_dists)
                            plt.draw()
                            plt.pause(0.001)
                            
            except Exception as e:
                print(f"Error procesando dato: {e}")
                continue
                
        plt.pause(0.001)
        
except KeyboardInterrupt:
    print("Interrupción por teclado")

finally:
    try:
        ser.close()
        print("Conexión serial cerrada")
    except:
        pass
    plt.ioff()
    plt.close()
    print(f"Programa terminado. Datos recibidos: {data_received}")
