import { Button, Card, Column, Heading, Row, StatusIndicator, Text } from "@once-ui-system/core";

import { MetaBadge } from "@/components/meta-badge";
import { PageShell } from "@/components/page-shell";

type ToolCardProps = {
  href: string;
  title: string;
  description: string;
  status: string;
  actionLabel: string;
  accent: "cyan" | "yellow";
};

function ToolCard({ href, title, description, status, actionLabel, accent }: ToolCardProps) {
  return (
    <Card className="tool-card" fillWidth fillHeight padding="24" radius="xl">
      <Column fillHeight gap="20">
        <Row horizontal="between" vertical="center" gap="12" wrap>
          <MetaBadge label="Tool" value={title} />
          <Row vertical="center" gap="8">
            <StatusIndicator color={accent} ariaLabel={status} />
            <Text size="s" weight="strong">
              {status}
            </Text>
          </Row>
        </Row>

        <Column gap="12" flex="1">
          <Heading as="h2" size="l" weight="strong">
            {title}
          </Heading>
          <Text as="p">{description}</Text>
        </Column>

        <Button href={href} fillWidth>
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
            accent="cyan"
          />
          <ToolCard
            href="/tools/privilege-log/"
            title="Privilege Log Preparation"
            description="Upload a privilege CSV, preview the reordered output, and download the review-ready CSV file."
            status="Ready"
            actionLabel="Open converter"
            accent="yellow"
          />
        </Row>
      </Column>
    </PageShell>
  );
}
