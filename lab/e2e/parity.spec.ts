/**
 * Numerical parity between the legacy dashboards and the research lab.
 * The legacy page makes a request; the lab replays the same request (same seed). Both backends run the
 * same code, so the responses must be identical, and both pages must display the same values.
 */
import { expect, test, type Page, type Response } from "@playwright/test";
import { LEGACY_AEGIS, LEGACY_SIM } from "../playwright.config";

const json = async (r: Response) => (await r.json()) as any; // eslint-disable-line @typescript-eslint/no-explicit-any
const api = (page: Page, path: string, method = "POST") =>
  page.waitForResponse((r) => r.url().includes(path) && r.request().method() === method && r.status() === 200, { timeout: 120_000 });
const digits = (s: string) => s.replace(/[^0-9]/g, "");

test("8000 → lab: error injection, circuit diagram and compiled metrics agree", async ({ page, browser }) => {
  const legacy = await browser.newPage();
  await legacy.goto(LEGACY_SIM + "/");
  await expect(legacy.getByTestId("overhead")).toBeVisible({ timeout: 120_000 });     // compiled metrics loaded
  const oldResp = api(legacy, "/api/simulate/injection");
  await legacy.getByTestId("run-injection").click();
  const r = await json(await oldResp);
  const old = {
    fired: (await legacy.getByTestId("inj-fired").textContent())!.trim(), outcome: (await legacy.getByTestId("inj-outcome").textContent())!.trim(),
    after: (await legacy.getByTestId("inj-after").textContent())!.trim(), depth: (await legacy.getByTestId("m-depth").textContent())!.trim(),
    twoq: (await legacy.getByTestId("m-2q").textContent())!.trim(), overhead: (await legacy.getByTestId("overhead").textContent())!.trim(),
    errors: await legacy.getByTestId("circuit-error").count(),
  };
  expect(r.request).toMatchObject({ code: "repetition", basis: "Z", distance: 3 });

  await page.goto("/error-correction");
  await page.getByTestId("bench-d").getByRole("radio", { name: "3" }).click();
  const info = await (await page.request.get(`/api/sim/circuit?code=repetition&basis=Z&distance=3&rounds=${r.request.rounds}`)).json();
  const index = info.layout.data_qubits.indexOf(r.request.qubit);
  await page.getByTestId("bench-tool").getByRole("radio", { name: r.request.error_type }).click();
  await page.getByTestId(`qubit-${index}`).click();
  await page.getByTestId("sim-rounds").selectOption(String(r.request.rounds));
  await page.getByTestId("sim-boundary").selectOption(String(r.request.boundary));
  await page.getByTestId("sim-shots").fill(String(r.request.shots));
  await page.getByTestId("sim-seed").fill(String(r.seed));
  const newResp = api(page, "/api/sim/simulate/injection");
  await page.getByTestId("sim-run-button").click();
  const r2 = await json(await newResp);
  expect({ ...r2.request, seed: null }).toEqual({ ...r.request, seed: null });
  expect(r2.syndrome).toEqual(r.syndrome);
  expect(r2.logical).toEqual(r.logical);
  expect(r2.circuit.drawing).toEqual(r.circuit.drawing);
  await expect(page.getByTestId("sim-fired")).toHaveText(old.fired);
  await expect(page.getByTestId("sim-outcome")).toHaveText(old.outcome);
  await expect(page.getByTestId("sim-after")).toContainText(`${old.after} / ${r.logical.shots}`);
  await expect(page.getByTestId("cm-depth")).toHaveText(old.depth);
  await expect(page.getByTestId("cm-2q")).toHaveText(old.twoq);
  await expect(page.getByTestId("cm-overhead")).toHaveText(old.overhead);
  await expect(page.getByTestId("circuit").getByTestId("circuit-error")).toHaveCount(old.errors);
  await expect(page.getByTestId("sim-raw")).toHaveText((await legacy.getByTestId("inj-first-shot").textContent())!.trim());
  await legacy.close();
});

test("8765 → lab: the same Gross-code shot decodes identically and shows the same router features", async ({ page, browser }) => {
  const legacy = await browser.newPage();
  await legacy.goto(LEGACY_AEGIS + "/");
  await legacy.locator("#seed").fill("7");
  await legacy.locator("#basis").selectOption("X");
  await legacy.locator("#p").selectOption("0.004");
  const oldResp = api(legacy, "/api/decode");
  await legacy.locator("#run").click();
  const r = await json(await oldResp);
  const oldRows = await legacy.locator("#decoders tbody tr").allTextContents();

  await page.goto("/experiments");
  await page.getByTestId("g-seed").fill("7");
  const newResp = api(page, "/api/aegis/decode");
  await page.getByTestId("g-run").click();
  const r2 = await json(await newResp);
  expect(r2.syndrome).toEqual(r.syndrome);
  expect(r2.true_observables).toEqual(r.true_observables);
  expect(Object.keys(r2.decoders).sort()).toEqual(Object.keys(r.decoders).sort());
  for (const [name, d] of Object.entries<any>(r.decoders)) {
    expect(r2.decoders[name].predicted_observables).toEqual(d.predicted_observables);
    expect(r2.decoders[name].bp_iterations).toBe(d.bp_iterations);
    const oldRow = oldRows.find((t) => t.startsWith(name))!;
    expect(oldRow).toContain(d.logical_correct ? "correct" : "logical error");
    await expect(page.getByTestId(`g-outcome-${name}`)).toHaveText(d.logical_correct ? "correct" : "logical error");
    await expect(page.getByTestId(`g-iter-${name}`)).toHaveText(String(d.bp_iterations));
  }
  expect(r2.features).toEqual(r.features);
  expect(r2.routing.path).toBe(r.routing.path);
  // Every feature the legacy page listed is listed by the lab, with the same value.
  const oldFeatures = await legacy.locator("#features > div").count();
  await page.goto("/decoders");
  await page.getByTestId("ld-seed").fill("7");
  const third = api(page, "/api/aegis/decode");
  await page.getByTestId("ld-run").click();
  const r3 = await json(await third);
  expect(r3.features).toEqual(r.features);
  await expect(page.getByTestId("ld-features").locator("[data-testid^=feat-]")).toHaveCount(oldFeatures);
  await expect(page.getByTestId("ld-threshold")).toHaveText(r.routing.threshold.toPrecision(4));
  await legacy.close();
});

test("8765 → lab: decoder studies show the same numbers", async ({ page, browser }) => {
  const legacy = await browser.newPage();
  const resultsResp = legacy.waitForResponse((r) => r.url().endsWith("/api/results"));
  await legacy.goto(LEGACY_AEGIS + "/");
  const res = await json(await resultsResp);
  const oldText = await legacy.locator("#results").textContent();
  await page.goto("/decoders");
  for (const [i, s] of res.studies.entries()) {
    await page.getByTestId("paired-outcomes").getByTestId("study-p").getByRole("radio", { name: new RegExp(`p = ${s.p}`) }).click();
    const k = s.paired_outcomes_bposd_relay["relay correct, bposd wrong"].shots;
    expect(oldText).toContain(String(k));
    await expect(page.getByTestId("po-relay-correct-bposd-wrong")).toHaveText(k.toLocaleString("en-US"));
    await page.getByTestId("routing-rules").getByTestId("study-p").getByRole("radio", { name: new RegExp(`p = ${s.p}`) }).click();
    for (const rule of ["fast -> relay", "relay1 -> relay", "bp200 -> strong10"]) {
      const bound = s.rule_based[`${rule} (perfect router)`];
      if (!bound) continue;
      // The legacy page renders one rules table per study, in the API's order: row i belongs to study i.
      const legacyRow = legacy.locator("#results tr", { hasText: `${rule} (perfect router)` }).nth(i);
      await expect(legacyRow.locator("td").nth(2)).toHaveText(String(bound.failures_pair));
      await expect(legacyRow).toContainText(String(bound.failures_pair));
      await expect(page.getByTestId(`rule-bound-${rule}`)).toContainText(`${bound.failures_pair} ·`);
    }
  }
  const pre = res.predecoder;
  for (const [k, v] of Object.entries<any>(pre.results)) {
    expect(oldText).toContain(String(v.failed));
    await expect(page.getByTestId(`pre-${k.replace(" ", "-")}`)).toHaveText(String(v.failed));
  }
  await legacy.close();
});

test("8000 → lab: archived hardware panel shows the same numbers", async ({ page, browser }) => {
  const legacy = await browser.newPage();
  await legacy.goto(LEGACY_SIM + "/");
  const panel = legacy.getByTestId("hardware");
  await expect(panel).toContainText("ibm_kingston");
  const oldText = (await panel.textContent())!;
  await page.goto("/hardware");
  for (const id of ["hw-raw", "hw-decoded", "hw-ff"]) {
    const v = (await page.getByTestId(id).textContent())!;
    const [a, b] = v.split("/").map(digits);
    expect(oldText.replace(/,/g, "")).toContain(`${a} / ${b}`);
  }
  await expect(page.getByTestId("hw-job")).toHaveText("dc0kvf2nj2vs73de5qvg");
  expect(oldText).toContain("dc0kvf2nj2vs73de5qvg");
  await legacy.close();
});
