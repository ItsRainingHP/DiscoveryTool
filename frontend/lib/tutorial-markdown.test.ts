import { describe, expect, it } from "vitest";

import { normalizeTutorialMarkdown } from "@/lib/tutorial-markdown";

describe("normalizeTutorialMarkdown", () => {
  it("rewrites frontend public asset references to browser paths", () => {
    const markdown =
      "![Screenshot](frontend/public/images/rfp/example.png)\n\n[Asset](./frontend/public/files/example.txt)";

    expect(normalizeTutorialMarkdown(markdown)).toBe(
      "![Screenshot](/images/rfp/example.png)\n\n[Asset](/files/example.txt)"
    );
  });

  it("leaves existing runtime paths unchanged", () => {
    const markdown = "![Screenshot](/images/rfp/example.png)";

    expect(normalizeTutorialMarkdown(markdown)).toBe(markdown);
  });
});
