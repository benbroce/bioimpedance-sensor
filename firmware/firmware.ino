// #include <Arduino.h>
#include <stdint.h>

// Constants

// body parameters
// #define SUBJECT_MASS_KG 97.5
// #define SUBJECT_HEIGHT_CM 289.6
// sampling and comms
#define BAUD_RATE 9600
#define NUM_SAMPLES_PER_CAPTURE 10
#define PERIOD_BETWEEN_SAMPLES_MS 100
#define PERIOD_BETWEEN_CAPTURES_MS 1000
// voltage to impedance calibration constants
#define ADC_REF_VOLTAGE 5.0
#define ADC_MAX_VAL 1023
#define VOLTAGE_TO_IMPEDANCE_SQUARE_GAIN 879.0
#define VOLTAGE_TO_IMPEDANCE_LINEAR_GAIN 1326.0
#define VOLTAGE_TO_IMPEDANCE_OFFSET 639.0

// Pin Defs

#define SENSOR_PIN A0
#define CAPTURE_BTN_PIN 3

// Globals
float SUBJECT_MASS_KG;
float SUBJECT_HEIGHT_CM;

// Functions

float samples_to_capture_avg(int (&samples)[NUM_SAMPLES_PER_CAPTURE]) {
  float average = 0;
  for (int i = 0; i < NUM_SAMPLES_PER_CAPTURE; ++i) {
    average = average + (((float)samples[i] - average) / ((float)i + 1.0));
  }
  return average;
}

float adc_to_impedance_ohms(float adc_val) {
  float in_voltage = adc_val * (ADC_REF_VOLTAGE / ADC_MAX_VAL);
  return VOLTAGE_TO_IMPEDANCE_OFFSET +
         (VOLTAGE_TO_IMPEDANCE_LINEAR_GAIN * in_voltage) +
         (VOLTAGE_TO_IMPEDANCE_SQUARE_GAIN * in_voltage * in_voltage);
}

// calculate Total Body Water (TBW) in kg from impedance,
// mass (within 0.1kg), and height (within 0.5cm)
// reference : Kushner
// (https://www.sciencedirect.com/science/article/abs/pii/S0002916523399581?via%3Dihub)
// (https://www.bodystat.com/content/114%20Validation%20TBW%20vs%20Deuterium%20new%20Equation%204-7%20year%20olds%20Weijs%202011%20Bodystat1500MDD.pdf)
float calc_TBW_kg(float impedance_ohms, float mass_kg, float height_cm) {
  float TBW_kg = (0.59 * ((height_cm * height_cm) / impedance_ohms)) +
                 (0.065 * mass_kg) + 0.04;
  return TBW_kg;
}

// calculate Fat Free Mass (FFM) in kg from TBW
// reference: Khaled
// (https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=508703)
float calc_FFM_kg(float TBW_kg) { return (TBW_kg / 0.732); }

// calculate Fat Mass in kg from mass and FFM
// reference: Khaled
// (https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=508703)
float calc_FM_kg(float mass_kg, float FFM_kg) { return (mass_kg - FFM_kg); }

void setPinModes() {
  pinMode(SENSOR_PIN, INPUT);
  pinMode(CAPTURE_BTN_PIN, INPUT_PULLUP);
}

void setup() {
  setPinModes();
  Serial.begin(BAUD_RATE);
  Serial.println("\n\nBioimpedance Sensor\nProgram the Device with Your Height "
                 "and Weight, then Press the Button\n");
  Serial.print("Subject Mass: ");
  while (Serial.available() == 0)
    ;
  SUBJECT_MASS_KG = Serial.parseFloat();
  Serial.print("Subject Height: ");
  while (Serial.available() == 0)
    ;
  SUBJECT_HEIGHT_CM = Serial.parseFloat();
  Serial.println();
}

void loop() {
  int samples[NUM_SAMPLES_PER_CAPTURE];
  // on capture button press, begin capture
  if (digitalRead(CAPTURE_BTN_PIN) == LOW) {
    // capture several samples at the specified rate
    for (int sample_i = 0; sample_i < NUM_SAMPLES_PER_CAPTURE; ++sample_i) {
      samples[sample_i] = analogRead(SENSOR_PIN);
      delay(PERIOD_BETWEEN_SAMPLES_MS);
    }
    // average captured samples' ADC values
    float adc_val = samples_to_capture_avg(samples);
    // convert average ADC value to impedance
    float impedance = adc_to_impedance_ohms(adc_val);
    // convert impedance to BIA values
    float total_body_water =
        calc_TBW_kg(impedance, SUBJECT_MASS_KG, SUBJECT_HEIGHT_CM);
    float lean_mass = calc_FFM_kg(total_body_water);
    float fatty_mass = calc_FM_kg(SUBJECT_MASS_KG, lean_mass);
    // display result
    Serial.print("\nImpedance (Ohms): ");
    Serial.print(impedance);
    Serial.print("\nTotal Body Water (kg): ");
    Serial.print(total_body_water);
    Serial.print("\nLean Mass (kg): ");
    Serial.print(lean_mass);
    Serial.print("\nFatty Mass (kg): ");
    Serial.print(fatty_mass);
    Serial.print("\n--------------------\n\n");
    delay(PERIOD_BETWEEN_CAPTURES_MS);
  }
}