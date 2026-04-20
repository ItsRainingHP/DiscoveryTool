import { Card, Column, Text } from "@once-ui-system/core";
import ReactMarkdown from "react-markdown";

import { PageShell } from "@/components/page-shell";

type RfpTutorialProps = {
  markdown: string;
  tutorialAvailable?: boolean;
};

export function RfpTutorial({ markdown, tutorialAvailable = true }: RfpTutorialProps) {
  return (
    <PageShell
      badge="RFP walkthrough"
      title="Prepare a converter-ready RFP CSV export."
      description="Follow the step-by-step walkthrough below to build a CSV with Bates columns first, RFP tag columns after them, and TRUE values in the responsive rows you want converted."
      backHref="/tools/rfp-csv-to-pleading/"
      backLabel="Back to converter"
    >
      <Column gap="20">
        {!tutorialAvailable ? (
          <Card padding="24" radius="xl" background="warning-alpha-weak" border="warning-medium">
            <Text as="p">
              The tutorial page loaded, but the source markdown file could not be found at build
              time. Add or restore <code>RFP_TUTORIAL.md</code> to republish the full walkthrough.
            </Text>
          </Card>
        ) : null}

        <Card className="surface-card tutorial-card" padding="32" radius="xl">
          <div className="tutorial-markdown">
            <ReactMarkdown
              components={{
                img: ({ alt, src }) =>
                  src ? (
                    // The walkthrough is authored in markdown, so we intentionally render its local screenshots as-is.
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      alt={alt ?? ""}
                      className="tutorial-markdown__image"
                      loading="lazy"
                      src={String(src)}
                    />
                  ) : null
              }}
            >
              {markdown}
            </ReactMarkdown>
          </div>
        </Card>
      </Column>
    </PageShell>
  );
}
