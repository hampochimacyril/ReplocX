import { describe, it, expect } from "vitest";
import { toCsv, type CsvColumn } from "./csv";

interface Row {
  name: string;
  score: number;
}

const columns: CsvColumn<Row>[] = [
  { header: "name", value: (r) => r.name },
  { header: "score", value: (r) => r.score },
];

describe("toCsv", () => {
  it("writes a header row and one line per row", () => {
    const csv = toCsv([{ name: "Alpha", score: 0.9 }], columns);
    expect(csv.split("\n")).toEqual(["name,score", "Alpha,0.9"]);
  });

  it("quotes and escapes cells containing commas, quotes, or newlines", () => {
    const csv = toCsv([{ name: 'Phila, "PA"', score: 1 }], columns);
    expect(csv.split("\n")[1]).toBe('"Phila, ""PA""",1');
  });

  it("renders null/undefined as empty cells", () => {
    const cols: CsvColumn<{ a?: string }>[] = [{ header: "a", value: (r) => r.a }];
    expect(toCsv([{}], cols)).toBe("a\n");
  });
});
