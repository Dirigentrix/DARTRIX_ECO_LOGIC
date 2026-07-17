# DARTRIX ECO‑LOGIC

**DARTRIX ECO‑LOGIC** is a deterministic digital‑twin OBD‑II simulator engineered for **Low‑Emission‑Zone (LEZ) compliance**, deterministic control, and hackathon demo purposes.  It showcases DARTRIX‑style technical rigor and clean, production‑ready code.

---

## 🎯 Mission
- Provide a **real‑time, reproducible OBD‑II data stream** that mirrors the behaviour of a Euro‑6 diesel power‑train.
- Detect and surface **Diagnostic Trouble Codes (DTCs)** with severity‑aware priorities.
- Evaluate **LEZ compliance** on‑the‑fly and suggest **compensation strategies**.
- Offer an **AI‑driven diagnostic interface** that can be queried programmatically or via the command line.

---

## 🛠️ Technical Specification
- **Language:** Python 3.11
- **Core components:**
  - `EngineState` – deterministic state machine (idle, cruising, accelerating, …).
  - `OBD2Simulator` – generates realistic PID values, DPF soot load, EGR behaviour, and fault injection.
  - `DiagnosticTroubleCodes` – curated DTC database with severity, affected systems, limp‑mode flag and compensation strategy.
  - `AIDiagnosticInterface` – AI‑ready wrapper that formats data, determines priorities, evaluates LEZ compliance and produces recommendations.
- **Determinism:** All random variations are seeded internally; repeated runs with the same throttle profile produce identical output, enabling reproducible demos.
- **Extensibility:** Add new DTCs in `DiagnosticTroubleCodes.CODES_DATABASE`.  Extend the AI instruction set in `AIDiagnosticInterface._generate_recommendations`.

---

## 🚀 Demo (run_demo)
```bash
python obd_simulator.py
```
The demo walks through two scenarios:
1. **Normal driving** – shows typical sensor data, no active DTCs, and a single AI recommendation.
2. **Approaching a LEZ with EGR fault** – triggers DTCs, evaluates LEZ compliance, and lists compensation strategies.

---

## 📦 Installation
```bash
pip install -r requirements.txt   # (standard library only, no external deps)
```
The simulator runs out‑of‑the‑box; no hardware is required.

---

## 📚 Usage Overview
```python
from obd_simulator import AIDiagnosticInterface

ai = AIDiagnosticInterface()
state = ai.get_ai_ready_state(throttle=25, events=["approaching_lez"])
response = ai.simulate_ai_response(state)
print(response)
```
The returned dictionary contains:
- `diagnostic_data` – raw OBD‑II PIDs and extended metrics.
- `active_dtcs` – list of current DTCs.
- `compensation_strategies` – AI‑recommended mitigations.
- `lez_compliance` – Euro‑6 compliance flag and reasons.
- `estimated_emissions` – calculated NOx, particulate and CO₂ values.

---

## 📜 License
MIT – feel free to fork, adapt, and integrate into your own fleet‑management or emissions‑monitoring solutions.

---

*Built with the **DARTRIX** philosophy – deterministic, auditable, and ready for hackathon showcase.*
