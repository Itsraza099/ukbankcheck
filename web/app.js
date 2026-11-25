"use strict";

// The in-browser batch checker. Python (Pyodide) runs ukbankcheck.batch.check_rows, the
// same code the CLI uses, on files read locally. Nothing is uploaded.

const PYTHON_GLUE = `
import json
from ukbankcheck import ModulusTables, TableFormatError
from ukbankcheck.batch import BatchError, OUTCOME_ORDER, check_rows

def run(csv_text, weights, subs):
    try:
        tables = ModulusTables.from_text(weights, subs)
    except TableFormatError as exc:
        return json.dumps({"error": f"The rules file isn't in Vocalink's format: {exc}"})
    try:
        result = check_rows(csv_text, tables)
    except BatchError as exc:
        return json.dumps({"error": str(exc).capitalize() + "."})
    return json.dumps({
        "columns": result.columns,
        "rows": result.rows,
        "summary": {o: result.summary[o] for o in OUTCOME_ORDER},
        "csv": result.to_csv(),
    })
`;

const LABELS = {
  valid: "Valid",
  invalid: "Invalid",
  not_checked: "Not checked",
  foreign_currency: "Foreign currency",
  needs_review: "Needs review",
  bad_format: "Bad format",
};
const MAX_TABLE_ROWS = 500;

const $ = (id) => document.getElementById(id);
const state = { run: null, csvText: null, csvName: null, result: null, filter: "all" };

function setStatus(text, isError = false) {
  $("status").textContent = text;
  $("status").classList.toggle("error", isError);
}

function updateRunButton() {
  $("run").disabled = !(state.run && state.csvText);
}

async function fetchText(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`couldn't load ${path} (${response.status})`);
  return response.text();
}

async function startPython() {
  try {
    const pyodide = await loadPyodide();
    await pyodide.loadPackage("micropip");
    // The deploy workflow builds the wheel from the same commit as this page and lists
    // its filename in wheel.json, so the page always runs the code it was tested with.
    const { file } = JSON.parse(await fetchText("wheel.json"));
    const micropip = pyodide.pyimport("micropip");
    await micropip.install(new URL(file, location.href).href);
    pyodide.runPython(PYTHON_GLUE);
    state.run = pyodide.globals.get("run");
    setStatus(state.csvText ? "Ready." : "Ready. Add a CSV to check.");
  } catch (error) {
    setStatus(`Couldn't start Python: ${error.message}`, true);
  }
  updateRunButton();
}

function setData(text, name) {
  state.csvText = text;
  state.csvName = name;
  $("drop").classList.add("has-file");
  $("drop-label").textContent = `${name} — ${text.split(/\r?\n/).filter(Boolean).length - 1} rows`;
  updateRunButton();
}

async function readRules() {
  if (document.querySelector('input[name="mode"]:checked').value === "demo") {
    return [await fetchText("demo/valacdos.txt"), await fetchText("demo/scsubtab.txt")];
  }
  const weights = $("weights-file").files[0];
  const subs = $("subs-file").files[0];
  if (!weights || !subs) throw new Error("Choose both Vocalink files in step 1.");
  return [await weights.text(), await subs.text()];
}

async function runCheck() {
  $("run").disabled = true;
  setStatus("Checking…");
  try {
    const [weights, subs] = await readRules();
    const result = JSON.parse(state.run(state.csvText, weights, subs));
    if (result.error) throw new Error(result.error);
    state.result = result;
    state.filter = "all";
    renderResults();
    const total = result.rows.length;
    setStatus(`Checked ${total.toLocaleString()} row${total === 1 ? "" : "s"}.`);
  } catch (error) {
    setStatus(error.message, true);
  }
  updateRunButton();
}

function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  Object.assign(node, props);
  for (const child of children) node.append(child);
  return node;
}

function renderResults() {
  const { summary, rows } = state.result;
  $("results").hidden = false;

  $("summary").replaceChildren(
    ...Object.entries(summary)
      .filter(([, n]) => n > 0)
      .map(([outcome, n]) =>
        el("div", { className: "tile" }, [
          el("span", { className: `n o-${outcome}`, textContent: n.toLocaleString() }),
          el("span", { className: "label", textContent: LABELS[outcome] }),
        ]),
      ),
  );

  const options = [["all", `All (${rows.length})`]].concat(
    Object.entries(summary)
      .filter(([, n]) => n > 0)
      .map(([o, n]) => [o, `${LABELS[o]} (${n})`]),
  );
  $("filters").replaceChildren(
    ...options.map(([value, text]) => {
      const button = el("button", { type: "button", textContent: text });
      button.setAttribute("aria-pressed", String(state.filter === value));
      button.addEventListener("click", () => {
        state.filter = value;
        renderResults();
      });
      return button;
    }),
  );
  renderTable();
}

function renderTable() {
  const { columns, rows } = state.result;
  const shown = rows.filter((r) => state.filter === "all" || r.outcome === state.filter);
  const visible = shown.slice(0, MAX_TABLE_ROWS);

  const head = el("thead", {}, [el("tr", {}, columns.map((c) => el("th", { textContent: c })))]);
  const body = el(
    "tbody",
    {},
    visible.map((row) =>
      el(
        "tr",
        {},
        columns.map((c) => {
          if (c === "outcome") {
            return el("td", {}, [
              el("span", { className: `badge o-${row[c]}`, textContent: LABELS[row[c]] ?? row[c] }),
            ]);
          }
          return el("td", { className: c === "reason" ? "reason" : "", textContent: row[c] ?? "" });
        }),
      ),
    ),
  );
  $("table").replaceChildren(head, body);
  $("table-note").textContent =
    shown.length > MAX_TABLE_ROWS
      ? `Showing the first ${MAX_TABLE_ROWS} of ${shown.length.toLocaleString()} rows. The download has all of them.`
      : "";
}

function downloadResults() {
  // Prepend a byte-order mark so Excel opens the file as UTF-8.
  const blob = new Blob(["﻿", state.result.csv], { type: "text/csv;charset=utf-8" });
  const link = el("a", {
    href: URL.createObjectURL(blob),
    download: (state.csvName || "bank-details").replace(/\.csv$/i, "") + "-checked.csv",
  });
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
}

function wireUp() {
  for (const radio of document.querySelectorAll('input[name="mode"]')) {
    radio.addEventListener("change", () => {
      const real = radio.value === "real" && radio.checked;
      $("real-files").hidden = !real;
      $("demo-note").hidden = real;
    });
  }

  $("data-file").addEventListener("change", async (event) => {
    const file = event.target.files[0];
    if (file) setData(await file.text(), file.name);
  });

  const drop = $("drop");
  drop.addEventListener("dragover", (event) => {
    event.preventDefault();
    drop.classList.add("over");
  });
  drop.addEventListener("dragleave", () => drop.classList.remove("over"));
  drop.addEventListener("drop", async (event) => {
    event.preventDefault();
    drop.classList.remove("over");
    const file = event.dataTransfer.files[0];
    if (file) setData(await file.text(), file.name);
  });
  drop.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      $("data-file").click();
    }
  });

  $("sample").addEventListener("click", async () => {
    setData(await fetchText("demo/sample.csv"), "sample.csv");
  });
  $("run").addEventListener("click", runCheck);
  $("download").addEventListener("click", downloadResults);
}

wireUp();
startPython();
