import { readFile } from "node:fs/promises";
import path from "node:path";

import { RfpTutorial } from "@/components/rfp-tutorial";
import { normalizeTutorialMarkdown } from "@/lib/tutorial-markdown";

const tutorialPath = path.resolve(process.cwd(), "..", "RFP_TUTORIAL.md");

async function loadTutorialMarkdown() {
  try {
    return {
      markdown: normalizeTutorialMarkdown(await readFile(tutorialPath, "utf8")),
      tutorialAvailable: true
    };
  } catch {
    return {
      markdown:
        "# Tutorial unavailable\n\nThe RFP walkthrough could not be loaded from `RFP_TUTORIAL.md`.",
      tutorialAvailable: false
    };
  }
}

export default async function RfpTutorialPage() {
  const { markdown, tutorialAvailable } = await loadTutorialMarkdown();

  return <RfpTutorial markdown={markdown} tutorialAvailable={tutorialAvailable} />;
}
