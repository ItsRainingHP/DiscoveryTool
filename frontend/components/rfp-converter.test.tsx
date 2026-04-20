import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { RfpConverter } from "@/components/rfp-converter";

const mockResponse = {
  sourceFilename: "sample.csv",
  downloadFilename: "sample.txt",
  warnings: ["Row 7 skipped: Invalid Bates token: 'BADVALUE'."],
  sections: [
    {
      label: "RFP 01",
      ranges: ["EXAMPLE_004558-4561"],
      responsive: true,
      text: "RFP 01:\nEXAMPLE_004558-4561"
    },
    {
      label: "RFP 02",
      ranges: [],
      responsive: false,
      text: "RFP 02:\nNo responsive documents."
    }
  ],
  documentTextWithEmpty: "RFP 01:\nEXAMPLE_004558-4561\n\nRFP 02:\nNo responsive documents.",
  documentTextWithoutEmpty: "RFP 01:\nEXAMPLE_004558-4561",
  stats: {
    total_rows: 2,
    skipped_rows: 1,
    total_sections: 2,
    responsive_sections: 1
  }
};

describe("RfpConverter", () => {
  const fetchMock = vi.fn();
  const createObjectURLMock = vi.fn(() => "blob:preview");
  const revokeObjectURLMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
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
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    fetchMock.mockReset();
    createObjectURLMock.mockReset();
    revokeObjectURLMock.mockReset();
  });

  it("uploads a CSV, renders warnings, and toggles empty sections", async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => mockResponse
    });

    const user = userEvent.setup();
    render(<RfpConverter />);

    const input = screen.getByLabelText("CSV file input");
    const file = new File(["begin,end"], "sample.csv", { type: "text/csv" });
    await user.upload(input, file);
    await user.click(screen.getAllByRole("button", { name: "Convert CSV" })[0]);

    expect(fetchMock).toHaveBeenCalledTimes(1);

    await screen.findByText("Conversion summary");
    expect(screen.getByText("Conversion warnings")).toBeInTheDocument();
    expect(screen.getByText(mockResponse.warnings[0])).toBeInTheDocument();
    expect(screen.getByLabelText("Preview text")).toHaveValue(mockResponse.documentTextWithEmpty);

    await user.click(screen.getByRole("switch", { name: "Include empty sections" }));

    await waitFor(() => {
      expect(screen.getByLabelText("Preview text")).toHaveValue(mockResponse.documentTextWithoutEmpty);
    });
  });

  it("keeps convert disabled until a file is selected", () => {
    render(<RfpConverter />);

    expect(screen.getAllByRole("button", { name: "Convert CSV" })[0]).toBeDisabled();
  });

  it("links to the RFP tutorial page", () => {
    render(<RfpConverter />);

    expect(screen.getByRole("link", { name: "View tutorial" })).toHaveAttribute(
      "href",
      "/tools/rfp-csv-to-pleading/tutorial"
    );
  });
});
