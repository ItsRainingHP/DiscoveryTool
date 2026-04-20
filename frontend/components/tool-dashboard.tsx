import { Button, Card, Column, Heading, Row, StatusIndicator, Text } from "@once-ui-system/core";

import { MetaBadge } from "@/components/meta-badge";
import { PageShell } from "@/components/page-shell";

type ToolCardProps = {
  href: string;
  title: string;
  description: string;
  status: string;
  actionLabel: string;
};

const READY_ACCENT = "cyan" as const;

function ToolCard({ href, title, description, status, actionLabel }: ToolCardProps) {
  return (
    <Card className="tool-card" fillWidth fillHeight padding="24" radius="xl">
      <Column fillWidth fillHeight gap="20">
        <div className="tool-card__header">
          <MetaBadge label="Tool" value={title} />
          <div className="tool-card__status">
            <StatusIndicator color={READY_ACCENT} ariaLabel={status} />
            <Text size="s" weight="strong">
              {status}
            </Text>
          </div>
        </div>

        <Column fillWidth gap="12" flex="1">
          <Heading as="h2" size="l" weight="strong">
            {title}
          </Heading>
          <Text as="p">{description}</Text>
        </Column>

        <Button className="tool-card__action" href={href}>
          {actionLabel}
        </Button>
      </Column>
    </Card>
  );
}

export function ToolDashboard() {
  return (
    <PageShell
      badge="Logikcull Workflows"
      title="Convert CSV"
      description="Upload Logikcull export CSVs into usable information for productions."
      backHref="/"
      backLabel="Refresh dashboard"
    >
      <Column gap="20">
        <Row gap="20" wrap>
          <ToolCard
            href="/tools/rfp-csv-to-pleading/"
            title="RFP CSV to Pleading"
            description="Upload a tagged production CSV, preview the converted RFP and ROG sections, and download the generated TXT file."
            status="Ready"
            actionLabel="Open converter"
          />
          <ToolCard
            href="/tools/privilege-log/"
            title="Privilege Log Preparation"
            description="Upload a privilege CSV, preview the reordered output, and download the review-ready CSV file."
            status="Ready"
            actionLabel="Open converter"
          />
        </Row>
      </Column>
    </PageShell>
  );
}
