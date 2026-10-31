"""Motor de simulación PLC (Siemens S7-1200/1500)."""
import time
import json
from typing import Any, Optional


class PLCEngine:
    def __init__(self, cpu="S7-1200"):
        self.cpu = cpu
        self.reset()

    def reset(self):
        # Memoria de proceso
        self.I = {}   # entradas (bool/int/real)
        self.Q = {}   # salidas
        self.M = {}   # marcas
        self.DB = {}  # bloques de datos: {db_num: {addr: value}}
        # Temporizadores y contadores
        self.T = {}   # {timer_id: {type, preset, accumulated, running, done}}
        self.C = {}   # {counter_id: {type, preset, count, done}}
        # Programa: lista de OBs, cada OB tiene lista de redes (rungs)
        self.program = {"OB1": []}  # OB1 = main cycle
        self.selected_ob = "OB1"
        # Estado
        self.cycle_count = 0
        self.cycle_time_ms = 0
        self.running = False
        self.debug_mode = False
        self.current_network = 0
        self.current_element = 0
        # HMI
        self.hmi_inputs = {}   # {name: value}
        self.hmi_outputs = {}  # {name: value}
        # Diagnóstico
        self.diagnostics = []
        # Variables para watch table
        self.watch = []

    # ── Memoria helpers ─────────────────────────────────────
    def get_var(self, addr: str) -> Any:
        """Lee una variable por dirección (I0.0, Q0.0, M0.0, DB1.DBX0.0, T1, C1, MW0, etc.)"""
        addr = addr.strip().upper()
        if addr.startswith("I"):
            return self.I.get(addr, False)
        if addr.startswith("Q"):
            return self.Q.get(addr, False)
        if addr.startswith("M"):
            return self.M.get(addr, False)
        if addr.startswith("DB"):
            parts = addr.split(".")
            db_num = int(parts[0][2:])
            rest = ".".join(parts[1:])
            db = self.DB.get(db_num, {})
            return db.get(rest, 0)
        if addr.startswith("T"):
            t = self.T.get(addr, {})
            return t.get("done", False)
        if addr.startswith("C"):
            c = self.C.get(addr, {})
            return c.get("done", False)
        return False

    def set_var(self, addr: str, value: Any):
        addr = addr.strip().upper()
        if addr.startswith("I"):
            self.I[addr] = value
        elif addr.startswith("Q"):
            self.Q[addr] = value
        elif addr.startswith("M"):
            self.M[addr] = value
        elif addr.startswith("DB"):
            parts = addr.split(".")
            db_num = int(parts[0][2:])
            rest = ".".join(parts[1:])
            self.DB.setdefault(db_num, {})[rest] = value
        elif addr.startswith("T"):
            self.T.setdefault(addr, {})["done"] = bool(value)
        elif addr.startswith("C"):
            self.C.setdefault(addr, {})["done"] = bool(value)

    def reset_memory(self):
        self.I = {}
        self.Q = {}
        self.M = {}
        self.DB = {}
        self.T = {}
        self.C = {}

    # ── Programa helpers ────────────────────────────────────
    def add_network(self, ob="OB1"):
        self.program.setdefault(ob, []).append({"elements": [], "output": None})
        return len(self.program[ob]) - 1

    def set_network(self, ob, idx, network):
        self.program[ob][idx] = network

    def get_networks(self, ob="OB1"):
        return self.program.get(ob, [])

    # ── Ejecución de un rung (red) ──────────────────────────
    def eval_element(self, el: dict) -> bool:
        """Evalúa un elemento y devuelve su estado (bool)."""
        t = el.get("type", "")
        if t == "contact_no":
            return bool(self.get_var(el.get("addr", "")))
        if t == "contact_nc":
            return not bool(self.get_var(el.get("addr", "")))
        if t == "contact_p":  # flanco positivo
            prev = el.get("_prev", False)
            cur = bool(self.get_var(el.get("addr", "")))
            el["_prev"] = cur
            return cur and not prev
        if t == "contact_n":  # flanco negativo
            prev = el.get("_prev", False)
            cur = bool(self.get_var(el.get("addr", "")))
            el["_prev"] = cur
            return (not cur) and prev
        if t == "coil":
            return True  # la bobina se evalúa por la red
        if t == "coil_set":
            return True
        if t == "coil_reset":
            return True
        if t == "coil_neg":
            return True
        # Bloques funcionales
        if t == "ton":
            # Timer on-delay
            tid = el.get("id", "T1")
            preset = el.get("preset", 1000)
            inp = self.get_var(el.get("input", ""))
            t = self.T.setdefault(tid, {"type": "TON", "preset": preset, "accum": 0, "running": False, "done": False, "start": None})
            t["preset"] = preset
            if inp:
                if not t["running"]:
                    t["running"] = True
                    t["start"] = time.time()
                    t["accum"] = 0
                else:
                    t["accum"] = (time.time() - t["start"]) * 1000
                t["done"] = t["accum"] >= preset
            else:
                t["running"] = False
                t["accum"] = 0
                t["done"] = False
            self.set_var(tid, t["done"])
            return t["done"]
        if t == "tof":
            tid = el.get("id", "T1")
            preset = el.get("preset", 1000)
            inp = self.get_var(el.get("input", ""))
            t = self.T.setdefault(tid, {"type": "TOF", "preset": preset, "accum": 0, "running": False, "done": False, "start": None})
            t["preset"] = preset
            if not inp:
                if not t["running"]:
                    t["running"] = True
                    t["start"] = time.time()
                    t["accum"] = 0
                else:
                    t["accum"] = (time.time() - t["start"]) * 1000
                t["done"] = t["accum"] < preset
            else:
                t["running"] = False
                t["accum"] = 0
                t["done"] = True
            self.set_var(tid, t["done"])
            return t["done"]
        if t == "tp":
            tid = el.get("id", "T1")
            preset = el.get("preset", 1000)
            inp = self.get_var(el.get("input", ""))
            t = self.T.setdefault(tid, {"type": "TP", "preset": preset, "accum": 0, "running": False, "done": False, "start": None, "triggered": False})
            t["preset"] = preset
            if inp and not t["triggered"]:
                t["triggered"] = True
                t["running"] = True
                t["start"] = time.time()
                t["accum"] = 0
                t["done"] = True
            if t["running"]:
                t["accum"] = (time.time() - t["start"]) * 1000
                if t["accum"] >= preset:
                    t["running"] = False
                    t["done"] = False
                    t["triggered"] = False
            if not inp:
                t["triggered"] = False
            self.set_var(tid, t["done"])
            return t["done"]
        if t == "ctu":
            cid = el.get("id", "C1")
            preset = el.get("preset", 10)
            inp = self.get_var(el.get("input", ""))
            reset = self.get_var(el.get("reset", ""))
            c = self.C.setdefault(cid, {"type": "CTU", "preset": preset, "count": 0, "done": False, "prev": False})
            c["preset"] = preset
            if reset:
                c["count"] = 0
                c["done"] = False
            if inp and not c["prev"]:
                c["count"] += 1
                c["done"] = c["count"] >= preset
            c["prev"] = bool(inp)
            self.set_var(cid, c["done"])
            return c["done"]
        if t == "ctd":
            cid = el.get("id", "C1")
            preset = el.get("preset", 10)
            inp = self.get_var(el.get("input", ""))
            load = self.get_var(el.get("load", ""))
            c = self.C.setdefault(cid, {"type": "CTD", "preset": preset, "count": preset, "done": False, "prev": False})
            c["preset"] = preset
            if load:
                c["count"] = preset
                c["done"] = False
            if inp and not c["prev"]:
                c["count"] = max(0, c["count"] - 1)
                c["done"] = c["count"] <= 0
            c["prev"] = bool(inp)
            self.set_var(cid, c["done"])
            return c["done"]
        if t == "cmp":
            # Comparador: ==, <>, <, >, <=, >=
            op = el.get("op", "==")
            a = self.get_var(el.get("in1", ""))
            b = self.get_var(el.get("in2", ""))
            try:
                a = float(a); b = float(b)
            except (ValueError, TypeError):
                a = bool(a); b = bool(b)
            if op == "==":
                return a == b
            if op == "<>":
                return a != b
            if op == "<":
                return a < b
            if op == ">":
                return a > b
            if op == "<=":
                return a <= b
            if op == ">=":
                return a >= b
            return False
        if t == "math":
            op = el.get("op", "ADD")
            a = self.get_var(el.get("in1", ""))
            b = self.get_var(el.get("in2", ""))
            try:
                a = float(a); b = float(b)
            except (ValueError, TypeError):
                a = 0; b = 0
            if op == "ADD":
                res = a + b
            elif op == "SUB":
                res = a - b
            elif op == "MUL":
                res = a * b
            elif op == "DIV":
                res = a / b if b != 0 else 0
            elif op == "MOD":
                res = a % b if b != 0 else 0
            elif op == "ABS":
                res = abs(a)
            elif op == "SQRT":
                res = math.sqrt(abs(a))
            else:
                res = a
            out = el.get("out", "")
            if out:
                self.set_var(out, res)
            return True
        if t == "move":
            src = self.get_var(el.get("in", ""))
            out = el.get("out", "")
            if out:
                self.set_var(out, src)
            return True
        if t == "not":
            return not bool(self.get_var(el.get("addr", "")))
        if t.startswith("and_") or t.startswith("or_") or t.startswith("xor_"):
            return False
        return False

    def eval_network(self, net: dict) -> bool:
        """Evalúa una red (rung) y devuelve el resultado (power flow)."""
        elements = net.get("elements", [])
        if not elements:
            return False
        # Evaluación simplificada: serie de contactos + bloques, paralelo con ramas
        # Estructura: {"series": [el, ...], "parallel": [[...], [...]]}
        # Si no hay estructura, evaluar linealmente
        if "series" in net:
            result = True
            for el in net["series"]:
                if isinstance(el, dict) and el.get("type", "").startswith("parallel"):
                    # rama paralela
                    branch_result = False
                    for branch in el.get("branches", []):
                        br = True
                        for be in branch:
                            br = br and self.eval_element(be)
                        branch_result = branch_result or br
                    result = result and branch_result
                else:
                    result = result and self.eval_element(el)
            return result
        # Lineal
        result = True
        for el in elements:
            result = result and self.eval_element(el)
        return result

    def execute_cycle(self):
        """Ejecuta un ciclo de scan completo."""
        start = time.time()
        # 1. Leer entradas (ya en self.I)
        # 2. Ejecutar programa OB1
        for net in self.program.get("OB1", []):
            power = self.eval_network(net)
            # 3. Escribir salidas (bobinas)
            out = net.get("output")
            if out:
                if isinstance(out, dict):
                    otype = out.get("type", "coil")
                    addr = out.get("addr", "")
                    if otype == "coil":
                        self.set_var(addr, power)
                    elif otype == "coil_set":
                        if power:
                            self.set_var(addr, True)
                    elif otype == "coil_reset":
                        if power:
                            self.set_var(addr, False)
                    elif otype == "coil_neg":
                        self.set_var(addr, not power)
                else:
                    self.set_var(out, power)
        self.cycle_count += 1
        self.cycle_time_ms = (time.time() - start) * 1000
        # Actualizar HMI outputs
        for name, addr in self.hmi_outputs.items():
            self.hmi_outputs[name] = self.get_var(addr)

    def run_continuous(self, cycles=100):
        for _ in range(cycles):
            self.execute_cycle()
            time.sleep(0.01)

    def get_state(self):
        return {
            "I": dict(self.I),
            "Q": dict(self.Q),
            "M": dict(self.M),
            "DB": {k: dict(v) for k, v in self.DB.items()},
            "T": {k: {"done": v.get("done", False), "accum": v.get("accum", 0), "preset": v.get("preset", 0)} for k, v in self.T.items()},
            "C": {k: {"count": v.get("count", 0), "done": v.get("done", False), "preset": v.get("preset", 0)} for k, v in self.C.items()},
            "cycle_count": self.cycle_count,
            "cycle_time_ms": round(self.cycle_time_ms, 2),
        }

    def save_project(self, name="project"):
        return {
            "name": name,
            "cpu": self.cpu,
            "program": self.program,
            "I": self.I, "Q": self.Q, "M": self.M, "DB": self.DB,
            "T": self.T, "C": self.C,
            "hmi_inputs": self.hmi_inputs,
            "hmi_outputs": self.hmi_outputs,
        }

    def load_project(self, data):
        self.cpu = data.get("cpu", self.cpu)
        self.program = data.get("program", {"OB1": []})
        self.I = data.get("I", {})
        self.Q = data.get("Q", {})
        self.M = data.get("M", {})
        self.DB = data.get("DB", {})
        self.T = data.get("T", {})
        self.C = data.get("C", {})
        self.hmi_inputs = data.get("hmi_inputs", {})
        self.hmi_outputs = data.get("hmi_outputs", {})
        self.cycle_count = 0
