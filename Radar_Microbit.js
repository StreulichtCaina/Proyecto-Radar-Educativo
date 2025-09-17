// Conexiones:
// - Servo: Pin P2
// - Sensor HC-SR04: Trig = P9, Echo = P0

// Variables globales
let scanning = false
let currentAngle = 0
let scanDirection = 1  // 1 = derecha, -1 = izquierda

// Mostrar logo inicial
basic.showIcon(IconNames.Yes)
basic.pause(1000)
basic.showString("RADAR")
basic.pause(500)

// Inicializar servo en posición 0
pins.servoWritePin(AnalogPin.P2, 0)
basic.pause(1000)

// Función para medir distancia con HC-SR04
function measureDistance(): number {
    // Enviar pulso de trigger
    pins.digitalWritePin(DigitalPin.P9, 0)
    control.waitMicros(2)
    pins.digitalWritePin(DigitalPin.P9, 1)
    control.waitMicros(10)
    pins.digitalWritePin(DigitalPin.P9, 0)

    // Medir tiempo de eco
    const duration = pins.pulseIn(DigitalPin.P0, PulseValue.High, 30000)

    // Calcular distancia en centímetros
    if (duration > 0) {
        return Math.idiv(duration, 58)  // Fórmula estándar para cm
    }
    return 0  // Si no hay eco, retornar 0
}

// Botón A: Iniciar/Detener escaneo
input.onButtonPressed(Button.A, function () {
    scanning = !scanning
    if (scanning) {
        basic.showIcon(IconNames.Yes)
        serial.writeLine("Radar Start")
        basic.clearScreen()
    } else {
        basic.showIcon(IconNames.No)
        serial.writeLine("Radar Stop")
        // Regresar servo a posición 0 cuando se detiene
        pins.servoWritePin(AnalogPin.P2, 0)
    }
})

// Botón B: Mostrar información
input.onButtonPressed(Button.B, function () {
    basic.showString("ANG:" + currentAngle)
    basic.pause(1000)
    basic.showString("SCAN:" + (scanning ? "ON" : "OFF"))
})

// Función principal de escaneo
function scan() {
    if (!scanning) return

    // Mover servo al ángulo actual
    pins.servoWritePin(AnalogPin.P2, currentAngle)
    basic.pause(50)  // Esperar a que el servo se estabilice

    // Medir distancia
    let distance = measureDistance()

    // Filtrar lecturas erróneas (más de 400cm o 0)
    if (distance > 0 && distance < 400) {
        // Enviar datos por serial: ángulo,distancia
        serial.writeLine("" + currentAngle + "," + distance)
    }

    // Actualizar ángulo para siguiente movimiento
    currentAngle += scanDirection * 5  // Mover de 5 en 5 grados

    // Cambiar dirección si llega a los límites
    if (currentAngle >= 180) {
        currentAngle = 180
        scanDirection = -1  // Cambiar a izquierda
    } else if (currentAngle <= 0) {
        currentAngle = 0
        scanDirection = 1   // Cambiar a derecha
    }
}

// Loop principal
basic.forever(function () {
    if (scanning) {
        scan()
        basic.pause(100)  // Pausa entre mediciones
    } else {
        basic.pause(200)  // Pausa más larga cuando no escanea
    }
})

// Indicador LED de actividad
basic.forever(function () {
    if (scanning) {
        led.toggle(0, 0)  // LED parpadeante cuando escanea
        basic.pause(200)
    }
})

// Enviar señal de ready al iniciar
basic.forever(function () {
    serial.writeLine("System Ready")
    basic.pause(5000)  // Enviar cada 5 segundos
})
