#include <Wire.h>
#include <math.h>
#include <Preferences.h>

#define AD5933_ADDR 0x0D
const double CLK_FREQ = 16776000; 
const double R_CAL = 97320.0;
const double RFB = 97230.0;      

long startFreq = 10000; 
long freqIncr = 1000;   
int numIncr = 90;       
double gainFactor = 0.0;

// Buffers para média móvel de cada parâmetro (janela de 5 leituras)
#define WINDOW_SIZE 5
struct Measurement {
  double imp, phase, real, imag, mag;
};
Measurement windows[91][WINDOW_SIZE];  // 91 frequências x 5 leituras
int windowIndices[91];                 // Índice atual de cada janela
int windowCounts[91];                  // Contagem de leituras válidas por frequência

Preferences preferences;

void resetI2C() {
  Wire.end();
  delay(100);
  Wire.begin(21, 22); 
  Wire.setClock(400000);
  delay(200);
  Serial.println("🔄 I2C resetado");
}

bool testAD5933() {
  Wire.beginTransmission(AD5933_ADDR);
  byte error = Wire.endTransmission();
  Serial.printf("   I2C Test AD5933(0x%02X): %s\n", AD5933_ADDR, error == 0 ? "OK" : "FALHOU");
  return error == 0;
}

void writeReg(byte reg, byte val) {
  Wire.beginTransmission(AD5933_ADDR);
  Wire.write(reg);
  Wire.write(val);
  byte error = Wire.endTransmission();
  if (error != 0) {
    Serial.printf("❌ WriteReg(0x%02X,0x%02X) ERRO: %d\n", reg, val, error);
  }
}

void setFrequency(byte reg, long freqHz) {
  long val = (long)((freqHz / (CLK_FREQ / 4.0)) * pow(2, 27));
  writeReg(reg, (val >> 16) & 0xFF);
  writeReg(reg + 1, (val >> 8) & 0xFF);
  writeReg(reg + 2, val & 0xFF);
}

byte readStatus() {
  Wire.beginTransmission(AD5933_ADDR);
  Wire.write(0x8F);
  Wire.endTransmission();
  Wire.requestFrom(AD5933_ADDR, 1);
  return Wire.read();
}

int readData(byte reg) {
  Wire.beginTransmission(AD5933_ADDR);
  Wire.write(reg);
  Wire.endTransmission();
  Wire.requestFrom(AD5933_ADDR, 2);
  return (int16_t)((Wire.read() << 8) | Wire.read());
}

bool waitValid(int max_ms = 3000) {
  unsigned long timeout = millis() + max_ms;
  while (millis() < timeout) {
    byte status = readStatus();
    if (status & 0x02) return true;
    delay(5);
  }
  Serial.printf("⏰ Status final: 0x%02X\n", readStatus());
  return false;
}

// Calcula média móvel para uma frequência específica
void calculateMovingAverage(int freqIndex, Measurement* avg) {
  double sumImp = 0, sumPhase = 0, sumReal = 0, sumImag = 0, sumMag = 0;
  int count = windowCounts[freqIndex];
  
  for (int i = 0; i < count; i++) {
    sumImp += windows[freqIndex][i].imp;
    sumPhase += windows[freqIndex][i].phase;
    sumReal += windows[freqIndex][i].real;
    sumImag += windows[freqIndex][i].imag;
    sumMag += windows[freqIndex][i].mag;
  }
  
  avg->imp = sumImp / count;
  avg->phase = sumPhase / count;
  avg->real = sumReal / count;
  avg->imag = sumImag / count;
  avg->mag = sumMag / count;
}

void initMovingAverageBuffers() {
  for (int i = 0; i <= numIncr; i++) {
    windowIndices[i] = 0;
    windowCounts[i] = 0;
    for (int j = 0; j < WINDOW_SIZE; j++) {
      windows[i][j].imp = 0;
      windows[i][j].phase = 0;
      windows[i][j].real = 0;
      windows[i][j].imag = 0;
      windows[i][j].mag = 0;
    }
  }
  Serial.println("📊 Buffers de média móvel inicializados");
}

void loadCalibration() {
  preferences.begin("ad5933", false);
  gainFactor = preferences.getDouble("gain", 0.0);
  preferences.end();
  
  Serial.printf("📂 Gain carregado: %.12f\n", gainFactor);
  
  if (gainFactor > 0.0) {
    Serial.printf("✅ Calibração carregada: %.12f\n", gainFactor);
  } else {
    Serial.println("❌ Sem calibração. Calibrando...\n");
  }
  
  initMovingAverageBuffers();
}

void saveCalibration() {
  preferences.begin("ad5933", false);
  preferences.putDouble("gain", gainFactor);
  preferences.end();
  Serial.printf("💾 SALVO: Gain = %.12f\n\n", gainFactor);
}

void setup() {
  Serial.begin(115200);
  delay(4000);
  
  Serial.println("\n🚀 AD5933 IMPEDÂNCIA ANALYZER - MÉDIA MÓVEL");
  Serial.printf("   RFB = %.0fΩ | Rcal = %.0fΩ | Janela: %d leituras\n", RFB, R_CAL, WINDOW_SIZE);
  
  resetI2C();
  
  if (!testAD5933()) {
    Serial.println("❌ AD5933 NÃO RESPONDE! Verifique fiação I2C.");
    Serial.println("   SDA=GPIO21 | SCL=GPIO22 | Pull-ups 4.7kΩ");
    while(1) {
      resetI2C();
      delay(2000);
    }
  }
  
  // CSV SIMPLIFICADO: só Freq + médias móveis
  Serial.println("Freq(Hz),Imp_AVG(Ohm),Fase_AVG(°),Real_AVG(Ohm),Imag_AVG(Ohm),Mag_AVG,N");
  Serial.println("═══════════════════════════════════════════════════════════════════════════════");
  
  setFrequency(0x82, startFreq);
  setFrequency(0x85, freqIncr);
  writeReg(0x88, (numIncr >> 8) & 0xFF);
  writeReg(0x89, numIncr & 0xFF);

  loadCalibration();
  
  if (gainFactor <= 0.0) {
    calibrate();
    saveCalibration();
  }
  
  Serial.println("✅ SISTEMA PRONTO!\n");
}

void calibrate() {
  Serial.println("🎯 CALIBRANDO com Rcal...");
  
  writeReg(0x80, 0x10);
  delay(100);
  writeReg(0x80, 0xB0);
  delay(200);
  
  writeReg(0x80, 0xB1);
  writeReg(0x80, 0x11); 
  delay(1000);
  writeReg(0x80, 0x21); 
  
  Serial.print("   Aguardando dados... ");
  if (!waitValid(5000)) {
    Serial.println("❌ TIMEOUT CALIBRAÇÃO!");
    return;
  }
  Serial.println("OK");
  
  delay(200);
  
  double realCal = readData(0x94);
  double imagCal = readData(0x96);
  double magCal = sqrt(pow(realCal, 2) + pow(imagCal, 2));
  
  gainFactor = (1.0 / R_CAL) / magCal;
  
  Serial.printf("📊 Calibração OK:\n");
  Serial.printf("   Real: %.0f | Imag: %.0f | Mag: %.2f\n", realCal, imagCal, magCal);
  Serial.printf("   Gain: %.12f\n\n", gainFactor);
}

void loop() {
  double somaZ = 0;
  long currentFreq = startFreq;
  static int scanCount = 0;

  Serial.printf("🔄 VARREDURA #%d\n", ++scanCount);

  if (gainFactor <= 0.0) {
    Serial.println("❌ Gain=0! Recalibrando...");
    calibrate();
    saveCalibration();
    delay(3000);
    return;
  }

  writeReg(0x80, 0xB0);
  delay(100);
  writeReg(0x80, 0x11); 
  delay(100);
  writeReg(0x80, 0x21); 

  int pontos = 0;
  for (int i = 0; i <= numIncr; i++) {
    if (!waitValid(3000)) {
      Serial.printf("⏰ TIMEOUT freq=%ld Hz!\n", currentFreq);
      break;
    }
    
    double real = readData(0x94);
    double imag = readData(0x96);
    double mag = sqrt(pow(real, 2) + pow(imag, 2));
    
    if (mag > 0) {
      double impedance = 1.0 / (mag * gainFactor);
      double phase = atan2(imag, real) * (180.0 / PI);
      double Z_real = impedance * cos(phase * PI / 180.0);
      double Z_imag = impedance * sin(phase * PI / 180.0);
      
      // Adicionar à janela móvel desta frequência (CIRCULAR)
      int freqIndex = i;
      int currentIdx = windowIndices[freqIndex];
      windows[freqIndex][currentIdx] = {impedance, phase, Z_real, Z_imag, mag};
      
      windowIndices[freqIndex] = (windowIndices[freqIndex] + 1) % WINDOW_SIZE;
      if (windowCounts[freqIndex] < WINDOW_SIZE) {
        windowCounts[freqIndex]++;
      }
      
      // Calcular e exibir APENAS a média móvel
      Measurement avg;
      calculateMovingAverage(freqIndex, &avg);
      
      Serial.printf("%ld,%.1f,%.2f,%.1f,%.1f,%.2f,%d\n", 
              currentFreq, avg.imp, avg.phase, avg.real, avg.imag, avg.mag,
              windowCounts[freqIndex]);
      
      somaZ += avg.imp;  // Usa média para soma total
      pontos++;
    }

    if (i < numIncr) {
      writeReg(0x80, 0x31); 
      currentFreq += freqIncr;
    } else {
      writeReg(0x80, 0xB1); 
    }
  }

  if (pontos > 0) {
    double media = somaZ / pontos;
    Serial.printf("📈 MÉDIA TOTAL MÓVEL: %.1f Ω (%d pts) | Gain: %.12f | Scan: #%d\n\n", 
                  media, pontos, gainFactor, scanCount);
  }
  
  delay(5000);
}