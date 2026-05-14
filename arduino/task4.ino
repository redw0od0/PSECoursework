#include <math.h>

// Configuration
const int B = 4275000;        // B value of the thermistor
const int R0 = 100000;        // R0 = 100k
const int pinTempSensor = A0; // Grove - Temperature Sensor connect to A0

const unsigned int sampling_freq_hz = 2;
const unsigned int sampling_duration_sec = 180;

/* size_t (unsigned long or unsigned long long depending on the implementation and OS)
   can be used to ensure SAMPLE_COUNT >= 0
*/

// Capitalisation helps me to differentiate these global variables and constants from local variables
// that may have similar names
const size_t SAMPLE_COUNT = sampling_freq_hz * sampling_duration_sec;


float temperature_read()
{
  int a = analogRead(pinTempSensor);
  float R = 1023.0 / a - 1.0;
  R = R0 * R;
  float temperature = 1.0 / (log(R / R0) / B + 1 / 298.15) - 273.15; // convert to temperature via datasheet
  return temperature;
}

void record_temperatures()
{
  unsigned long delay_ms = 1000 / sampling_freq_hz;

  Serial.println("Time,Temperature");

  for (size_t i = 0; i < SAMPLE_COUNT; i++)
  {
    float t = i / (float)sampling_freq_hz;
    float temp = temperature_read();

    Serial.print(t);
    Serial.print(",");
    Serial.println(temp);
    // Saves memory by writing tempertatues directly to serial without storing in a static buffer
    delay(delay_ms);
  }
}

void setup()
{
    Serial.begin(9600);

    delay(2000);

    record_temperatures();
}


void loop(){
  // Do nothing
}