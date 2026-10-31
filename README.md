# ☀️ Solar Guardian: An AI-Based Smart Solar Energy System with Fault Detection, Sun Tracking, and Consumption Monitoring

> **Senior Graduation Project** — Computer System Engineering

---

## 📋 Abstract

**Solar Guardian** is an integrated smart solar energy system built around three pillars:

1. **AI-Based Fault Detection** — Compares actual measured electrical parameters (voltage & current) against theoretically expected values derived from environmental conditions (irradiance & temperature) to automatically detect, classify, and alert on panel anomalies with severity ratings and remediation recommendations.
2. **Automatic Sun Tracking** — A motorized mechanism continuously adjusts the panel's physical tilt to follow the sun throughout the day, maximising captured irradiance compared to a fixed-mount installation.
3. **Electricity Consumption & Cost Monitoring** — Tracks energy production and household consumption, then calculates the estimated electricity bill based on the applicable local tariff, giving users a clear, actionable view of their energy usage and costs.

The result is a complete platform combining embedded hardware, IoT connectivity, AI-powered analysis, and a mobile application — designed specifically for deployment conditions in Palestine.

To validate the concept before physical hardware deployment, an interactive **Simulation Dashboard** (`app.py`) was built using Streamlit. It replicates the full mathematical model and fault injection logic in software, allowing the team to verify diagnostic accuracy, tune thresholds, and demonstrate all fault scenarios to the evaluation committee without requiring live sensor readings.

---

## 🎯 Problem Statement

Solar PV systems in Palestine face four compounding problems that this project addresses together:

1. **Silent performance loss** — Dust accumulation, cable faults, partial shading, and cell degradation all reduce energy yield without obvious physical indicators. Traditional monitoring only reports raw readings; Solar Guardian goes further by *reasoning about what the output should be* under current conditions and flagging deviations as classified faults in real time.
2. **Fixed-panel irradiance waste** — A static mount cannot follow the sun's arc, meaning the panel operates below its potential for most of the day. An automatic tracking mechanism closes this gap.
3. **No consumption transparency** — Users of grid-connected or hybrid systems currently lack a continuous, clear view of their electricity consumption and expected bill without contacting the utility company.
4. **Diagnosis requires expertise** — Identifying fault causes and severity today demands on-site technical knowledge. Solar Guardian surfaces fault type, confidence level, and actionable recommendations directly to the user.

---

## 🔍 How Solar Guardian Differs from Related Work

Most prior solar panel monitoring systems that have been developed focus on a **single, narrow concern** and solve it in isolation. Solar Guardian was designed from the ground up to be a fundamentally different class of system. The key distinguishing points are:

### 1. Electrical Intelligence vs. Visual Inspection
Many existing systems rely on a **camera and computer-vision model** (e.g., image classification or object detection) to observe the panel surface and infer whether it is dirty. Solar Guardian takes the opposite approach: it uses **no camera at all**. Instead, it reads the panel's live electrical output (voltage and current) and compares it against a physics-based expected value computed from the current environmental conditions (irradiance and temperature). This means faults are detected from *what the panel is actually doing electrically*, not from how it looks — making the diagnosis more directly tied to real energy loss.

### 2. Fault Classification, Not Just Contamination Detection
Prior work in this space typically answers one binary question: *"Is the panel dirty?"* Solar Guardian answers a richer question: *"What kind of fault is present, how severe is it, and what should the user do?"* It classifies five distinct fault modes — Partial Shading, Dust & Soiling, Open Circuit, Short Circuit, and Long-Term Degradation — each with a **severity level**, a **confidence score**, and a plain-language **remediation recommendation**.

### 3. Three Integrated Subsystems in One Platform
Existing projects are almost always single-purpose: a cleaning robot, a monitoring dashboard, or an MPPT tracker — each built as a standalone system. Solar Guardian integrates three fully operational subsystems into a **single embedded platform running on one ESP32**:
- AI-based fault detection and classification
- Automatic sun tracking via LDR differential sensing
- Electricity consumption monitoring and bill estimation

No prior work reviewed combines all three in a unified, low-cost embedded design.

### 4. Actionable Economic Output
Most monitoring systems stop at raw sensor data or fault alerts. Solar Guardian goes further by calculating the **estimated electricity bill** from the grid draw, giving users a direct financial view of their system's performance — a feature absent from purely technical monitoring or cleaning-focused systems.

### 5. Dual Expected-Power Validation
To make fault confidence more robust, Solar Guardian computes the expected panel output using **two independent methods simultaneously**: a real-time physics model (temperature coefficient + irradiance ratio + angle loss + dust factor) and an **on-device AI Time-Series Transformer** trained on the rolling session history. A fault is flagged with higher confidence only when both models agree — significantly reducing false positives compared to single-threshold systems.

### 6. No Mechanical Cleaning — Inform and Track Instead
Systems that attach a brush and water pump to physically clean the panel introduce mechanical complexity, water consumption, and maintenance overhead. Solar Guardian's philosophy is different: **detect the fault precisely, quantify the loss, and inform the user with a clear recommendation** — then let the user decide when and how to act. The only motor in the system is the sun-tracking servo, which directly increases energy yield rather than reacting to contamination after the fact.

### Summary Table

| Aspect | Typical Prior Approaches | Solar Guardian |
|--------|--------------------------|----------------|
| Fault detection method | Camera + image/CV model | Electrical parameter deviation from physics model |
| Output | "Panel is dirty / clean" | Fault type, severity, confidence, recommendation |
| Subsystems covered | Single (cleaning OR monitoring OR tracking) | Three (fault detection + sun tracking + billing) |
| Economic output | None | Estimated electricity bill in ILS |
| Expected-power validation | Single threshold or none | Dual: physics model + AI Transformer |
| Hardware complexity | Camera, motor, water pump, Raspberry Pi | Electrical sensors only, single ESP32 |
| Water / mechanical usage | Yes (cleaning systems) | None |

---

## 🏗️ System Architecture

```
[Physical Sensors & Actuators]   [Microcontroller]   [Cloud / Local Server]   [User Interface]
  ├─ ACS712 (Current)                  │                      │                      │
  ├─ Voltage Divider            ──>  ESP32  ──> WiFi ──>  MySQL DB  ──>  AI  ──>  Mobile App
  ├─ DS18B20 (Temp)                    │                      │         Engine    (Primary UI)
  ├─ Mini Cell (Irradiance)            │               FastAPI / Flask    │
  ├─ LDR Sensors ×2 (Sun Pos.)  ──> Servo/Stepper                        └──>  Web Dashboard
  └─ Energy Meter (Consumption)        │                                        (Streamlit)
```

The system has three active subsystems running simultaneously on the ESP32:
- **Sensing loop** — reads V, I, temperature, and irradiance every 10 s and POSTs to the server
- **Tracking loop** — compares LDR readings to determine sun offset; drives the servo to re-align
- **Metering loop** — accumulates energy (Wh) and consumption data for billing calculation

---

## ⚙️ Hardware Components

| Component | Role | Notes |
|-----------|------|-------|
| **Solar Floodlight (~120 NIS)** | Main PV panel prototype source | Provides real solar cell, LED load, and battery |
| **ESP32 Microcontroller** | Data acquisition, tracking control & WiFi transmission | Sends readings every 10 seconds via HTTP POST |
| **ACS712 Current Sensor (5A/20A)** | Measures actual panel output current | Wired in-series with the positive PV output lead |
| **Voltage Divider (10kΩ / 2kΩ)** | Scales panel voltage to ADC-safe range | Steps 18V down to <3.3V for ESP32 ADC pins |
| **Zener Diode** | Overvoltage protection on ADC pins | Clamps any voltage spike to a safe level before it reaches the ESP32 |
| **DS18B20 Temperature Sensor** | Measures PV cell temperature | Waterproof; mounted on the back of the panel |
| **Mini Solar Cell (Irradiance Sensor)** | Measures solar irradiance reference | Short-circuit current (Isc) is linearly proportional to W/m² |
| **LDR Sensors ×2** | Detect differential light intensity for sun position | One on each side of a divider; imbalance signals tracking offset |
| **Servo / Stepper Motor** | Physically rotates the panel to follow the sun | Driven by ESP32 PWM based on LDR differential |
| **Energy Meter / Shunt** | Measures cumulative energy consumption (Wh) | Used for bill estimation against local tariff |

### Current Measurement Circuit — ACS712

The ACS712 is fully electrically isolated in the high-current path of the PV panel, but requires a critical protection step: **it operates at 5V and its output signal can reach 5V, while the ESP32 ADC pins only tolerate 3.3V.**

**Protection solution:**
- The ACS712 is powered from the ESP32's `Vin / 5V` pin
- Its signal output (`Vout`) is **never connected directly** to the ESP32
- Two equal **10 kΩ resistors** form a voltage divider that halves the output signal from the (0–5V) range down to (0–2.5V) — safely within ESP32 limits
- The PV panel's power leads are connected in-series through the ACS712's dedicated high-current terminals

```
Panel (+) ──── [ACS712 IP+ ▶ IP-] ──── Load
                      │
                   Vout (0–5V)
                      │
                   [10kΩ]
                      ├──────> ESP32 ADC Pin 35 (reads 0–2.5V)
                   [10kΩ]
                      │
                     GND
```

### Voltage Measurement Circuit — Zener Diode Protection

The panel voltage (up to ~18V open-circuit) must be stepped down below 3.3V for the ESP32 ADC. A resistor voltage divider combined with a Zener diode achieves this safely.

**Components:**
- R₁ = **10 kΩ** (series resistor)
- R₂ = **2 kΩ** (shunt resistor)
- Zener diode = **3.3V** (connected in parallel with R₂, cathode toward signal line, anode to GND)

**Wiring:**
- Panel `(+)` → R₁ → junction node → ESP32 **GPIO 34** (ADC-only input pin, no internal pull)
- Junction node → R₂ → GND
- Zener diode in parallel with R₂ (clamps any spike above 3.3V to protect the ADC pin)

```
Panel (+) ──[R₁ 10kΩ]──┬──────────> ESP32 GPIO 34
                        │
                     [R₂ 2kΩ]  ⟂ Zener 3.3V (cathode up)
                        │
                       GND
```

**Scaling formula — recovering real panel voltage in firmware:**

$$V_{panel} = V_{ADC} \times \frac{R_1 + R_2}{R_2} = V_{ADC} \times \frac{10 + 2}{2} = V_{ADC} \times 6$$

> At peak sun (18V open-circuit), the ESP32 reads **3.0V** — safely within the 3.3V limit. The Zener clamps any transient spike above 3.3V to GND before it can damage the pin.

### Irradiance Sensing — DIY Approach
A small solar cell wired with a shunt resistor acts as an irradiance sensor: its short-circuit current is directly proportional to incoming solar radiation. It is mounted at the **same tilt angle** as the main panel and calibrated to ~1000 W/m² at peak noon sun.

### ESP32 Firmware Highlights (C++)
- Reads voltage & current from ADC pins 34 and 35
- Reads LDR differential and drives servo for sun tracking
- Reconnects to WiFi automatically on disconnect
- Transmits JSON payload containing device UUID (MAC address) to the server
- Configurable sample interval (default: 10 seconds)

---

## 🛠️ Fault Detection Capabilities

| Detected Pattern | Physical Condition | Diagnosis Trigger |
|---|---|---|
| Low `I`, normal `V`, high irradiance | **Partial Shading** | Current drops sharply while reference cell still reads high irradiance |
| Gradual drop in both `V` and `I` | **Dust & Soiling** | Power deviation >10–25% below expected over 14+ days at noon |
| `V ≈ Voc`, `I = 0` | **Open Circuit / Cable Cut** | Voltage at open-circuit level with zero current despite good sun |
| `V ≈ 0`, `I > 0` | **Short Circuit** | Voltage collapses while current spikes above Isc |
| Long-term efficiency decline | **Panel Degradation (PID)** | Efficiency ratio trend degrades against temperature-corrected baseline curves |

For every detected fault the system outputs a **severity level** (Low / Medium / High / Critical), a **confidence score**, and a plain-language **recommendation** (e.g., "Clean panels — estimated 18% soiling loss detected").

---

## 🌞 Automatic Sun Tracking

A fixed panel loses a significant fraction of potential energy yield because the angle of incidence changes throughout the day. Solar Guardian's tracking subsystem eliminates this loss by continuously realigning the panel.

### How It Works

Two LDR (light-dependent resistor) sensors are mounted on opposite sides of a small divider fin. When the sun is perfectly aligned the two sensors read equal light intensity. Any offset produces a differential that the ESP32 translates into a motor correction signal.

```
         ┌─────────┐
   LDR₁ ─┤  divider ├─ LDR₂
         └────┬────┘
              │  differential → ESP32 → Servo/Stepper PWM
              ▼
        Panel tilts until LDR₁ = LDR₂
```

### Tracking Logic (Pseudocode)
```
loop every 2 s:
    diff = LDR1_reading - LDR2_reading
    if abs(diff) > DEAD_BAND:
        step motor toward brighter side
    log current angle to sensor_readings
```

### Benefits
| Condition | Fixed Panel | With Tracking |
|-----------|-------------|---------------|
| Morning / late afternoon | ~40–60% of peak output | ~85–95% of peak output |
| Full day energy yield (est.) | Baseline | +20–35% more kWh |

---

## 🧮 Expected Power — Two Independent Methods

The system computes **expected power using two parallel approaches** and compares both against the actual measured output:

| Method | How it works | When it's available |
|--------|-------------|---------------------|
| **1. Theoretical Model** | Physics equations using temperature coefficient, irradiance ratio, angle cosine loss, and dust factor | Always — computed instantly from current sensor inputs |
| **2. AI Time-Series Transformer** | Learns patterns from the rolling history of past readings and forecasts what the power *should* be at this moment | After enough history has been collected (minimum ~10 readings) |

Having two independent expected-power references strengthens fault confidence: if both the theoretical model and the AI forecast agree that output should be higher than what is measured, the fault diagnosis is far more reliable.

### Real-Time Efficiency Index

The core diagnostic metric used by the system is the **Efficiency Index**, which compares live measured power against the expected historical power:

$$\text{Efficiency Index} = \left(\frac{\text{Live Power}}{\text{Expected Power}}\right) \times 100\%$$

| Efficiency Index | Status | Meaning |
|-----------------|--------|---------|
| **> 85%** | 🟢 Green — System Healthy | Panel performing within normal range |
| **50% – 85%** | 🟡 Yellow — Performance Degradation | Possible soiling, shading, or angle misalignment |
| **< 50%** | 🔴 Red — Severe Fault | Short circuit, open circuit, or critical degradation |

### Theoretical Baseline
```
V_expected = V_oc_ideal × (1 − (T_cell − 25) × 0.004)   # Temperature coefficient: −0.4%/°C
I_expected = I_sc_ideal × (Irradiance / 1000)             # Linear proportionality to G (W/m²)
P_expected = V_expected × I_expected × cos(Δθ)            # Angle misalignment loss
```

Where:
- `V_oc_ideal = 18.0 V` (prototype open-circuit reference)
- `I_sc_ideal = 1.5 A` (prototype short-circuit reference)
- `Δθ` = deviation between physical tilt angle and optimal sun angle

### Dust Factor
```
P_actual ≈ P_ideal × (1 − dust_percentage / 100)
```

---

## 🧠 AI & Machine Learning Components

### 1. Fault Classification (Random Forest / SVM)
- **Inputs:** Voltage, Current, Temperature, Irradiance
- **Output:** Fault class — `Normal`, `Partial Shading`, `Short Circuit`, `Soiling`
- **Why RF/SVM:** Robust to sensor noise; no large dataset required for initial deployment
- **Training data:** Labeled readings collected from the prototype under simulated fault conditions

```python
from sklearn.ensemble import RandomForestClassifier

X_train = [
    [18.0, 1.2, 35.0, 950.0],   # Normal
    [17.5, 0.2, 34.0, 900.0],   # Partial Shading
    [0.1,  4.5, 40.0, 950.0],   # Short Circuit
    [14.0, 0.8, 45.0, 920.0],   # Soiling
]
y_train = [0, 1, 2, 3]

model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)
```

### 2. Time-Series Transformer Forecast (HuggingFace)
- Uses `TimeSeriesTransformerForPrediction` from 🤗 Transformers
- Trained **on-the-fly** from the rolling 30-point session history
- Predicts the **next expected power output** based on time-of-day, temperature, and irradiance features
- Forecasts are shown as a diamond marker on the live power chart
- Supports configurable context length (4–20 steps) and training steps (5–120)

---

## 📱 Mobile Application

The primary user interface for the deployed system is a **mobile application** (iOS & Android) that connects to the FastAPI backend. The Streamlit simulation dashboard is a development/validation tool; the mobile app is what end users interact with daily.

### Key Screens

| Screen | Content |
|--------|---------|
| **Live Dashboard** | Real-time voltage, current, power, panel angle, and system health status |
| **Fault Alerts** | Push notifications for detected faults with severity, confidence, and recommended action |
| **Sun Tracking Status** | Current panel angle, target angle, and daily tracking log |
| **Energy Overview** | Daily / weekly / monthly production vs. consumption charts |
| **Bill Estimator** | Current-period grid draw and projected electricity cost in ILS |
| **Historical Data** | Browsable log of all sensor readings and past fault events |

### Target Users
- **Homeowners** with rooftop solar or hybrid (solar + grid) systems — need to know system health and estimated bill without technical expertise
- **Small businesses** (shops, workshops, farms) relying on solar — an unnoticed fault directly costs money and operating time
- **Solar installers & maintenance technicians** — use fault diagnosis, severity scores, and recommendations to locate problems faster and avoid unnecessary site visits

---

## 💻 Concept Validation — Streamlit Simulation Dashboard

The simulation dashboard (`app.py`) is a **proof-of-concept tool** built to validate the project's mathematical model and fault detection logic before the physical hardware prototype is fully deployed. It mirrors the exact equations and diagnostic rules used in the real system, allowing the team to:

- Verify that the fault detection thresholds behave correctly across all scenarios
- Demonstrate every fault type (short circuit, open circuit, shading, soiling) interactively to the evaluation committee
- Test the AI time-series forecasting module against synthetic sensor data

### Tech Stack
| Layer | Technology |
|-------|------------|
| UI Framework | [Streamlit](https://streamlit.io) |
| Data Processing | NumPy, Pandas |
| Visualization | Plotly |
| AI/ML Forecasting | HuggingFace Transformers, PyTorch |

### Running the Dashboard
```bash
pip install streamlit numpy pandas plotly transformers torch
streamlit run app.py
```

---

## 📊 Dashboard Features

### Sidebar Controls
| Control | Range | Purpose |
|---------|-------|---------|
| Solar Irradiance (W/m²) | 0 – 1200 | Simulate cloud cover or time of day |
| Panel Temperature (°C) | 10 – 75 | Model thermal efficiency loss |
| Physical Tilt Angle (°) | 0 – 90 | Model panel mounting misalignment |
| Optimal Sun Angle (°) | 0 – 90 | Reference angle for cosine loss |
| Dust & Soiling (%) | 0 – 100 | Simulate gradual soiling accumulation |
| Fault Mode | Select | Inject Short Circuit or Open Circuit faults |
| Transformer Forecast | Toggle | Enable AI time-series prediction |

### KPI Metrics (Live)
- 🔵 **Live Voltage** (V)
- 🟠 **Live Current** (A)
- 🟢 **Actual Power Output** (W)
- 🔴 **Expected Yield Power** (W)
- 🟣 **Transformer Expected Power** (W)

### Diagnostic Status Banner
| Condition | Status |
|-----------|--------|
| All parameters nominal | 🟢 System Healthy |
| Dust ≥ 25% | 🍃 High Dust & Soiling Warning |
| Angle deviation ≥ 20° | 📐 Panel Tilt Adjustment Required |
| Short circuit injected | 💥 Short Circuit Fault Detected |
| Open circuit injected | 🔌 Open Circuit / Cable Cut Detected |

### Charts
- **Electrical Characteristics Chart:** Tracks live Voltage and Current over time
- **Efficiency Chart:** Overlays Actual Power, Expected Power, and Transformer Forecast
- **Historical Registry Table:** Scrollable log of all timestamped sensor readings

### Live Update Engine
- Auto-refreshes the dashboard every second using `st.rerun()`
- Supports **Unlimited** mode or **Max Steps** (capped run) mode
- Rolling buffer stores the last 30 data points for chart smoothness

---

## 🗄️ Backend & Database (IoT Architecture)

The backend follows a **Multi-Tenant IoT Architecture** — a professional-grade design where every physical device is identified by a unique serial number (MAC Address or UUID) and linked to a specific user account in the database. This ensures each user sees only their own panel data, securely and separately.

### How it works
1. The ESP32 automatically reads its own MAC address and includes it in every HTTP POST it sends to the server
2. An administrator links that device UUID to a user account once during registration
3. All sensor readings are tagged with the device UUID, so the dashboard filters and displays only the readings belonging to the logged-in user

### Database Schema (MySQL)

```
users               (user_id, username, password_hash)
     └──> devices       (device_uuid [MAC], device_name, user_id)
               └──> sensor_readings  (id, device_uuid, voltage, current,
                                      temperature, irradiance, panel_angle, timestamp)
               └──> consumption_log  (id, device_uuid, kwh_consumed,
                                      kwh_produced, grid_kwh, estimated_cost_ils, date)
```

| Table | Key Fields | Purpose |
|-------|-----------|---------|
| `users` | `user_id`, `username`, `password_hash` | Stores user accounts |
| `devices` | `device_uuid`, `device_name`, `user_id` | Links each ESP32 to its owner |
| `sensor_readings` | `device_uuid`, `voltage`, `current`, `temperature`, `irradiance`, `panel_angle`, `timestamp` | Time-series telemetry log |
| `consumption_log` | `device_uuid`, `kwh_consumed`, `kwh_produced`, `grid_kwh`, `estimated_cost_ils`, `date` | Daily energy balance and bill estimate |

- A Python **FastAPI** or **Flask** backend receives incoming ESP32 readings, stores them in MySQL, and runs AI inference on each new entry
- The user dashboard and mobile app query only the readings belonging to the authenticated user's registered devices

---

## 💡 Electricity Consumption & Cost Monitoring

Solar Guardian tracks both what the panel *produces* and what the household *consumes*, then calculates the estimated electricity bill based on the applicable Palestinian utility tariff.

### Energy Balance
```
Grid Draw (kWh) = Total Consumption (kWh) − Solar Production (kWh)
Estimated Bill  = Grid Draw × Applicable Tariff Rate (ILS/kWh)
```

### What the User Sees
| Metric | Description |
|--------|-------------|
| **Daily / Monthly Production** | kWh generated by the solar panel |
| **Daily / Monthly Consumption** | kWh used by the household |
| **Grid Dependency** | How much was drawn from the public grid |
| **Estimated Bill (ILS)** | Financial cost of grid consumption at current tariff |
| **Savings vs. Grid-Only** | How much was saved by having solar this period |

### Tariff Tiers
The backend stores the applicable tiered tariff schedule so the cost calculation remains accurate even when rates change — an administrator can update the tariff table without changing application code.

---

## 📁 Project Structure

```
solar-ai/
├── app.py          # Streamlit simulation & AI dashboard (concept validation)
├── idea.txt        # Full project ideation and discussion log
└── README.md       # This file
```

> **Senior 2 additions:** ESP32 firmware (`firmware/`), FastAPI backend (`server/`), and mobile app (`mobile/`) will be added as development progresses.

---

## 🗺️ Project Roadmap

### Senior 1 — Current Phase ✅
- [x] Define system architecture and fault detection methodology
- [x] Build mathematical model for expected power output
- [x] Develop Streamlit simulation dashboard to validate the concept
- [x] Integrate AI time-series transformer for expected power forecasting
- [x] Simulate all fault scenarios (short circuit, open circuit, shading, soiling)

### Senior 2 — Hardware Implementation Phase 🔜
- [ ] Purchase hardware components (ESP32, ACS712, DS18B20, solar floodlight, LDRs, servo motor)
- [ ] Build and wire the physical prototype
- [ ] Implement ESP32 firmware for live sensor data acquisition and WiFi transmission
- [ ] Implement sun-tracking control loop (LDR differential → servo PWM)
- [ ] Set up backend server (FastAPI + MySQL) to store and process telemetry
- [ ] Train and deploy the Random Forest fault classifier on real prototype data
- [ ] Connect the live data stream to the dashboard and mobile app
- [ ] Integrate electricity consumption metering and bill estimation
- [ ] Build the mobile application (iOS / Android)
- [ ] Validate results against the simulation model

---

## 🌍 Context

Developed in **Palestine** as a graduation project targeting real-world deployment conditions — including local hardware sourcing, cost-optimized sensor alternatives, and field-calibrated irradiance measurement using locally available mini solar cells.

---

## 👥 Team

| Student ID | Name |
|------------|------|
| 202210761 | Bana Mustafa Nasser Hamarshi |
| 202210223 | Dalya Yousef Saber Mustafa |
| 202210630 | Bisan Karem Mahmoud Qalalwe |

**Supervisor:** Mr. Hussein Younis  
**Department:** Computer System Engineering  
**Faculty:** Faculty of Engineering  
**Institution:** Arab American University — Palestine  
**Academic Year:** 2025 – 2026
