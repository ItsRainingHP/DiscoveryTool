import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ToolDashboard } from "@/components/tool-dashboard";

describe("ToolDashboard", () => {
  it("renders both tool cards with navigation links", () => {
    render(<ToolDashboard />);

    expect(screen.getByRole("heading", { name: "RFP CSV to Pleading" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Privilege Log Preparation" })).toBeInTheDocument();
    const converterLinks = screen.getAllByRole("link", { name: "Open converter" });

    expect(converterLinks[0]).toHaveAttribute(
      "href",
      "/tools/rfp-csv-to-pleading"
    );
    expect(converterLinks[1]).toHaveAttribute(
      "href",
      "/tools/privilege-log"
    );
  });
});
