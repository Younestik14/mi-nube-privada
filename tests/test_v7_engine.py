import math

from v7_engine import (
    current_from_power,
    inspect,
    new_circuit,
    suggest_section,
    voltage_drop_pct,
)


def test_voltage_drop_uses_metres_without_a_second_kilometre_conversion():
    # 2 kW, 230 V, 50 m, Cu 2.5 mm²: approximately 2.65 %, not 0.00265 %.
    drop = voltage_drop_pct(2.0, 50.0, 2.5)
    assert math.isclose(drop, 2.6465, rel_tol=0.01)


def test_auto_sizing_rejects_section_when_voltage_drop_exceeds_limit():
    section, breaker, _, _ = suggest_section(2.0, 500.0, limit=3.0)
    assert section is not None
    assert section > 2.5
    assert breaker is not None


def test_inspector_flags_a_breaker_below_design_current():
    circuit = new_circuit(power_kw=4.0, voltage=230.0, breaker=10, section=6.0)
    findings = inspect([circuit])
    assert any(status == "error" and "inferior a Ib" in message for status, _, message in findings)


def test_three_phase_current_is_calculated_with_root_three():
    assert math.isclose(current_from_power(6.0, 400.0, phases=3), 8.66025, rel_tol=1e-5)
