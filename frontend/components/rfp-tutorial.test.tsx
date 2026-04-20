import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { RfpTutorial } from "@/components/rfp-tutorial";

describe("RfpTutorial", () => {
  it("renders markdown content and tutorial screenshots", () => {
    render(
      <RfpTutorial
        markdown={`# Tutorial\n\n## Step 1\n\nFollow the process.\n\n![Example](/images/rfp/example.png)`}
      />
    );

    expect(screen.getByRole("heading", { name: "Prepare a converter-ready RFP CSV export." })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Tutorial" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Step 1" })).toBeInTheDocument();
    expect(screen.getByAltText("Example")).toHaveAttribute("src", "/images/rfp/example.png");
    expect(screen.getByRole("link", { name: "Back to converter" })).toHaveAttribute(
      "href",
      "/tools/rfp-csv-to-pleading"
    );
  });
});
