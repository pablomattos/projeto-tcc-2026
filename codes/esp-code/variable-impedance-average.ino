#include <Wire.h>
#include <math.h>

#define AD5933_ADDR 0x0D

// Registradores
#define REG_CONTROL_HIGH   0x80
#define REG_CONTROL_LOW    0x81
#define REG_START_FREQ     0x82
#define REG_FREQ_INC       0x85
#define REG_NUM_INC        0x88
#define REG_NUM_SETTLING   0x8A
#define REG_STATUS         0x8F
#define REG_REAL           0x94
#define REG_IMAG           0x96

// Comandos
#define CMD_INIT_START_FREQ 0x10
#define CMD_START_SWEEP     0x20
#define CMD_INCREMENT_FREQ  0x30
#define CMD_REPEAT_FREQ     0x40
#define CMD_POWER_DOWN      0xA0
#define CMD_STANDBY         0xB0

// Status
#define STATUS_VALID_DATA   0x02

// Configuração reduzida para teste (fácil de ver o gain)
const float START_FREQ = 1000.0;
const float FREQ_INC   = 1000.0;   // 1 kHz de incremento
const int   NUM_INC    = 4;        // 5 pontos total
const int   SETTLING   = 5;

// Hardware
const float R_FB  = 550.0;   // res. de TIA, só para info
const float R_CAL = 550.0;   // resistor de calibração

// Cabos ESP32
const int SDA_PIN = 21;
const int SCL_PIN = 22;
const uint32_t MCLK_HZ = 16776000UL;

// --- funções de leitura/escrita já usadas anteriormente ---

void writeRegister(uint8_t reg, uint8_t value) {
  Wire.beginTransmission(AD5933_ADDR);
  Wire.write(reg);
  Wire.write(value);
  Wire.endTransmission();
}

uint8_t readRegister(uint8_t reg) {
  Wire.beginTransmission(AD5933_ADDR);
  Wire.write(reg);
  Wire.endTransmission(false);
  Wire.requestFrom(AD5933_ADDR, (uint8_t)1);
  if (Wire.available()) return Wire.read();
  return 0;
}

void writeRegister24(uint8_t reg, uint32_t value) {
  writeRegister(reg,     (value >> 16) & 0xFF);
  writeRegister(reg + 1, (value >>  8) & 0xFF);
  writeRegister(reg + 2, value & 0xFF);
}

void writeRegister16(uint8_t reg, uint16_t value) {
  writeRegister(reg,     (value >>  8) & 0xFF);
  writeRegister(reg + 1, value & 0xFF);
}

int16_t readInt16(uint8_t reg) {
  uint8_t hi = readRegister(reg);
  uint8_t lo = readRegister(reg + 1);
  return (int16_t)((hi << 8) | lo);
}

void setControlMode(uint8_t cmd) {
  uint8_t high = readRegister(REG_CONTROL_HIGH);
  high &= 0x0F;
  high |= cmd;
  writeRegister(REG_CONTROL_HIGH, high);
}

void resetAD5933() {
  uint8_t low = readRegister(REG_CONTROL_LOW);
  low |= 0x10;
  writeRegister(REG_CONTROL_LOW, low);
  delay(10);
}

void setPGAx1() {
  uint8_t low = readRegister(REG_CONTROL_LOW);
  low &= ~0x01;
  writeRegister(REG_CONTROL_LOW, low);
}

void setOutputRange1() {
  uint8_t high = readRegister(REG_CONTROL_HIGH);
  high &= 0xF1;
  high |= (0b00 << 1);
  writeRegister(REG_CONTROL_HIGH, high);
}

uint32_t freqToCode(float freqHz) {
  return (uint32_t)((freqHz / (MCLK_HZ / 4.0)) * (1UL << 27));
}

void configureSweep(float startFreq, float incFreq, int numInc, int settling) {
  writeRegister24(REG_START_FREQ, freqToCode(startFreq));
  writeRegister24(REG_FREQ_INC, freqToCode(incFreq));
  writeRegister16(REG_NUM_INC, numInc);
  writeRegister16(REG_NUM_SETTLING, settling);
}

bool waitValidData(uint32_t timeoutMs = 1500) {
  uint32_t t0 = millis();
  while (millis() - t0 < timeoutMs) {
    if (readRegister(REG_STATUS) & STATUS_VALID_DATA) return true;
    delay(1);
  }
  return false;
}

bool startSweep() {
  setControlMode(CMD_STANDBY);
  setControlMode(CMD_INIT_START_FREQ);
  delay(10);
  setControlMode(CMD_START_SWEEP);
  return true;
}

void setup() {
  Serial.begin(115200);
  delay(1200);

  Wire.begin(SDA_PIN, SCL_PIN, 100000);

  // Configura o AD5933
  resetAD5933();
  setOutputRange1();
  setPGAx1();
  configureSweep(START_FREQ, FREQ_INC, NUM_INC, SETTLING);

  // Inicia o sweep
  if (!startSweep()) {
    Serial.println("Falha ao iniciar sweep.");
    return;
  }

  // Exibição de informação
  Serial.println("=== DEMONSTRACAO DO GAIN FACTOR ===");
  Serial.print("R_FB = "); Serial.print(R_FB, 2); Serial.println(" ohm");
  Serial.print("R_CAL = "); Serial.print(R_CAL, 2); Serial.println(" ohm");
  Serial.println("Conecte o resistor de 550 ohms para calibracao.");
  Serial.println("freq (Hz), real, imag, mag, gainFactor");

  // Medição e cálculo do ganho para cada ponto
  for (int i = 0; i < NUM_INC + 1; i++) {
    long sumR = 0;
    long sumI = 0;

    // 4 médias
    for (int k = 0; k < 4; k++) {
      if (!waitValidData()) {
        Serial.println("Erro de leitura de dados.");
        return;
      }

      int16_t r = readInt16(REG_REAL);
      int16_t im = readInt16(REG_IMAG);

      sumR += r;
      sumI += im;

      if (k < 3) setControlMode(CMD_REPEAT_FREQ);
    }

    int16_t rAvg = (int16_t)(sumR / 4);
    int16_t iAvg = (int16_t)(sumI / 4);

    float mag = sqrtf((float)rAvg * rAvg + (float)iAvg * iAvg);
    float gf = (mag > 0.0f) ? 1.0f / (R_CAL * mag) : NAN;

    float f = START_FREQ + i * FREQ_INC;

    // Imprime ponto a ponto
    Serial.print(f, 1);  Serial.print(", ");
    Serial.print(rAvg);  Serial.print(", ");
    Serial.print(iAvg);  Serial.print(", ");
    Serial.print(mag, 3);  Serial.print(", ");
    Serial.println(gf, 12);

    // Avança para a próxima frequência, se não for o último ponto
    if (i < NUM_INC) setControlMode(CMD_INCREMENT_FREQ);
  }

  // Desliga
  setControlMode(CMD_POWER_DOWN);
  Serial.println("Fim.");
}

void loop() {
}