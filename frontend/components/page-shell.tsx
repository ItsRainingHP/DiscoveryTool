import { Button, Card, Column, Heading, Row, Text } from "@once-ui-system/core";

import { MetaBadge } from "@/components/meta-badge";

type PageShellProps = {
  badge: string;
  title: string;
  description: string;
  children: React.ReactNode;
  backHref?: string;
  backLabel?: string;
};

export function PageShell({
  badge,
  title,
  description,
  children,
  backHref = "/",
  backLabel = "Back to tool dashboard"
}: PageShellProps) {
  return (
    <Column className="app-shell" paddingY="24" gap="24">
      <div className="page-frame">
        <Row className="page-header" vertical="center" horizontal="between" paddingY="16" gap="12" wrap>
          <MetaBadge label="Discovery Tool" value={badge} />
          <Button href={backHref} variant="secondary" size="s">
            {backLabel}
          </Button>
        </Row>

        <Card className="hero-card" fillWidth padding="32" radius="xl">
          <Column gap="16">
            <MetaBadge label="Workflow" value={badge} />
            <Column gap="8">
              <Heading as="h1" size="xl" weight="strong">
                {title}
              </Heading>
              <Text as="p" size="l">
                {description}
              </Text>
            </Column>
          </Column>
        </Card>
      </div>

      <div className="page-frame">
        {children}
      </div>
    </Column>
  );
}
