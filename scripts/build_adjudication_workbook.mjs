import fs from "node:fs/promises";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";

const root = "D:/LLM-Knowledge-Graph";
const csvPath = `${root}/outputs/adjudication/per_paper_adjudication_ai_draft.csv`;
const outDir = `${root}/outputs/adjudication`;
const outXlsx = `${outDir}/Richmond_Per_Paper_Adjudication_AI_Draft.xlsx`;

const csvText = await fs.readFile(csvPath, "utf8");
const workbook = await Workbook.fromCSV(csvText, { sheetName: "Adjudication_Draft" });

const draft = workbook.worksheets.getItem("Adjudication_Draft");
draft.freezePanes.freezeRows(1);
draft.showGridLines = false;
draft.getRange("A1:AK1").format = {
  fill: "#1F4E79",
  font: { bold: true, color: "#FFFFFF" },
  wrapText: true,
};
draft.getRange("A1:AK58").format.borders = {
  preset: "all",
  style: "thin",
  color: "#D9E2F3",
};

const widths = {
  A: 70, B: 110, C: 260, D: 80, E: 80, F: 80, G: 170, H: 110,
  I: 145, J: 145, K: 145, L: 145, M: 145, N: 145, O: 145, P: 145,
  Q: 145, R: 145, S: 360, T: 120, U: 120, V: 120, W: 120, X: 90,
  Y: 120, Z: 120, AA: 120, AB: 120, AC: 120, AD: 280, AE: 200,
  AF: 120, AG: 240, AH: 110, AI: 95, AJ: 190, AK: 380,
};
for (const [column, widthPx] of Object.entries(widths)) {
  draft.getRange(`${column}:${column}`).format.columnWidthPx = widthPx;
}
draft.getRange("A1:AK58").format = {
  wrapText: true,
  verticalAlignment: "top",
};
try {
  draft.tables.add("A1:AK58", true, "AdjudicationDraftTable");
} catch {}

const summary = workbook.worksheets.add("Summary");
summary.showGridLines = false;
summary.getRange("A1:H1").merge();
summary.getRange("A1").values = [["Richmond Per-Paper Adjudication - AI Draft"]];
summary.getRange("A1").format = {
  fill: "#1F4E79",
  font: { bold: true, color: "#FFFFFF", size: 16 },
  horizontalAlignment: "center",
};
summary.getRange("A3:B10").values = [
  ["Metric", "Value"],
  ["Rows / CMOCs", 57],
  ["Studies", 28],
  ["Full-text rows", 39],
  ["Abstract-only rows", 16],
  ["Partial full-text rows", 2],
  ["AI accept ready for human signoff", 15],
  ["Rows requiring review", 42],
];
summary.getRange("A3:B3").format = { fill: "#D9EAF7", font: { bold: true } };
summary.getRange("A3:B10").format.borders = {
  preset: "all",
  style: "thin",
  color: "#BFBFBF",
};
summary.getRange("A:A").format.columnWidthPx = 310;
summary.getRange("B:B").format.columnWidthPx = 130;
summary.getRange("D3:E7").values = [
  ["Review Priority", "Count"],
  ["HIGH", 26],
  ["MEDIUM", 16],
  ["LOW", 15],
  ["Total", 57],
];
summary.getRange("D3:E3").format = { fill: "#D9EAF7", font: { bold: true } };
summary.getRange("D3:E7").format.borders = {
  preset: "all",
  style: "thin",
  color: "#BFBFBF",
};
summary.getRange("D:E").format.columnWidthPx = 150;
summary.getRange("A12:H18").values = [
  ["Important Note"],
  ["This workbook is AI-assisted adjudication draft, not final human gold standard."],
  ["Use LOW priority rows for quick sign-off checks, then review HIGH priority rows carefully."],
  ["The human_corrected_* columns are prefilled suggestions and must be confirmed by a researcher."],
  ["Abstract-only and partial full-text rows remain provisional until full text is checked."],
  ["After review, this file can become the per-paper gold standard for refinement."],
  [""],
];
summary.getRange("A12:H18").merge(true);
summary.getRange("A12:H18").format = {
  fill: "#FFF2CC",
  wrapText: true,
  verticalAlignment: "top",
};

const dictionary = workbook.worksheets.add("Data_Dictionary");
dictionary.showGridLines = false;
dictionary.getRange("A1:C1").values = [["Column group", "Meaning", "Action for human reviewer"]];
dictionary.getRange("A1:C1").format = {
  fill: "#1F4E79",
  font: { bold: true, color: "#FFFFFF" },
};
dictionary.getRange("A2:C10").values = [
  ["model_*", "Original AI extraction from evidence_table.json", "Use as baseline; do not treat as gold automatically"],
  ["quote_support_*", "Whether source text contains the cited evidence quote", "Check rows marked not_found or approximate"],
  ["human_corrected_*", "AI draft correction columns prefilled for review", "Edit these to create final human gold"],
  ["decision_status", "Draft status assigned by automatic checks", "Only human can convert draft to approved gold"],
  ["review_priority", "LOW/MEDIUM/HIGH triage label", "Start with HIGH priority rows"],
  ["error_category", "Reasons a row needs review", "Use for prompt/schema refinement later"],
  ["evidence_level", "Full-text, Abstract Only, or Partial Full-text", "Treat non-full-text rows as provisional"],
  ["ai_adjudication_confidence", "Heuristic confidence based on quote support and chain checks", "Do not report as final accuracy"],
  ["reviewer_notes", "Audit note explaining why row was accepted or flagged", "Replace/add human reasoning after review"],
];
dictionary.getRange("A:C").format.columnWidthPx = 260;
dictionary.getRange("A1:C10").format = {
  wrapText: true,
  verticalAlignment: "top",
};
dictionary.getRange("A1:C10").format.borders = {
  preset: "all",
  style: "thin",
  color: "#BFBFBF",
};

await fs.mkdir(outDir, { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outXlsx);
console.log(outXlsx);
