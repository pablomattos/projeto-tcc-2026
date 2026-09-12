#include <Wire.h>
#include <math.h>

#define AD5933_ADDR 0x0D

// ======================================================
// CLOCK DO AD5933
// ======================================================
const double CLK_FREQ = 16776000.0; // 

// ======================================================
// CONFIGURAÇÕES DA VARREDURA
// ======================================================
const long startFreq = 1000;   // Frequência inicial 
const long freqIncr  = 333.333;    // Incremento 
const int TOTAL_POINTS = 300;    // 
const int numIncr = TOTAL_POINTS - 1; // 

// Configuração padrão de controle: Range 1 (2Vpp) e PGA = x1 (Bit D8 = 1) -> 0x01
// Combinado com o modo inicial que você deseja (Standby = 0xB0) -> 0xB1
const byte CTRL_BASE = 0x01; 

// ======================================================
// RESISTOR DE CALIBRAÇÃO
// ======================================================
const double R_CAL = 1460.0;

// ======================================================
// SETTLING TIME
// ======================================================
const int settlingCycles = 100; 
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
  if (err != 0) { // [cite: 7]
    Serial.printf("⚠️ Erro I2C reg 0x%02X -> %d\n", reg, err); // [cite: 7]
  }
}

// ======================================================
// LEITURA DE DADOS 16 BITS
// ======================================================
int readData(byte reg) {
  Wire.beginTransmission(AD5933_ADDR); 
  Wire.write(reg); 
  if (Wire.endTransmission(false) != 0) { 
    return 0; 
  }
  Wire.requestFrom(AD5933_ADDR, 2); 
  if (Wire.available() < 2) { 
    return 0; 
  }
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
  if (Wire.endTransmission(false) != 0) { 
    return 0; 
  }
  Wire.requestFrom(AD5933_ADDR, 1); 
  if (Wire.available()) { 
    return Wire.read(); 
  }
  return 0; 
}

// ======================================================
// AGUARDA DADOS DISPONÍVEIS
// ======================================================
bool aguardarDados() {
  unsigned long timeout = millis() + 2000; 
  while (millis() < timeout) { 
    byte status = readStatus(); 
    // Bit D1 = Data valid
    if (status & 0x02) { // 
      return true; // 
    }
    delay(1); 
    yield(); 
  }
  return false; 
}

// ======================================================
// CONFIGURA FREQUÊNCIA
// ======================================================
void setFrequency(byte reg, long freqHz) {
  long freqCode = (long)((freqHz / (CLK_FREQ / 4.0)) * pow(2, 27)); // 
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
// RESET E STANDBY DO AD5933
// ======================================================
void resetAD5933() {
  // Ativa bit de Reset mantendo a base de configuração (CTRL_BASE)
  writeReg(0x80, CTRL_BASE | 0x10); 
  delay(10);
  // Coloca em modo Standby (0xB0) mantendo a base
  writeReg(0x80, CTRL_BASE | 0xB0); 
  delay(100);
}

// ======================================================
// INICIA SWEEP
// ======================================================
void iniciarSweep() {
  // Coloca em modo inicializar com a frequência inicial (0x10)
  writeReg(0x80, CTRL_BASE | 0x10);
  delay(100);
  // Inicia a varredura de frequência (0x20)
  writeReg(0x80, CTRL_BASE | 0x20);
  delay(100);
}

// ======================================================
// INCREMENTA FREQUÊNCIA
// ======================================================
bool incrementarFrequencia() {
  // Comando para incrementar frequência (0x30) preservando a base de configuração
  writeReg(0x80, CTRL_BASE | 0x30);

  unsigned long timeout = millis() + 1000; // 
  while (millis() < timeout) { // 
    byte status = readStatus();
    // CORREÇÃO: O bit de fim de incremento ou varredura em andamento varia. 
    // Para garantir o próximo ponto, verificamos se o bit de dado válido (0x02) limpou e reativou,
    // ou simplesmente retornamos true pois o comando de incremento é imediato no clock interno.
    // A folha de dados recomenda checar se o Sweep não terminou (Bit D2 - 0x04)
    if ((status & 0x04) == 0) { 
      return true;
    }
    delay(1); 
    yield(); 
  }
  return false; 
}

// ======================================================
// LEITURA COM MÉDIA
// ======================================================
bool lerMedia(double &realMedio, double &imagMedio) {
  const int samples = 5; 
  double somaReal = 0; // 
  double somaImag = 0; // 

  for (int i = 0; i < samples; i++) {
    if (!aguardarDados()) { // 
      return false; // 
    }
    somaReal += (double)readData(0x94); 
    somaImag += (double)readData(0x96); 
    delay(2); 
  }
  realMedio = somaReal / samples; 
  imagMedio = somaImag / samples; 
  return true; 
}

// ======================================================
// CALIBRAÇÃO COMPLETA
// ======================================================
void executarCalibracaoCompleta() {
  Serial.println("\n🎯 INICIANDO CALIBRAÇÃO"); 
  resetAD5933(); 
  configurarSettlingTime(settlingCycles); 
  iniciarSweep(); 

  for (int i = 0; i < TOTAL_POINTS; i++) {
    double real; 
    double imag; 
    if (!lerMedia(real, imag)) { 
      Serial.printf("❌ Timeout calibração ponto %d\n", i); 
      sistemaCalibrado = false; 
      return; 
    }

    double magnitude = sqrt((real * real) + (imag * imag)); 
    gainFactors[i] = (1.0 / R_CAL) / magnitude; 
    systemPhases[i] = atan2(imag, real) * (180.0 / PI); 

    long freqAtual = startFreq + (i * freqIncr); 
    Serial.printf("CAL %02d | %ld Hz | Mag: %.1f\n", i, freqAtual, magnitude);

    if (i < (TOTAL_POINTS - 1)) { 
      if (!incrementarFrequencia()) { 
        Serial.println("❌ Erro incremento frequência"); 
        sistemaCalibrado = false; 
        return; 
      }
    }
  }
  sistemaCalibrado = true; 
  Serial.println("\n✅ CALIBRAÇÃO CONCLUÍDA"); 
}

// ======================================================
// SETUP
// ======================================================
void setup() {
  Serial.begin(115200); 
  delay(3000); 

  Wire.begin(21, 22); 
  Wire.setClock(100000); // 

  // Configura os parâmetros básicos de frequência nos registradores
  setFrequency(0x82, startFreq); // 
  setFrequency(0x85, freqIncr); // 
  writeReg(0x88, (numIncr >> 8) & 0xFF); // 
  writeReg(0x89, numIncr & 0xFF); // 

  configurarSettlingTime(settlingCycles); // 

  // Inicializa o chip colocando em Standby com a configuração correta de Range
  resetAD5933();

  Serial.println("================================="); // 
  Serial.println("🚀 AD5933 + ESP32 CORRIGIDO");
  Serial.println("================================="); // 
  Serial.printf("Freq Inicial : %ld Hz\n", startFreq); // 
  Serial.printf("Incremento   : %ld Hz\n", freqIncr); 
  Serial.printf("Pontos       : %d\n", TOTAL_POINTS); 
  Serial.println("\nIniciando..."); 
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
  iniciarSweep(); 
  Serial.println("\nFreq(Hz),Impedancia(Ohm),Fase(°)"); 

  for (int i = 0; i < TOTAL_POINTS; i++) {
    double real; 
    double imag; 

    if (!lerMedia(real, imag)) { 
      Serial.printf("❌ Timeout medição ponto %d\n", i); 
      break; 
    }

    double magnitude = sqrt((real * real) + (imag * imag)); 
    double impedance = 1.0 / (gainFactors[i] * magnitude); 
    
    double rawPhase = atan2(imag, real) * (180.0 / PI); 
    double correctedPhase = rawPhase - systemPhases[i]; 

    while (correctedPhase > 180)  correctedPhase -= 360; 
    while (correctedPhase < -180) correctedPhase += 360; 

    long freqAtual = startFreq + (i * freqIncr); 
    Serial.printf("%ld,%.2f,%.2f\n", freqAtual, impedance, correctedPhase); 

    if (i < (TOTAL_POINTS - 1)) { 
      if (!incrementarFrequencia()) { 
        Serial.println("❌ Erro incremento frequência"); 
        break; 
      }
    }
  }

  Serial.println("\n========================"); 
  Serial.println("Nova varredura em 10s"); 
  Serial.println("========================"); 
  delay(10000); 
}