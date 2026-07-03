#include <Wire.h>
#include <math.h>

#define AD5933_ADDR 0x0D

// ======================================================
// CLOCK DO AD5933
// ======================================================
const double CLK_FREQ = 16776000.0;

// ======================================================
// CONFIGURAÇÕES DA VARREDURA (1 kHz a 100 kHz)
// ======================================================
const long startFreq = 1000;    // Frequência inicial (1 kHz)
const long freqIncr  = 1000;    // Incremento (1 kHz)
const int TOTAL_POINTS = 100;   // Varredura até 100 kHz
const int numIncr = TOTAL_POINTS - 1;

// ======================================================
// RESISTOR DE CALIBRAÇÃO
// ======================================================
const double R_CAL = 2160.0;

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

  if (err != 0) {
    Serial.printf("⚠️ Erro I2C reg 0x%02X -> %d\n", reg, err);
  }
}

// ======================================================
// CONFIGURA FONTE DE CLOCK (Garante Clock Interno)
// ======================================================
void configurarClockInterno() {
  // O registrador 0x81 controla o clock. 
  // Bit D3 = 0 seleciona o clock interno.
  // Enviamos 0x00 para garantir que o bit D3 (e os outros) fiquem em zero.
  writeReg(0x81, 0x00); 
  Serial.println("🔒 Clock do sistema configurado explicitamente para INTERNO.");
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
    if (status & 0x02) {
      return true;
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
// RESET DO AD5933 (Configura Standby na Faixa 4 - 200mVpp)
// ======================================================
void resetAD5933() {
  writeReg(0x80, 0x16); // Ativa o bit de reset mantendo Faixa 4 (200mVpp, PGA=1x)
  delay(10);
  writeReg(0x80, 0xB6); // Coloca o chip em modo Standby na Faixa 4
  delay(100);
}

// ======================================================
// INICIA SWEEP (Preservando Faixa 4 - 200mVpp)
// ======================================================
void iniciarSweep() {
  writeReg(0x80, 0x16); // Executa o reset mantendo Faixa 4
  delay(10);
  writeReg(0x80, 0x16); // Inicializa com frequência inicial na Faixa 4
  delay(100);
  writeReg(0x80, 0x26); // Inicia a Varredura de Frequência na Faixa 4
  delay(100);
}

// ======================================================
// INCREMENTA FREQUÊNCIA
// ======================================================
bool incrementarFrequencia() {
  writeReg(0x80, 0x36); // Próxima frequência mantendo os bits de controle da Faixa 4

  unsigned long timeout = millis() + 1000;
  while (millis() < timeout) {
    if (readStatus() & 0x02) {
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
  double somaReal = 0;
  double somaImag = 0;

  for (int i = 0; i < samples; i++) {
    if (!aguardarDados()) {
      return false;
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
void ejecutarCalibracaoCompleta() {
  Serial.println("\n🎯 INICIANDO CALIBRAÇÃO (Faixa 4 - 200mVpp)");
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
    Serial.printf("CAL %02d | %ld Hz\n", i, freqAtual);

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

  // SDA = GPIO21, SCL = GPIO22
  Wire.begin(21, 22);
  Wire.setClock(100000);

  configurarClockInterno();

  setFrequency(0x82, startFreq);
  setFrequency(0x85, freqIncr);
  
  writeReg(0x88, (numIncr >> 8) & 0xFF);
  writeReg(0x89, numIncr & 0xFF);

  configurarSettlingTime(settlingCycles);

  writeReg(0x80, 0xB6); 

  Serial.println("=================================");
  Serial.println("🚀 AD5933 + ESP32 - Processamento Vetorial");
  Serial.println("=================================");
  Serial.printf("Freq Inicial : %ld Hz\n", startFreq);
  Serial.printf("Incremento   : %ld Hz\n", freqIncr);
  Serial.printf("Pontos       : %d\n", TOTAL_POINTS);
  Serial.println("\nIniciando...");
}

// ======================================================
// LOOP PRINCIPAL
// ======================================================
void loop() {
  if (!sistemaCalibrado) {
    ejecutarCalibracaoCompleta();
    delay(1000);
    return;
  }

  writeReg(0x80, 0xB6); 
  delay(10);
  iniciarSweep();

  Serial.println("\nFreq(Hz),Impedancia(Ohm),Fase(°)");

  for (int i = 0; i < TOTAL_POINTS; i++) {
    double real;
    double imag;

    if (!lerMedia(real, imag)) {
      Serial.printf("❌ Timeout medição ponto %d\n", i);
      break;
    }

    // CÁLCULO DA MAGNITUDE E IMPEDÂNCIA
    double magnitude = sqrt((real * real) + (imag * imag));
    double impedance = 1.0 / (gainFactors[i] * magnitude);

    // ======================================================
    // COMPENSAÇÃO MATEMÁTICA VIA ROTAÇÃO DE FASE COMPLEXA
    // ======================================================
    // Converte a fase de erro do sistema (armazenada na calibração) para radianos
    double sysPhaseRad = systemPhases[i] * (PI / 180.0);
    
    // Matriz de rotação complexa: rotaciona os eixos Real e Imaginário brutos 
    // para remover o atraso de propagação analógico e digital nativo do chip
    double realCorrigido = (real * cos(sysPhaseRad)) + (imag * sin(sysPhaseRad));
    double imagCorrigido = (imag * cos(sysPhaseRad)) - (real * sin(sysPhaseRad));

    // O sinal negativo corrige a inversão de polaridade introduzida pelo canal TIA
    double correctedPhase = atan2(imagCorrigido, realCorrigido) * (180.0 / PI);

    // Normalização estrita dentro do círculo trigonométrico (-180° a +180°)
    while (correctedPhase > 180)  correctedPhase -= 360;
    while (correctedPhase < -180) correctedPhase += 360;

    long freqAtual = startFreq + (i * freqIncr);

    // SAÍDA SERIAL DIRETA
    Serial.printf("%ld,%.2f,%.2f\n", freqAtual, impedance, correctedPhase);

    // INCREMENTO DE PASSO
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