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

const int TOTAL_POINTS = 91;
const int numIncr = TOTAL_POINTS - 1;

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

  if (err != 0) {

    Serial.printf(
      "⚠️ Erro I2C reg 0x%02X -> %d\n",
      reg,
      err
    );
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

    byte status = readStatus(); //verifica dados válidos

    // Bit D1 = Data valid
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
//calcula fredcode e distribui valores nos espaços de memória
void setFrequency(byte reg, long freqHz) {

  long freqCode =
    (long)((freqHz / (CLK_FREQ / 4.0)) * pow(2, 27));

  writeReg(reg,     (freqCode >> 16) & 0xFF); //Realiza um deslocamento de bits para a direita em 16 posições. Isso isola os 8 bits mais significativos
  writeReg(reg + 1, (freqCode >> 8)  & 0xFF); //Desloca o número em 8 posições para a direita, isolando os 8 bits do "meio
  writeReg(reg + 2,  freqCode        & 0xFF); //pega os 8bits menos significativos
}

// ======================================================
// CONFIGURA SETTLING TIME
// ======================================================

void configurarSettlingTime(int cycles) {

  writeReg(0x8A, (cycles >> 8) & 0x01); //armazena os bits mais significativos do número de ciclos, pega o valor acima de 8bits, considera 9ºbit no registrador
  writeReg(0x8B, cycles & 0xFF); //armazena os 8 bits menos significativos do valor, isola 8bits finais
}

// ======================================================
// RESET DO AD5933
// ======================================================

void resetAD5933() {

  writeReg(0x80, 0x10); //ativa o bit de reset do AD5933

  delay(10);

  writeReg(0x80, 0xB0); //configura o chip para o modo Standby

  delay(100);
}

// ======================================================
// INICIA SWEEP
// ======================================================

void iniciarSweep() {

  writeReg(0x80, 0x10); //ativa o bit de reset do AD5933

  delay(10);

  // Inicializa frequência
  writeReg(0x80, 0x11);

  delay(100);

  // Inicia a Varredura de Frequência
  writeReg(0x80, 0x21);

  delay(100);
}

// ======================================================
// INCREMENTA FREQUÊNCIA
// ======================================================

bool incrementarFrequencia() {

  writeReg(0x80, 0x31); // instrui o chip a calcular a próxima frequência da varredura 

  unsigned long timeout = millis() + 1000;

  while (millis() < timeout) {
    //veirificacao de status
    if (readStatus() & 0x02) {//acessa registrador 0x8F do chip, verifica bit de freq incrementada
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

void executarCalibracaoCompleta() {

  Serial.println("\n🎯 INICIANDO CALIBRAÇÃO");

  resetAD5933();

  configurarSettlingTime(settlingCycles);

  iniciarSweep();

  for (int i = 0; i < TOTAL_POINTS; i++) {

    double real;
    double imag;

    if (!lerMedia(real, imag)) {

      Serial.printf(
        "❌ Timeout calibração ponto %d\n",
        i
      );

      sistemaCalibrado = false;

      return;
    }

    double magnitude =
      sqrt((real * real) + (imag * imag));

    gainFactors[i] =
      (1.0 / R_CAL) / magnitude;

    systemPhases[i] =
      atan2(imag, real) * (180.0 / PI);

    long freqAtual =
      startFreq + (i * freqIncr);

    Serial.printf(
      "CAL %02d | %ld Hz\n",
      i,
      freqAtual
    );

    if (i < (TOTAL_POINTS - 1)) {

      if (!incrementarFrequencia()) {

        Serial.println(
          "❌ Erro incremento frequência"
        );

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

  // SDA = GPIO21
  // SCL = GPIO22

  Wire.begin(21, 22);

  // Clock I2C mais estável

  Wire.setClock(100000);

  // ====================================================
  // CONFIGURAÇÕES DO AD5933
  // ====================================================

  setFrequency(0x82, startFreq);

  setFrequency(0x85, freqIncr);
 //define quantidade de pontos para medição
  writeReg(0x88, (numIncr >> 8) & 0xFF);// isola o byte mais significativo (MSB) e grava no reg
  writeReg(0x89, numIncr & 0xFF);// isola o byte menos significativo (LSB) e grava no reg

  configurarSettlingTime(settlingCycles);

  Serial.println("=================================");
  Serial.println("🚀 AD5933 + ESP32");
  Serial.println("=================================");

  Serial.printf(
    "Freq Inicial : %ld Hz\n",
    startFreq
  );

  Serial.printf(
    "Incremento   : %ld Hz\n",
    freqIncr
  );

  Serial.printf(
    "Pontos       : %d\n",
    TOTAL_POINTS
  );

  Serial.println("\nIniciando...");
}

// ======================================================
// LOOP PRINCIPAL
// ======================================================

void loop() {

  // ====================================================
  // CALIBRAÇÃO
  // ====================================================

  if (!sistemaCalibrado) {

    executarCalibracaoCompleta();

    delay(1000);

    return;
  }

  // ====================================================
  // NOVA VARREDURA
  // ====================================================

  resetAD5933();

  iniciarSweep();

  Serial.println(
    "\nFreq(Hz),Impedancia(Ohm),Fase(°)"
  );

  for (int i = 0; i < TOTAL_POINTS; i++) {

    double real;
    double imag;

    if (!lerMedia(real, imag)) {

      Serial.printf(
        "❌ Timeout medição ponto %d\n",
        i
      );

      break;
    }

    // ==================================================
    // MAGNITUDE
    // ==================================================

    double magnitude =
      sqrt((real * real) + (imag * imag));

    // ==================================================
    // IMPEDÂNCIA
    // ==================================================

    double impedance =
      1.0 / (gainFactors[i] * magnitude);

    // ==================================================
    // FASE
    // ==================================================

    double rawPhase =
      atan2(imag, real) * (180.0 / PI);

    double correctedPhase =
      rawPhase - systemPhases[i];

    // ==================================================
    // NORMALIZA FASE
    // ==================================================

    while (correctedPhase > 180) {
      correctedPhase -= 360;
    }

    while (correctedPhase < -180) {
      correctedPhase += 360;
    }

    // ==================================================
    // FREQUÊNCIA ATUAL
    // ==================================================

    long freqAtual =
      startFreq + (i * freqIncr);

    // ==================================================
    // SERIAL CSV
    // ==================================================

    Serial.printf(
      "%ld,%.2f,%.2f\n",
      freqAtual,
      impedance,
      correctedPhase
    );

    // ==================================================
    // PRÓXIMA FREQUÊNCIA
    // ==================================================

    if (i < (TOTAL_POINTS - 1)) {

      if (!incrementarFrequencia()) {

        Serial.println(
          "❌ Erro incremento frequência"
        );

        break;
      }
    }
  }

  Serial.println("\n========================");
  Serial.println("Nova varredura em 10s");
  Serial.println("========================");

  delay(10000);
}