#include <Wire.h>
#include <math.h>

#define AD5933_ADDR 0x0D

// ======================================================
// CLOCK DO AD5933
// ======================================================
const double CLK_FREQ = 16776000.0;

// ======================================================
// CONFIGURAÇÕES DA VARREDURA
// ======================================================
const long startFreq = 10000;   // Frequência inicial
const long freqIncr  = 1000;    // Incremento
const int TOTAL_POINTS = 91;    // 10kHz a 100kHz
const int numIncr = TOTAL_POINTS - 1;

// ======================================================
// RESISTOR DE CALIBRAÇÃO
// ======================================================
const double R_CAL = 1460.0;

// ======================================================
// SETTLING TIME (Aumentado para maior estabilidade)
// ======================================================
const int settlingCycles = 150; 

// ======================================================
// ARRAYS DE CALIBRAÇÃO
// ======================================================
double gainFactors[TOTAL_POINTS];
double systemPhases[TOTAL_POINTS];
bool sistemaCalibrado = false;

// ======================================================
// ESCRITA DE REGISTRADOR
// ======================================================
void writeReg(byte reg, byte val) {
  Wire.beginTransmission(AD5933_ADDR);
  Wire.write(reg);
  Wire.write(val);
  byte err = Wire.endTransmission();
  if (err != 0) {
    Serial.printf("⚠️ Erro I2C reg 0x%02X -> %d\n", reg, err);
  }
}

// ======================================================
// LEITURA DE DADOS 16 BITS
// ======================================================
int readData(byte reg) {
  Wire.beginTransmission(AD5933_ADDR);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return 0;
  Wire.requestFrom(AD5933_ADDR, 2);
  if (Wire.available() < 2) return 0;
  int msb = Wire.read();
  int lsb = Wire.read();
  return (int16_t)((msb << 8) | lsb);
}

// ======================================================
// LEITURA DO STATUS
// ======================================================
byte readStatus() {
  Wire.beginTransmission(AD5933_ADDR);
  Wire.write(0x8F);
  if (Wire.endTransmission(false) != 0) return 0;
  Wire.requestFrom(AD5933_ADDR, 1);
  if (Wire.available()) return Wire.read();
  return 0;
}

// ======================================================
// AGUARDA DADOS DISPONÍVEIS
// ======================================================
bool aguardarDados() {
  unsigned long timeout = millis() + 2000;
  while (millis() < timeout) {
    byte status = readStatus();
    if (status & 0x02) return true; // Bit D1 = Data valid
    delay(1);
    yield();
  }
  return false;
}

// ======================================================
// CONFIGURA FREQUÊNCIA
// ======================================================
void setFrequency(byte reg, long freqHz) {
  long freqCode = (long)((freqHz / (CLK_FREQ / 4.0)) * pow(2, 27));
  writeReg(reg,     (freqCode >> 16) & 0xFF);
  writeReg(reg + 1, (freqCode >> 8)  & 0xFF);
  writeReg(reg + 2,  freqCode        & 0xFF);
}

// ======================================================
// CONFIGURA SETTLING TIME
// ======================================================
void configurarSettlingTime(int cycles) {
  writeReg(0x8A, (cycles >> 8) & 0x01);
  writeReg(0x8B, cycles & 0xFF);
}

// ======================================================
// RESET DO AD5933
// ======================================================
void resetAD5933() {
  writeReg(0x80, 0x10); // Control Register para Standby
  delay(10);
  writeReg(0x80, 0xB0); // Ativa clock externo (se aplicável) ou reinicia
  delay(100);
}

// ======================================================
// INICIA SWEEP
// ======================================================
void iniciarSweep() {
  writeReg(0x80, 0x11); // Inicializa com a Frequência Inicial (Gera a onda mas não mede)
  delay(100);
  writeReg(0x80, 0x21); // Inicia a varredura de frequência real
  delay(100);
}

// ======================================================
// INCREMENTA FREQUÊNCIA
// ======================================================
bool incrementarFrequencia() {
  writeReg(0x80, 0x31); // Comando de incremento
  return true;
}

// ======================================================
// LEITURA COM MÉDIA OTIMIZADA
// ======================================================
bool lerMedia(double &realMedio, double &imagMedio) {
  const int samples = 15; // Aumentado para reduzir a dispersão no Nyquist
  double somaReal = 0;
  double somaImag = 0;

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

// ======================================================
// CALIBRAÇÃO COMPLETA
// ======================================================
void executarCalibracaoCompleta() {
  Serial.println("\n🎯 INICIANDO CALIBRAÇÃO MULTI-PONTO...");
  resetAD5933();
  configurarSettlingTime(settlingCycles);
  iniciarSweep();

  for (int i = 0; i < TOTAL_POINTS; i++) {
    double real, imag;
    if (!lerMedia(real, imag)) {
      Serial.printf("❌ Timeout calibração ponto %d\n", i);
      sistemaCalibrado = false;
      return;
    }

    double magnitude = sqrt((real * real) + (imag * imag));
    gainFactors[i] = (1.0 / R_CAL) / magnitude;
    systemPhases[i] = atan2(imag, real) * (180.0 / PI);

    if (i < (TOTAL_POINTS - 1)) {
      incrementarFrequencia();
    }
  }
  sistemaCalibrado = true;
  Serial.println("\n✅ CALIBRAÇÃO CONCLUÍDA COM SUCESSO");
}

// ======================================================
// SETUP
// ======================================================
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

  Serial.println("=================================");
  Serial.println("🚀 AD5933 + ESP32 OPTIMIZED");
  Serial.println("=================================");
}

// ======================================================
// LOOP PRINCIPAL
// ======================================================
void loop() {
  if (!sistemaCalibrado) {
    executarCalibracaoCompleta();
    delay(1000);
    return;
  }

  resetAD5933();
  configurarSettlingTime(settlingCycles);
  iniciarSweep();

  Serial.println("\nFreq(Hz),Impedancia(Ohm),Fase(°)");

  for (int i = 0; i < TOTAL_POINTS; i++) {
    double real, imag;
    if (!lerMedia(real, imag)) {
      Serial.printf("❌ Timeout medição ponto %d\n", i);
      break;
    }

    double magnitude = sqrt((real * real) + (imag * imag));
    double impedance = 1.0 / (gainFactors[i] * magnitude);
    
    // MATHEMATICAL CORRECTION FOR AD5933 PHASE
    double rawPhase = atan2(imag, real) * (180.0 / PI);
    double correctedPhase = systemPhases[i] - rawPhase; 

    // NORMALIZA FASE ENTRE -180 E 180
    while (correctedPhase > 180)  correctedPhase -= 360;
    while (correctedPhase < -180) correctedPhase += 360;

    long freqAtual = startFreq + (i * freqIncr);
    Serial.printf("%ld,%.2f,%.2f\n", freqAtual, impedance, correctedPhase);

    if (i < (TOTAL_POINTS - 1)) {
      incrementarFrequencia();
    }
  }

  Serial.println("\n========================");
  Serial.println("Nova varredura em 10s");
  Serial.println("========================");
  delay(10000);
}