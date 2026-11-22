import { describe, expect, it } from "vitest";
import { BELL, GATES, apply, applyChannel, bloch, corr, kron, PAULI1, stateFromAngles, whichBell, probPlus, I2 } from "@/lib/quantum";

const close = (a: number, b: number, eps = 1e-12) => expect(Math.abs(a - b)).toBeLessThan(eps);

describe("single qubit", () => {
  it("Bloch vector of cos(t/2)|0> + e^{ip} sin(t/2)|1>", () => {
    const t = 1.1, p = 2.3, r = bloch(stateFromAngles(t, p));
    close(r[0], Math.sin(t) * Math.cos(p)); close(r[1], Math.sin(t) * Math.sin(p)); close(r[2], Math.cos(t));
  });
  it("Paulis rotate the Bloch vector by pi", () => {
    const r = bloch(stateFromAngles(0.7, 0.4));
    const rx = bloch(apply(GATES.X, stateFromAngles(0.7, 0.4)));
    const ry = bloch(apply(GATES.Y, stateFromAngles(0.7, 0.4)));
    const rz = bloch(apply(GATES.Z, stateFromAngles(0.7, 0.4)));
    [[rx, [r[0], -r[1], -r[2]]], [ry, [-r[0], r[1], -r[2]]], [rz, [-r[0], -r[1], r[2]]]].forEach(([a, b]) => a.forEach((x, i) => close(x, b[i])));
  });
  it("Hadamard maps |0> to |+>", () => {
    const r = bloch(apply(GATES.H, stateFromAngles(0, 0)));
    close(r[0], 1); close(r[2], 0); close(probPlus(r, "X"), 1); close(probPlus(r, "Z"), 0.5);
  });
});

describe("Bell states", () => {
  it("stabilizers of Phi+ are XX = +1, ZZ = +1, YY = -1, local Paulis average to 0", () => {
    const v = BELL["Φ+"];
    close(corr(v, "X", "X"), 1); close(corr(v, "Z", "Z"), 1); close(corr(v, "Y", "Y"), -1);
    close(corr(v, "Z", "I"), 0); close(corr(v, "X", "I"), 0);
  });
  it("X on A flips ZZ, Z on A flips XX, Y flips both", () => {
    const XA = kron(PAULI1.X, I2), ZA = kron(PAULI1.Z, I2), YA = kron(PAULI1.Y, I2);
    expect(whichBell(apply(XA, BELL["Φ+"]))).toBe("Ψ+");
    expect(whichBell(apply(ZA, BELL["Φ+"]))).toBe("Φ−");
    expect(whichBell(apply(YA, BELL["Φ+"]))).toBe("Ψ−");
    close(corr(apply(XA, BELL["Φ+"]), "Z", "Z"), -1); close(corr(apply(ZA, BELL["Φ+"]), "X", "X"), -1);
  });
});

describe("channels", () => {
  it("depolarizing shrinks the Bloch vector by 1 - 4p/3", () => {
    const r = applyChannel("depolarizing", 0.3, [0, 0, 1]); close(r[2], 1 - 0.4);
  });
  it("amplitude damping drives every state to |0>", () => {
    const r = applyChannel("amplitude-damping", 0.2, [1, 0, 0], 200); close(r[2], 1, 1e-9); close(r[0], 0, 1e-9);
  });
  it("bit flip leaves x alone and scales y, z", () => {
    const r = applyChannel("bit-flip", 0.1, [0.6, 0, 0.8]); close(r[0], 0.6); close(r[2], 0.8 * 0.8);
  });
});
