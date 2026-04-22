#include <math.h>
// Configuration
const int B = 4275000;        // B value of the thermistor
const int R0 = 100000;        // R0 = 100k
const int pinTempSensor = A0; // Grove - Temperature Sensor connect to A0

/*
An enum can be used to represent system power states
(IDLE, ACTIVE, POWER_DOWN). I Believe this can help maintain type safety.

I believe on an arduino, enums are compiled into integer constants so this
should not introduce any memory overhead

*/

typedef enum{
  PWR_IDLE = 0,
  PWR_ACTIVE = 1,
  PWR_DOWN = 2
} PwrState;



#define MAX_SAMPLES 300
float temperature_data[MAX_SAMPLES];
float dft_magnitude[MAX_SAMPLES];
float dft_frequency[MAX_SAMPLES];

// Read temperature value
float temperature_read()
{
  int a = analogRead(pinTempSensor);
  float R = 1023.0 / a - 1.0;
  R = R0 * R;
  float temperature = 1.0 / (log(R / R0) / B + 1 / 298.15) - 273.15; // convert to temperature via datasheet
  return temperature;
}

void setup()
{
  Serial.begin(9600);
}

void collect_temperature_data(float *arr, int sample_count, int sample_interval_ms)
{
  for (int i = 0; i < sample_count; i++)
  {
    arr[i] = temperature_read(); // Write value to array
    delay(sample_interval_ms);   // Wait for set interval before taking the next sample
  }
}

// Finds of the average of the difference between consecutive values
float calculate_variation(float *data, size_t n)
{
  float total = 0;
  for (int i = 1; i < n; i++)
  {
    float diff = fabsf(data[i] - data[i - 1]);
    total += diff;
  }
  return total / (n - 1);
}

void apply_dft(float *data, float *mag_out, float *freq_out, int sample_count, float fs)
{
  // size_t could be used for sample_count but it may occupy more memory
  for (int k = 0; k < sample_count; k++)
  {

    float re = 0, im = 0; // Real - Imaginary separation for dft

    for (int n = 0; n < sample_count; n++)
    {
      // Compare each frequency with each sample O(N^2)
      float angle = M_PI * 2 * k * n / sample_count;
      re += data[n] * cos(angle);
      im -= data[n] * sin(angle);
    }
    // Recombine real and imaginary values through magnitude calculation
    mag_out[k] = sqrt(re * re + im * im);
    freq_out[k] = (k * fs) / sample_count;
  }
}

PwrState decide_power_mode(float f){
  if (f > 0.5) return PWR_ACTIVE;
  if (f > 0.1) return PWR_IDLE;
  return PWR_DOWN;
}

float adjust_sample_rate(float dominant_freq){
  float f = 2.0 * dominant_freq; // Nyquist theorem, minimum safe frequency// ===================== ADAPTIVE SAMPLING =====================
  
  // Clamp to bounds
  if (f < 0.5) return 0.5;
  if (f > 4.0) return 4.0;

  return f;
}

float get_dominant_frequency(int sample_count){
  float max_mag = 0;
  float dom_freq = 0;

  for (int k = 1; k < sample_count; k++){ // skip DC
    if (dft_magnitude[k] > max_mag){
      max_mag = dft_magnitude[k];
      dom_freq = dft_frequency[k];
    }
  }

  return dom_freq;
}

void send_data_to_pc(float* data, int n, float f){
  float dt = 1.0 / f;

  //**Hint:** The format should be **Time, Temperature, Frequency, Magnitude**.
  // Doesnt support printf-style format specifiers?
  for (int i = 0; i < n; i++){
    Serial.print(i * dt);
    Serial.print(", ");
    Serial.print(data[i]);
    Serial.print(", ");
    Serial.print(dft_frequency[i]);
    Serial.print(", ");
    Serial.println(dft_magnitude[i]);
  }

}

void loop()
{
  static float sampling_rate = 1.0;
  PwrState mode;

  int N = 120; // ~2 minutes at 1 Hz baseline

  float sample_interval = 1000.0 / sampling_rate;

  // 1. Collect data
  collect_temperature_data(temperature_data, N, sample_interval);

  // 2. Variation
  float var = calculate_variation(temperature_data, N);

  // 3. DFT
  apply_dft(temperature_data, dft_magnitude, dft_frequency, N, sampling_rate);

  // 4. Dominant frequency
  float dom_freq = get_dominant_frequency(N);

  // 5. Power mode decision
  mode = decide_power_mode(dom_freq);

  // 6. Adaptive sampling
  sampling_rate = adjust_sample_rate(dom_freq);

  // 7. Output
  send_data_to_pc(temperature_data, N, sampling_rate);

  Serial.print("Mode: ");
  Serial.println(mode);

  Serial.print("Dominant Frequency: ");
  Serial.println(dom_freq);

  Serial.print("Sampling Rate: ");
  Serial.println(sampling_rate);

  Serial.println("-------------------");
}