import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  convertPrivilegeCsv,
  convertRfpCsv,
  downloadCsvFile,
  downloadTextFile,
  type ConversionResponse,
  type PrivilegeConversionResponse
} from "@/lib/api";

const conversionResponse: ConversionResponse = {
  sourceFilename: "sample.csv",
  downloadFilename: "sample.txt",
  warnings: [],
  sections: [],
  documentTextWithEmpty: "",
  documentTextWithoutEmpty: "",
  stats: { total_rows: 0, skipped_rows: 0, total_sections: 0, responsive_sections: 0 }
};

const privilegeResponse: PrivilegeConversionResponse = {
  sourceFilename: "sample.csv",
  downloadFilename: "sample-privilege-log.csv",
  headers: [],
  rows: [],
  csvText: "",
  warnings: [],
  stats: { total_rows: 0, exported_rows: 0, reason_columns: 0 }
};

function makeFile(name = "sample.csv") {
  return new File(["a,b,c"], name, { type: "text/csv" });
}

describe("convertRfpCsv", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it("posts the file as multipart form data to the default base URL", async () => {
    fetchMock.mockResolvedValue({ ok: true, json: async () => conversionResponse });

    await convertRfpCsv(makeFile());

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/rfp/convert");
    expect((init as RequestInit).method).toBe("POST");
    const body = (init as RequestInit).body as FormData;
    expect(body).toBeInstanceOf(FormData);
    expect(body.get("file")).toBeInstanceOf(File);
  });

  it("strips a trailing slash from NEXT_PUBLIC_API_BASE_URL", async () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "https://example.test/api/";
    fetchMock.mockResolvedValue({ ok: true, json: async () => conversionResponse });

    await convertRfpCsv(makeFile());

    expect(fetchMock.mock.calls[0][0]).toBe("https://example.test/api/rfp/convert");
  });

  it("returns the parsed JSON body on success", async () => {
    fetchMock.mockResolvedValue({ ok: true, json: async () => conversionResponse });

    await expect(convertRfpCsv(makeFile())).resolves.toEqual(conversionResponse);
  });

  it("throws with the API detail when the response is not ok", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      json: async () => ({ detail: "The uploaded CSV is empty." })
    });

    await expect(convertRfpCsv(makeFile())).rejects.toThrow("The uploaded CSV is empty.");
  });

  it("falls back to the default error message when the body is not JSON", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      json: async () => {
        throw new SyntaxError("not json");
      }
    });

    await expect(convertRfpCsv(makeFile())).rejects.toThrow("The CSV could not be converted.");
  });

  it("falls back to the default error message when detail is missing", async () => {
    fetchMock.mockResolvedValue({ ok: false, json: async () => ({}) });

    await expect(convertRfpCsv(makeFile())).rejects.toThrow("The CSV could not be converted.");
  });
});

describe("convertPrivilegeCsv", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it("posts to the privilege endpoint and returns parsed JSON", async () => {
    fetchMock.mockResolvedValue({ ok: true, json: async () => privilegeResponse });

    const result = await convertPrivilegeCsv(makeFile());

    expect(fetchMock.mock.calls[0][0]).toBe("/api/privilege/convert");
    expect(result).toEqual(privilegeResponse);
  });

  it("throws with the API detail when the response is not ok", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      json: async () => ({ detail: "Row 2 must have exactly one ..." })
    });

    await expect(convertPrivilegeCsv(makeFile())).rejects.toThrow(
      "Row 2 must have exactly one ..."
    );
  });

  it("falls back to the default error when the body is not JSON", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      json: async () => {
        throw new Error("boom");
      }
    });

    await expect(convertPrivilegeCsv(makeFile())).rejects.toThrow(
      "The CSV could not be converted."
    );
  });
});

describe("download helpers", () => {
  const createObjectURLMock = vi.fn(() => "blob:preview");
  const revokeObjectURLMock = vi.fn();
  const clickMock = vi.fn();

  beforeEach(() => {
    Object.defineProperty(globalThis.URL, "createObjectURL", {
      configurable: true,
      writable: true,
      value: createObjectURLMock
    });
    Object.defineProperty(globalThis.URL, "revokeObjectURL", {
      configurable: true,
      writable: true,
      value: revokeObjectURLMock
    });
    HTMLAnchorElement.prototype.click = clickMock;
  });

  afterEach(() => {
    createObjectURLMock.mockReset();
    revokeObjectURLMock.mockReset();
    clickMock.mockReset();
  });

  it("downloads text content with a text/plain blob", () => {
    downloadTextFile("output.txt", "hello world");

    expect(createObjectURLMock).toHaveBeenCalledTimes(1);
    const blob = createObjectURLMock.mock.calls[0][0] as Blob;
    expect(blob.type).toBe("text/plain;charset=utf-8");
    expect(blob.size).toBe("hello world".length);
    expect(clickMock).toHaveBeenCalledTimes(1);
    expect(revokeObjectURLMock).toHaveBeenCalledWith("blob:preview");
  });

  it("downloads CSV content with a text/csv blob", () => {
    const csv = "a,b\n1,2\n";
    downloadCsvFile("output.csv", csv);

    const blob = createObjectURLMock.mock.calls[0][0] as Blob;
    expect(blob.type).toBe("text/csv;charset=utf-8");
    expect(blob.size).toBe(csv.length);
    expect(clickMock).toHaveBeenCalledTimes(1);
  });
});
