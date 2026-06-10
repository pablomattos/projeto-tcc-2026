#include <Wire.h>
#include <math.h>

#define AD5933_ADDR 0x0D

// ======================================================
// CLOCK E CONFIGURAÇÕES DE VARREDURA
// ======================================================
const double CLK_FREQ = 16776000.0; 
const long startFreq = 10000;   
const long freqIncr  = 1000;    
const int TOTAL_POINTS = 91; 
const int numIncr = TOTAL_POINTS - 1;

// ======================================================
// CONFIGURAÇÕES DE HARDWARE (RFB Adicionado)
// ======================================================
const double R_CAL = 1459.0; 
const double RFB   = 1480.0; // Resistor de realimentação física no shield
const int settlingCycles = 500; // Estabilização aumentada para precisão

// ======================================================
// ARRAYS DE CALIBRAÇÃO
// ======================================================
double gainFactors[TOTAL_POINTS]; 
double systemPhases[TOTAL_POINTS]; 
bool sistemaCalibrado = false; 

// --- Funções de Comunicação I2C ---
void writeReg(byte reg, byte val) {
  Wire.beginTransmission(AD5933_ADDR);
  Wire.write(reg); Wire.write(val);
  Wire.endTransmission();
}

int readData(byte reg) {
  Wire.beginTransmission(AD5933_ADDR);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return 0; 
  Wire.requestFrom(AD5933_ADDR, 2);
  if (Wire.available() < 2) return 0;
  return (int16_t)((Wire.read() << 8) | Wire.read()); 
}

byte readStatus() {
  Wire.beginTransmission(AD5933_ADDR);
  Wire.write(0x8F);
  if (Wire.endTransmission(false) != 0) return 0;
  Wire.requestFrom(AD5933_ADDR, 1);
  return Wire.available() ? Wire.read() : 0;
}

bool aguardarDados() {
  unsigned long timeout = millis() + 2000;
  while (millis() < timeout) {
    if (readStatus() & 0x02) return true;
    delay(2); 
  }
  return false;
}

// --- Função de Média para Estabilidade ---
bool lerMedia(double &realMedio, double &imagMedio) {
  const int samples = 20; // Aumentado para 20 amostras conforme discutido
  double somaReal = 0; double somaImag = 0;
  for (int i = 0; i < samples; i++) {
    if (!aguardarDados()) return false;
    somaReal += (double)readData(0x94);
    somaImag += (double)readData(0x96);
    delay(1); 
  }
  realMedio = somaReal / samples; 
  imagMedio = somaImag / samples;
  return true;
}

void setFrequency(byte reg, long freqHz) {
  long freqCode = (long)((freqHz / (CLK_FREQ / 4.0)) * pow(2, 27));
  writeReg(reg, (freqCode >> 16) & 0xFF); 
  writeReg(reg + 1, (freqCode >> 8) & 0xFF); 
  writeReg(reg + 2, freqCode & 0xFF); 
}

void configurarSettlingTime(int cycles) {
  writeReg(0x8A, (cycles >> 8) & 0x01); 
  writeReg(0x8B, cycles & 0xFF); 
}

void resetAD5933() {
  writeReg(0x80, 0x10); delay(10);
  writeReg(0x80, 0xB0); delay(100);
}

void iniciarSweep() {
  writeReg(0x80, 0x11); delay(100); 
  writeReg(0x80, 0x21); delay(100); 
}

void executarCalibracaoCompleta() {
  Serial.printf("\n🎯 INICIANDO CALIBRAÇÃO (RFB:%0.2f, RCAL:%0.2f)\n", RFB, R_CAL);
  resetAD5933();
  configurarSettlingTime(settlingCycles);
  iniciarSweep(); 

  for (int i = 0; i < TOTAL_POINTS; i++) {
    double r, im;
    if (!lerMedia(r, im)) break;
    
    double mag = sqrt(pow(r, 2) + pow(im, 2));
    // O Gain Factor absorve a influência do RFB automaticamente
    gainFactors[i] = (1.0 / R_CAL) / mag;
    systemPhases[i] = atan2(im, r) * (180.0 / M_PI);

    if (i % 10 == 0) Serial.printf("Progresso: %d%%\n", (i * 100) / numIncr);
    
    writeReg(0x80, 0x31); // Incrementa frequência [6]
    delay(15); 
  }
  sistemaCalibrado = true;
  Serial.println("✅ CALIBRAÇÃO CONCLUÍDA");
}

void setup() {
  Serial.begin(115200);
  delay(3000);
  Wire.begin(21, 22); 
  Wire.setClock(100000); 

  setFrequency(0x82, startFreq);
  setFrequency(0x85, freqIncr);
  writeReg(0x88, (numIncr >> 8) & 0xFF); 
  writeReg(0x89, numIncr & 0xFF); 
  configurarSettlingTime(settlingCycles);
  
  Serial.println("🚀 AD5933 + ESP32 Inicializado");
}

void loop() {
  if (!sistemaCalibrado) {
    executarCalibracaoCompleta();
    return;
  }

  resetAD5933();
  iniciarSweep();
  Serial.println("\nFreq(Hz),Impedancia(Ohm),Fase(°)");

  for (int i = 0; i < TOTAL_POINTS; i++) {
    double r, im;
    if (!lerMedia(r, im)) break;

    double mag = sqrt(pow(r, 2) + pow(im, 2));
    double impedance = 1.0 / (gainFactors[i] * mag);
    double rawPhase = atan2(im, r) * (180.0 / M_PI);
    double correctedPhase = rawPhase - systemPhases[i];

    if (correctedPhase > 180) correctedPhase -= 360;
    if (correctedPhase < -180) correctedPhase += 360;

    Serial.printf("%ld,%.2f,%.2f\n", startFreq + (i * freqIncr), impedance, correctedPhase);
    
    writeReg(0x80, 0x31);
    delay(10); 
  }
  
  Serial.println("\n========================");
  Serial.println("Nova varredura em 10s");
  Serial.println("========================"); 
  delay(10000);
}