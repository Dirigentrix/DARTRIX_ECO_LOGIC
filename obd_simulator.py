import random
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class EngineState(Enum):
    IDLE = "idle"
    CRUISING = "cruising"
    ACCELERATING = "accelerating"
    DECELERATING = "decelerating"
    DPF_REGEN = "dpf_regen"
    LIMP_MODE = "limp_mode"

@dataclass
class OBD2Data:
    timestamp: str
    engine_rpm: int
    coolant_temp: int
    maf: float
    lambda_sensor: float
    fuel_pressure: float
    intake_temp: int
    throttle_position: int
    engine_load: int
    speed: int
    egt_temp: int
    dpf_pressure_diff: float
    egr_position: int

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

class DiagnosticTroubleCodes:
    CODES_DATABASE = {
        "P0101": {
            "description": "Mass Air Flow Circuit Range/Performance",
            "severity": "HIGH",
            "affected_systems": ["MAF", "Fuel Trim"],
            "limp_mode": True,
            "compensation_strategy": "MAF substitution with MAP + TPS"
        },
        "P0401": {
            "description": "EGR Flow Insufficient",
            "severity": "MEDIUM",
            "affected_systems": ["EGR", "NOx"],
            "limp_mode": False,
            "compensation_strategy": "Increase EGR offset by 5% using alternative map"
        },
        "P2002": {
            "description": "DPF Efficiency Below Threshold",
            "severity": "HIGH",
            "affected_systems": ["DPF", "Backpressure"],
            "limp_mode": True,
            "compensation_strategy": "Force active regeneration cycle, reduce injection timing"
        },
        "P242F": {
            "description": "DPF Ash Accumulation",
            "severity": "HIGH",
            "affected_systems": ["DPF"],
            "limp_mode": True,
            "compensation_strategy": "Increase post-injection quantity, request service"
        },
        "P0420": {
            "description": "Catalyst System Efficiency Below Threshold",
            "severity": "MEDIUM",
            "affected_systems": ["Catalytic Converter", "O2 Sensors"],
            "limp_mode": False,
            "compensation_strategy": "Richen mixture, reduce ignition timing"
        },
        "P2138": {
            "description": "Throttle Position Sensor Correlation",
            "severity": "CRITICAL",
            "affected_systems": ["Throttle", "ECU"],
            "limp_mode": True,
            "compensation_strategy": "Use backup TPS sensor, limit torque request"
        }
    }

    @classmethod
    def get_code_info(cls, code: str) -> Optional[Dict]:
        return cls.CODES_DATABASE.get(code)

class OBD2Simulator:
    def __init__(self, vehicle_type: str = "diesel_euro6"):
        self.vehicle_type = vehicle_type
        self.state = EngineState.IDLE
        self.rpm = 750
        self.speed = 0
        self.engine_temp = 20
        self.dpf_soot_load = 0.0
        self.egr_stuck = False
        self.maf_degraded = False
        self.active_codes = []
        self._time = 0
        self.engine_params = {
            "diesel_euro6": {
                "max_rpm": 4500,
                "idle_rpm": 750,
                "redline_rpm": 4200,
                "max_maf_gps": 250,
                "max_fuel_pressure": 200,
                "dpf_regeneration_temp": 600,
                "max_egt": 850
            }
        }

    def update_state(self, throttle_input: float = 0.0, external_events: List[str] = None) -> Dict:
        self._time += 0.1
        self._update_engine_state(throttle_input)
        sensor_data = self._generate_sensor_data()
        if external_events:
            self._process_external_events(external_events)
        self._update_faults()
        active_codes = self._determine_dtc_codes(sensor_data)
        self.active_codes = active_codes
        vehicle_state = {
            "timestamp": datetime.now().isoformat(),
            "obd2_pids": {
                "0x0C": sensor_data["engine_rpm"],
                "0x05": sensor_data["coolant_temp"],
                "0x10": sensor_data["maf"],
                "0x14": sensor_data["lambda_sensor"],
                "0x0A": sensor_data["fuel_pressure"],
                "0x0F": sensor_data["intake_temp"],
                "0x11": sensor_data["throttle_pos"],
                "0x04": sensor_data["engine_load"],
                "0x0D": sensor_data["speed"],
                "0x22": sensor_data["egt_temp"]
            },
            "extended_data": {
                "dpf_pressure_diff": sensor_data["dpf_pressure_diff"],
                "egr_position": sensor_data["egr_position"],
                "dpf_soot_load": self.dpf_soot_load,
                "engine_state": self.state.value,
                "calculated_fuel_consumption": self._calculate_fuel_consumption()
            },
            "active_dtcs": active_codes,
            "context": {
                "throttle_input": throttle_input,
                "time_elapsed": round(self._time, 1),
                "approaching_lez": self._check_lez_proximity()
            }
        }
        return vehicle_state

    def _update_engine_state(self, throttle: float):
        if self.speed == 0 and throttle < 5:
            self.state = EngineState.IDLE
            self.rpm = 750
        elif throttle > 70 and self.speed > 30:
            self.state = EngineState.ACCELERATING
            self.rpm = min(self.rpm + random.randint(100, 300), 4000)
        elif throttle < 10 and self.speed > 10:
            self.state = EngineState.DECELERATING
            self.rpm = max(self.rpm - random.randint(50, 200), 750)
        elif self.dpf_soot_load > 85:
            self.state = EngineState.DPF_REGEN
            self.rpm = 2500
        elif self.speed > 10:
            self.state = EngineState.CRUISING
            self.rpm = 1500 + (self.speed * 20)

        if self.state == EngineState.ACCELERATING:
            self.speed = min(self.speed + 0.5, 180)
        elif self.state == EngineState.DECELERATING:
            self.speed = max(self.speed - 0.8, 0)
        elif self.state == EngineState.CRUISING:
            self.speed = max(self.speed - 0.1, 30)

        if self.engine_temp < 90 and self._time > 5:
            self.engine_temp = min(self.engine_temp + 0.5, 90)

    def _generate_sensor_data(self) -> Dict:
        base_maf = self.rpm / 15
        base_fuel_pressure = 25 + (self.rpm / 100) * 1.2
        maf_noise = random.gauss(0, base_maf * 0.02)
        pressure_noise = random.gauss(0, 2)
        if self.maf_degraded:
            maf_noise -= base_maf * 0.25
        return {
            "engine_rpm": self.rpm + random.randint(-30, 30),
            "coolant_temp": min(self.engine_temp + random.randint(-2, 2), 105),
            "maf": max(base_maf + maf_noise, 1.0),
            "lambda_sensor": 0.85 + random.uniform(-0.05, 0.1),
            "fuel_pressure": base_fuel_pressure + pressure_noise,
            "intake_temp": 25 + random.randint(-5, 15),
            "throttle_pos": min(max(random.randint(0, 100), 0), 100),
            "engine_load": min(int((self.rpm / 4000) * 100 + random.randint(-10, 10)), 100),
            "speed": self.speed,
            "egt_temp": 200 + (self.rpm / 10) + random.randint(-20, 20),
            "dpf_pressure_diff": (self.dpf_soot_load / 100) * 5 + random.uniform(0, 1),
            "egr_position": self._calculate_egr_position()
        }

    def _calculate_egr_position(self) -> int:
        base_position = 0
        if self.state == EngineState.IDLE:
            base_position = 0
        elif self.state == EngineState.CRUISING:
            base_position = 30 + (self.speed / 180) * 30
        elif self.state == EngineState.ACCELERATING:
            base_position = 10
        elif self.state == EngineState.DPF_REGEN:
            base_position = 0
        if self.egr_stuck:
            return 5
        return min(max(base_position + random.randint(-5, 5), 0), 100)

    def _determine_dtc_codes(self, sensor_data: Dict) -> List[str]:
        codes = []
        expected_maf = sensor_data["engine_rpm"] / 15
        if sensor_data["maf"] < expected_maf * 0.6:
            codes.append("P0101")
        if sensor_data["egr_position"] < 2 and self.state == EngineState.CRUISING:
            codes.append("P0401")
        if self.dpf_soot_load > 85:
            codes.append("P2002")
            if self.dpf_soot_load > 95:
                codes.append("P242F")
        if sensor_data["lambda_sensor"] > 1.1 or sensor_data["lambda_sensor"] < 0.7:
            codes.append("P0420")
        if sensor_data["throttle_pos"] > 80 and sensor_data["engine_rpm"] < 1000:
            codes.append("P2138")
        return codes[:3] if codes else []

    def _process_external_events(self, events: List[str]):
        for event in events:
            if event == "approaching_lez":
                if "P0401" not in self.active_codes:
                    self.egr_stuck = True
            elif event == "dpf_forced_regen":
                self.dpf_soot_load = max(self.dpf_soot_load - 20, 0)
                self.state = EngineState.DPF_REGEN

    def _update_faults(self):
        if self.state == EngineState.CRUISING:
            self.dpf_soot_load = min(self.dpf_soot_load + 0.02, 100)
        elif self.state == EngineState.DPF_REGEN:
            self.dpf_soot_load = max(self.dpf_soot_load - 0.5, 0)

    def _calculate_fuel_consumption(self) -> float:
        base_consumption = 5.0
        if self.state == EngineState.ACCELERATING:
            return base_consumption * 1.8
        elif self.state == EngineState.IDLE:
            return 0.5
        elif self.state == EngineState.DPF_REGEN:
            return base_consumption * 1.5
        else:
            return base_consumption * (1 + (self.speed / 180) * 0.5)

    def _check_lez_proximity(self) -> bool:
        return self._time > 30 and self._time < 45

class AIDiagnosticInterface:
    def __init__(self):
        self.simulator = OBD2Simulator()
        self.history = []

    def get_ai_ready_state(self, throttle: float = 0.0, events: List[str] = None) -> Dict:
        raw_state = self.simulator.update_state(throttle, events)
        ai_ready = {
            "diagnostic_data": raw_state,
            "ai_instruction": {
                "required_analysis": [
                    "Identify all active DTC codes",
                    "Recommend compensation strategies",
                    "Predict emission levels",
                    "Suggest immediate actions"
                ],
                "priorities": self._determine_priorities(raw_state["active_dtcs"])
            }
        }
        self.history.append(ai_ready)
        return ai_ready

    def _determine_priorities(self, dtcs: List[str]) -> Dict:
        priorities = {"critical": [], "high": [], "medium": [], "low": []}
        for code in dtcs:
            info = DiagnosticTroubleCodes.get_code_info(code)
            if info:
                if info.get("limp_mode", False):
                    priorities["critical"].append(code)
                elif info["severity"] == "HIGH":
                    priorities["high"].append(code)
                elif info["severity"] == "MEDIUM":
                    priorities["medium"].append(code)
        return priorities

    def simulate_ai_response(self, ai_ready_data: Dict) -> Dict:
        diagnostic = ai_ready_data["diagnostic_data"]
        active_dtcs = diagnostic["active_dtcs"]
        strategies = []
        for code in active_dtcs:
            info = DiagnosticTroubleCodes.get_code_info(code)
            if info:
                strategies.append({
                    "dtc": code,
                    "description": info["description"],
                    "severity": info["severity"],
                    "recommended_action": info["compensation_strategy"]
                })
        can_enter_lez = self._evaluate_lez_compliance(diagnostic)
        response = {
            "timestamp": datetime.now().isoformat(),
            "analysis": {
                "active_faults": len(active_dtcs),
                "critical_faults": len([s for s in strategies if s["severity"] == "CRITICAL"]),
                "vehicle_safety": "LIMITED" if any(s["severity"] == "CRITICAL" for s in strategies) else "OPERATIONAL"
            },
            "compensation_strategies": strategies,
            "lez_compliance": can_enter_lez,
            "recommended_actions": self._generate_recommendations(diagnostic, strategies),
            "estimated_emissions": self._estimate_emissions(diagnostic)
        }
        return response

    def _evaluate_lez_compliance(self, diagnostic: Dict) -> Dict:
        dtcs = diagnostic["active_dtcs"]
        emission_check = {"euro_6_compliant": True, "reason": []}
        emission_codes = ["P0401", "P2002", "P0420", "P242F"]
        for code in dtcs:
            if code in emission_codes:
                emission_check["euro_6_compliant"] = False
                emission_check["reason"].append(f"Active DTC {code} affects emissions")
        if diagnostic["obd2_pids"]["0x05"] > 95:
            emission_check["euro_6_compliant"] = False
            emission_check["reason"].append("Elevated coolant temperature - potential NOx increase")
        return emission_check

    def _generate_recommendations(self, diagnostic: Dict, strategies: List) -> List[str]:
        recommendations = []
        for strategy in strategies:
            if strategy["severity"] in ["CRITICAL", "HIGH"]:
                recommendations.append(f"URGENT: {strategy['recommended_action']}")
                recommendations.append(f"Schedule service for {strategy['dtc']} immediately")
        if not diagnostic["active_dtcs"]:
            recommendations.append("Vehicle operating normally. Continue standard maintenance.")
        else:
            recommendations.append("Monitor vehicle performance. Avoid aggressive driving.")
        if diagnostic["context"].get("approaching_lez", False):
            if len(strategies) > 0:
                recommendations.append("LEZ detected ahead. Consider alternative route or service intervention before entry.")
            else:
                recommendations.append("LEZ detected ahead. Vehicle appears compliant - proceed with caution.")
        return recommendations[:5]

    def _estimate_emissions(self, diagnostic: Dict) -> Dict:
        rpm = diagnostic["obd2_pids"]["0x0C"]
        load = diagnostic["obd2_pids"]["0x04"]
        nox_base = load * 0.1
        if diagnostic["obd2_pids"]["0x22"] > 700:
            nox_base *= 1.5
        if "P2002" in diagnostic["active_dtcs"]:
            particulate = 0.08
        else:
            particulate = 0.02
        return {
            "estimated_nox_g_km": round(nox_base / 10, 2),
            "estimated_particulate_mg_km": round(particulate, 2),
            "co2_emission_g_km": round(120 + (rpm / 40), 0),
            "euro_standard": "Euro 6",
            "compliance": "PASS" if nox_base < 2.0 else "FAIL"
        }

def run_demo():
    interface = AIDiagnosticInterface()
    print("=" * 60)
    print("DARTRIX - Digital Twin OBD‑II Simulator")
    print("=" * 60)
    print("\nSCENARIUSZ 1: Normalna jazda")
    print("-" * 40)
    state = interface.get_ai_ready_state(throttle=20)
    response = interface.simulate_ai_response(state)
    print(f"Stan pojazdu: {state['diagnostic_data']['context']['engine_state']}")
    print(f"Obroty: {state['diagnostic_data']['obd2_pids']['0x0C']} RPM")
    print(f"Kody błędów: {state['diagnostic_data']['active_dtcs'] or 'BRAK'}")
    print(f"Zalecenia AI: {response['recommended_actions'][0]}")
    print("\nSCENARIUSZ 2: Zbliżanie do LEZ + Usterki EGR")
    print("-" * 40)
    for _ in range(3):
        pass
    state = interface.get_ai_ready_state(throttle=30, events=["approaching_lez"])
    response = interface.simulate_ai_response(state)
    print(f"Stan: {state['diagnostic_data']['context']['engine_state']}")
    print(f"Kody błędów: {', '.join(state['diagnostic_data']['active_dtcs'])}")
    print(f"DPF obciążenie: {state['diagnostic_data']['extended_data']['dpf_soot_load']:.1f}%")
    print(f"LEZ zgodność: {'TAK' if response['lez_compliance']['euro_6_compliant'] else 'NIE'}")
    if not response['lez_compliance']['euro_6_compliant']:
        print(f"Powód: {', '.join(response['lez_compliance']['reason'])}")
    print("\nStrategie kompensacyjne AI:")
    for strategy in response['compensation_strategies']:
        print(f"  - {strategy['dtc']}: {strategy['recommended_action']}")
    print("\nRekomendacje AI:")
    for rec in response['recommended_actions']:
        print(f"  • {rec}")
    print("\n" + "=" * 60)
    print("Demo gotowe do pokazania na Hackathonie!")
    print("=" * 60)

if __name__ == "__main__":
    run_demo()
