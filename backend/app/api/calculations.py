from fastapi import APIRouter
from pydantic import BaseModel
from ..services.calculations import suggest_section, short_circuit_check, voltage_drop_pct, current_from_power, fv_dimension, phase_balance

router = APIRouter(prefix="/calc", tags=["calc"])


class SectionRequest(BaseModel):
    power_kw: float
    length_m: float
    voltage: float = 230
    phases: int = 1
    cosphi: float = 1.0
    limit: float = 5.0
    material: str = "Cobre"


class ShortCircuitRequest(BaseModel):
    icc_ka: float
    time_s: float
    section: float
    material: str = "Cobre"
    insulation: str = "PVC"


class FVRequest(BaseModel):
    power_peak_kw: float
    system: str = "230V"
    losses: float = 0.15
    irradiance: float = 5.0


@router.post("/section")
def calc_section(req: SectionRequest):
    return suggest_section(req.power_kw, req.length_m, req.voltage, req.phases, req.cosphi, req.limit, req.material)


@router.post("/short-circuit")
def calc_short_circuit(req: ShortCircuitRequest):
    return short_circuit_check(req.icc_ka, req.time_s, req.section, req.material, req.insulation)


@router.post("/fv")
def calc_fv(req: FVRequest):
    return fv_dimension(req.power_peak_kw, req.system, req.losses, req.irradiance)


@router.get("/sections")
def list_sections():
    return [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300]


@router.get("/breakers")
def list_breakers():
    return [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400]
