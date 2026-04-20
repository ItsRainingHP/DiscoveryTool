import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { PrivilegeConverter } from "@/components/privilege-converter";

const NativeBlob = Blob;

const mockResponse = {
  sourceFilename: "priv.csv",
  downloadFilename: "priv-privilege-log.csv",
  headers: [
    "Beginning No.",
    "End No.",
    "Date",
    "Description",
    "Author",
    "Recipient(s)",
    "Privilege"
  ],
  rows: [
    [
      "EXAMPLE_003824",
      "EXAMPLE_003825",
      "1/24/2025",
      "Alpha Subject",
      "Author One",
      "To One; CC One",
      "Redacted - Attorney Client Privilege"
    ]
  ],
  csvText:
    "Beginning No.,End No.,Date,Description,Author,Recipient(s),Privilege\r\n" +
    "EXAMPLE_003824,EXAMPLE_003825,1/24/2025,Alpha Subject,Author One,To One; CC One,Redacted - Attorney Client Privilege\r\n",
  warnings: ["Row 8 Beginning Bates value 'BADVALUE' could not be normalized."],
  stats: {
    total_rows: 1,
    exported_rows: 1,
    reason_columns: 3
  }
};

describe("PrivilegeConverter", () => {
  const fetchMock = vi.fn();
  const createObjectURLMock = vi.fn(() => "blob:preview");
  const revokeObjectURLMock = vi.fn();
  let anchorClickSpy: ReturnType<typeof vi.spyOn>;
  let blobConstructorMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
    blobConstructorMock = vi.fn((parts: BlobPart[], options?: BlobPropertyBag) => {
      return new NativeBlob(parts, options);
    });
    vi.stubGlobal("Blob", blobConstructorMock as unknown as typeof Blob);
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
    anchorClickSpy = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    fetchMock.mockReset();
    createObjectURLMock.mockReset();
    revokeObjectURLMock.mockReset();
    anchorClickSpy.mockRestore();
  });

  it("uploads a CSV, renders warnings, and previews the generated CSV in a table", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => mockResponse
    });

    const user = userEvent.setup();
    render(<PrivilegeConverter />);

    const input = screen.getByLabelText("CSV file input");
    const file = new File(["begin,end"], "priv.csv", { type: "text/csv" });
    await user.upload(input, file);
    await user.click(screen.getByRole("button", { name: "Convert CSV" }));

    expect(fetchMock).toHaveBeenCalledTimes(1);

    await screen.findByText("Conversion summary");
    expect(screen.getByText("Conversion warnings")).toBeInTheDocument();
    expect(screen.getByText(mockResponse.warnings[0])).toBeInTheDocument();
    expect(
      screen.getByText(
        "Review this privilege log and redact any privileged names before using or sharing it."
      )
    ).toBeInTheDocument();
    expect(screen.getByRole("table", { name: "Preview CSV" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "Beginning No." })).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "Alpha Subject" })).toBeInTheDocument();
  });

  it("shows API errors returned by the converter endpoint", async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      json: async () => ({
        detail:
          "Row 5 [EXAMPLE003847]-[EXAMPLE003847] must include at least one privilege reason marked TRUE."
      })
    });

    const user = userEvent.setup();
    render(<PrivilegeConverter />);

    const input = screen.getByLabelText("CSV file input");
    const file = new File(["begin,end"], "priv.csv", { type: "text/csv" });
    await user.upload(input, file);
    await user.click(screen.getByRole("button", { name: "Convert CSV" }));

    await screen.findByText(
      "Row 5 [EXAMPLE003847]-[EXAMPLE003847] must include at least one privilege reason marked TRUE."
    );
  });

  it("downloads the generated CSV preview", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => mockResponse
    });

    const user = userEvent.setup();
    render(<PrivilegeConverter />);

    const input = screen.getByLabelText("CSV file input");
    const file = new File(["begin,end"], "priv.csv", { type: "text/csv" });
    await user.upload(input, file);
    await user.click(screen.getByRole("button", { name: "Convert CSV" }));

    await screen.findByText("Conversion summary");
    await user.click(screen.getByRole("button", { name: "Download CSV" }));

    await waitFor(() => {
      expect(createObjectURLMock).toHaveBeenCalledTimes(1);
    });

    expect(blobConstructorMock).toHaveBeenCalledWith([mockResponse.csvText], {
      type: "text/csv;charset=utf-8"
    });
    expect(revokeObjectURLMock).toHaveBeenCalledTimes(1);
  });
});
