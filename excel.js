// Requires: npm install xlsx
// Usage: node excel.js

const path = require("path");
const xlsx = require("xlsx");

// ===================== Config =====================
// Use a Windows path or relative path.
const EXCEL_FILE_PATH = "F:\\Desktop\\顶流降临打卡收集表（收集结果）\\顶流降临打卡收集表（收集结果）.xlsx";

const SHEET_NAME = "sheet1";

// ===================== Target rows =====================
const targetRows1 = [
  569, 568, 567, 566, 563, 562, 559, 557, 556, 554, 552, 551, 550, 549, 548, 547, 546,
  542, 541, 540, 539, 537, 535, 533, 532, 530, 529, 528, 527, 526, 525, 524, 522, 521,
  520, 518, 516, 515, 512, 510, 509, 508, 504, 501, 498, 497, 496, 495, 493, 492, 491,
  490, 489, 488, 487, 486, 484, 483, 482, 480, 479, 478, 476, 475, 471, 469, 468, 467,
  465, 464, 463, 462, 460, 458, 455, 452, 449, 448, 441, 439, 438, 437, 436, 435, 433,
  432, 430, 427, 425, 424, 422, 421, 420, 419, 416, 415, 414, 411, 407, 406, 405, 404,
  403, 401, 400, 399, 394, 393, 392, 391, 390, 388, 385, 384, 381, 379, 376, 375, 374,
  373, 372, 370, 369, 368, 367, 366, 365, 364, 363, 361, 360, 358, 356, 355, 353, 352,
  350, 349, 348, 345, 344, 343, 342, 341, 340, 339, 338, 337, 336, 329, 328, 327, 326,
  325, 323, 322, 320, 317, 314, 313, 311, 309, 308, 301, 299, 298, 297, 296, 295, 291,
  290, 287, 286, 284, 283, 282, 281, 280,
];

const targetRows2 = [
  565, 553, 544, 543, 517, 513, 511, 503, 502, 485, 481, 473, 472, 470, 466, 461, 456,
  454, 453, 450, 446, 445, 442, 434, 431, 423, 417, 413, 412, 409, 408, 389, 382, 380,
  347, 335, 319, 316, 312, 310, 307, 303, 300, 288,
];

function getCellValue(sheet, address) {
  const cell = sheet[address];
  return cell ? cell.v : null;
}

function extractFColumn(filePath, sheetName, rows) {
  const wb = xlsx.readFile(filePath, { cellDates: true });
  const sheet = wb.Sheets[sheetName];
  if (!sheet) {
    throw new Error(`Sheet not found: ${sheetName}`);
  }

  return rows.map((row) => getCellValue(sheet, `F${row}`));
}

function buildOutputWorkbook(rows1, data1, rows2, data2) {
  const outWb = xlsx.utils.book_new();

  const ws1Data = [["Row", "F Value"]];
  rows1.forEach((row, idx) => ws1Data.push([row, data1[idx]]));
  const ws1 = xlsx.utils.aoa_to_sheet(ws1Data);
  xlsx.utils.book_append_sheet(outWb, ws1, "Group1_Row_F");

  const ws2Data = [["Row", "F Value"]];
  rows2.forEach((row, idx) => ws2Data.push([row, data2[idx]]));
  const ws2 = xlsx.utils.aoa_to_sheet(ws2Data);
  xlsx.utils.book_append_sheet(outWb, ws2, "Group2_Row_F");

  return outWb;
}

function main() {
  const data1 = extractFColumn(EXCEL_FILE_PATH, SHEET_NAME, targetRows1);
  const data2 = extractFColumn(EXCEL_FILE_PATH, SHEET_NAME, targetRows2);

  console.log("=== Group 1 - F column values (by row order) ===");
  console.dir(data1, { maxArrayLength: null });
  console.log("\n=== Group 2 - F column values (by row order) ===");
  console.dir(data2, { maxArrayLength: null });

  const outWb = buildOutputWorkbook(targetRows1, data1, targetRows2, data2);
  const outPath = path.resolve("extracted_f_values.xlsx");
  xlsx.writeFile(outWb, outPath);
  console.log(`\nDone. Saved: ${outPath}`);
}

main();
