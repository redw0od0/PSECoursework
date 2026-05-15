# PSE Coursework

This repository contains all work completed for the PSE coursework assignment.

# Task 2

## Notes

In order to maintain type safety while also providing a small edge in code readability, I decided to use an enum for the power states, as this allows me to associate integers with english phrases/abbreviations.

``` C
typedef enum{
  PWR_IDLE = 0,
  PWR_ACTIVE = 1,
  PWR_DOWN = 2
} PwrState;

````
This is no different to using:

``` C

#define PWR_IDLE 0
#define PWR_ACTIVE 1
#define PWR_DOWN 2

```
However, in C functions are able to return enums, once again reinforcing the code's legibility:

``` C
PwrState decide_power_mode(float f){
  if (f > 0.5) return PWR_ACTIVE;
  if (f > 0.1) return PWR_IDLE;
  return PWR_DOWN;
}

```

A minor issue that occured in this task was the result of the arduino's memory constraints; the code was initially prone to failing verification steps in compilation as the static arrays were defined using an integer constant that was initially too large:

``` C
#define MAX_SAMPLES 300
float temperature_data[MAX_SAMPLES];
float dft_magnitude[MAX_SAMPLES];
float dft_frequency[MAX_SAMPLES];
```

This caused each array to occupy a size of ``` sizeof(float) * MAX_SAMPLES ```, which would have been compiled to:
 ```
  4 * 300 = 1200B 
  1200B * 3 = 3600B
  ```
The Arduino UNO SRAM is of 2kB in size, meaning that our  static arrays overflow this by 1600 Bytes.

---

# Task 4


## Operation Guide

1. Run the Arduino code normally, ideally through the Arduino IDE
2. Do not open the Serial Monitor, only one application may use it at once
3. Run:

```bash
python seriallogger.py
```

This will then provide a series of graphs in relation to the gathered temperature data

## Notes

The Python serial logger was designed to:
- collect live temperature data from the Arduino through serial communication,
- store the data into CSV format,
- and perform several forms of signal analysis and visualisation.

The script automatically:
- logs incoming serial data,
- converts the captured data into NumPy arrays,
- performs FFT analysis,
- applies signal smoothing,
- calculates temperature change rate,
- and generates several graphs for analysis.

The FFT analysis was intentionally excluded from the arduino code and instead operated in python to ensure the arduino could perform in an optimal fashion within its memory contraints and produce data in a reasonable time

---

## Temperature vs Time

This graph displays the raw recorded temperature readings over time.

In testing, the graph showed very little variation in temperature. This indicates:
- stable ambient conditions,
- low sensor noise,
- and relatively consistent readings from the temperature sensor.

The lack of major fluctuation is expected because the testing environment remained mostly unchanged during data collection.

Even though the signal remained relatively flat, the graph still demonstrates:
- successful serial logging
- correct parsing of temperature data
- continuous real-time logging functionality

---

## Magnitude vs Frequency (FFT Analysis)

The Fast Fourier Transform (FFT) graph converts the temperature signal from the time domain into the frequency domain.

This allows periodic behaviour or oscillations within the signal to be identified.

Because the captured temperature data contained minimal fluctuation:
- the FFT output showed very small frequency magnitudes,
- with most signal energy concentrated near zero frequency, causing a great spike at the origin of the graph

This is expected for a near-constant signal and demonstrates that:
- the environment contained little periodic thermal variation,
- and the recorded data was relatively noise-free.

---

## Smoothed Temperature Signal

A moving average filter was applied using:

```python
smoothed = np.convolve(temp_data, np.ones(window) / window, mode='same')
```

This smooths short-term noise by averaging nearby samples.

Because the original data already contained very little fluctuation:
- the smoothed signal closely matched the original signal.

This demonstrates that:
- the sensor readings were already stable,
- and little high-frequency noise was present in the collected data.

---

## Temperature Histogram

The histogram visualises the distribution of recorded temperature values.

Most readings were concentrated within a very narrow temperature range, producing a dense cluster of values.

This indicates:
- strong measurement consistency,
- stable environmental conditions,
- and limited random variation within the sensor readings.

---

## Temperature Change Rate

The temperature change rate graph calculates:

```python
dT/dt
```

using numerical differentiation:

```python
np.diff(temp_data) / dt
```

Since the temperature remained mostly constant:
- the rate-of-change values remained close to zero for most of the recording.

This confirms that:
- no significant thermal events occurred during testing,
- and the recorded signal changed only minimally over time.

---

## Overall Analysis

Although the recorded temperature data did not contain major fluctuations, the analysis pipeline still successfully demonstrated:
- real-time serial data acquisition,
- CSV logging,
- numerical signal processing,
- FFT frequency analysis,
- signal smoothing,
- histogram generation,
- and graphical data visualisation using matplotlib.

The consistency of the recorded data also provides evidence that the sensing system operated reliably under stable environmental conditions.



---

# Task 3 - Robot Delivery Optimisation

Task 3 focused on improving the efficiency and reliability of the pizza delivery ecosystem by modifying robot decision-making behaviour, primarily in relation to task allocation and charging priority.

The baseline implementation used relatively simple logic:
- bots selected the first available pizza,
- all bots used the same charging threshold,
- charging behaviour was static,
- and delivery decisions did not account for battery risk or payload optimisation - this often led to bots breaking while trying to complete their tasks

The modified implementation introduced several optimisations designed to improve Key Performance Indicators (KPIs) such as:
- delivered pizzas,
- energy efficiency,
- distance travelled,
- and robot survivability.

---

# Charging Optimisation

## Dynamic Charging Thresholds

The baseline implementation used a fixed 20% battery threshold for every bot type.

This was replaced with a dynamic charging threshold system which adjusts depending on:
- distance from the nearest charger,
- robot type,
- robot speed,
- and ecosystem workload pressure.

Example:

```python
travel_risk = dist_to_charger / [FACTOR]
```

Bots further away from chargers will charge earlier, while bots operating near chargers can continue working longer before charging.

Different bot types also use different base thresholds:
- drones use higher safety margins,
- faster bots can operate with lower thresholds,
- slower bots behave more conservatively.

This reduces unnecessary charging while also reducing the likelihood of bots breaking due to battery depletion.

---

## Multiple Charger Support

The baseline system used a single charger.

The modified implementation introduces multiple distributed chargers:

```python
charger_list = (
    [55, 20],
    [x0, y0],
    [x1, y1],
    ....
    ...
    ..
    .
)
```

Bots dynamically receive the index of the nearest charger using:

```python
choose_charger(bot, chargers)
```

Or can be forced to charge from it using:

```python
charge_from_nearest(bot) -> None:
```

This reduces:
- charging travel distance,
- charging turnaround time,
- and unnecessary energy consumption.

The addition of nearby chargers also enables lower charging thresholds because bots can safely reach charging stations more quickly.

---

## Energy-Aware Job Acceptance

Bots now estimate whether they possess enough battery charge to:
1. collect the pizza,
2. complete the delivery,
3. and safely reach a charger afterwards.

This is handled by:

```python
has_charge_to_start_job(bot, pizza)
```

The calculation considers:
- pickup distance,
- delivery distance,
- return-to-charger distance,
- robot payload,
- movement speed,
- and energy consumption.

This prevents bots from accepting delivery contracts they are unlikely to complete successfully.

---

## Emergency Low-Battery Behaviour

The bots have gained additional functionality that allows them to abandon their current task if their charge falls below a certain level

If charge falls below a critical level:

```python
if bot_get_charge(bot) < [CRITICAL LEVEL]
```

the bot:
- abandons its current movement,
- reroutes to the nearest charger,

This significantly reduces broken bots during long simulation runs, aiding in the increase of total pizzas delivered, as the negative effect of broken bots is more significant in long-term testing compared to that of shorter tests.

---

# Pizza Allocation Optimisation

## Nearest Pizza Allocation

The baseline implementation allocated pizzas using a simple first-ready system.

This often caused bots to:
- travel unnecessarily long distances,
- waste energy,
- and increase delivery time.

The modified implementation instead searches for the nearest available pizza:

```python
find_nearest_pizza(bot, pizzas)
```

This improves:
- delivery efficiency,
- energy usage,
- and overall throughput.

---

## Payload-Aware Delivery Selection

Bots now validate whether a pizza can safely fit within their payload capacity before accepting a contract.

```python
pizza.weight <= (bot.max_payload - bot.payload)
```

This prevents:
- rejected delivery contracts,
- overloaded bots,
- and failed assignments.

---

# KPI Analysis

The modified ecosystem is compared against a baseline implementation using collected KPIs.

Measured KPIs include:
- delivered units,
- delivered weight,
- total distance travelled,
- total energy consumed,
- total damage,
- broken bots,
- and delivery efficiency.

The system automatically compares both runs and calculates percentage improvements:

```python
print_comparison_table(baseline, modified)
```

Here is an example output from a 52-week test

```text
========================================================================
KPI COMPARISON
========================================================================
Metric              Baseline       Modified       Delta %        
------------------------------------------------------------------------
Delivered           1849           2756             49.05%
Weight              27838          41530            49.18%
Distance            126095.88      139814.76        10.88%
Energy              133958         142424            6.32%
Damage              6              2               -66.67%
Broken Bots         1              0              -100.00%
Efficiency          0.0138         0.0194           40.58%
========================================================================
```

This provides measurable evidence showing the impact of the implemented optimisations.



---

# Running The Project

Run the optimisation file using:

```bash
python3 -m  robots.robot_optimisation.py
```

---


