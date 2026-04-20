"use client";

import { startTransition, useDeferredValue, useRef, useState } from "react";
import {
  Button,
  Card,
  Column,
  Heading,
  Row,
  Switch,
  Text,
  Textarea
} from "@once-ui-system/core";

import { MetaBadge } from "@/components/meta-badge";
import { PageShell } from "@/components/page-shell";
import { convertRfpCsv, downloadTextFile, type ConversionResponse } from "@/lib/api";

function StatsPanel({ result }: { result: ConversionResponse }) {
  return (
    <Card className="surface-card" fillWidth padding="24" radius="xl">
      <Column gap="12">
        <Heading as="h2" size="l" weight="strong">
          Conversion summary
        </Heading>
        <ul className="stats-list">
          <li>{result.stats.total_rows} CSV rows scanned</li>
          <li>{result.stats.total_sections} discovered RFP/ROG sections</li>
          <li>{result.stats.responsive_sections} sections with responsive documents</li>
          <li>{result.stats.skipped_rows} rows skipped with warnings</li>
        </ul>
      </Column>
    </Card>
  );
}

function WarningPanel({ warnings }: { warnings: string[] }) {
  if (warnings.length === 0) {
    return null;
  }

  return (
    <Card
      fillWidth
      padding="24"
      radius="xl"
      background="warning-alpha-weak"
      border="warning-medium"
    >
      <Column gap="12">
        <Heading as="h2" size="l" weight="strong">
          Conversion warnings
        </Heading>
        <Text as="p">
          Invalid Bates rows were skipped, but the rest of the responsive document ranges were still
          converted.
        </Text>
        <ul className="warning-list">
          {warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      </Column>
    </Card>
  );
}

export function RfpConverter() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [result, setResult] = useState<ConversionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [includeEmpty, setIncludeEmpty] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const previewText = useDeferredValue(
    includeEmpty ? result?.documentTextWithEmpty ?? "" : result?.documentTextWithoutEmpty ?? ""
  );

  async function handleConvert() {
    if (!selectedFile) {
      setError("Choose a CSV file before converting.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const payload = await convertRfpCsv(selectedFile);
      startTransition(() => {
        setResult(payload);
      });
    } catch (conversionError) {
      const message =
        conversionError instanceof Error
          ? conversionError.message
          : "The CSV could not be converted.";
      setResult(null);
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleReset() {
    setSelectedFile(null);
    setResult(null);
    setError(null);
    setIncludeEmpty(true);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function handleDownload() {
    if (!result) {
      return;
    }

    downloadTextFile(result.downloadFilename, previewText);
  }

  return (
    <PageShell
      badge="RFP CSV to pleading"
      title="Convert tagged CSV productions into pleading-ready section text."
      description="Upload a CSV, keep or remove empty RFP sections, inspect warnings, and download the TXT output when the preview looks right."
    >
      <Column className="converter-layout" gap="20">
        <Card className="surface-card" fillWidth padding="24" radius="xl">
          <Column gap="20">
            <Row horizontal="between" vertical="center" gap="12" wrap>
              <Column gap="8">
                <Heading as="h2" size="l" weight="strong">
                  Upload and convert
                </Heading>
                <Text as="p">
                  The converter reads Bates values from the first two columns and responsive RFP or
                  ROG tags from column C onward.
                </Text>
              </Column>
              <MetaBadge
                label="TXT output"
                value={selectedFile ? selectedFile.name : "No CSV selected yet"}
              />
            </Row>

            <input
              ref={fileInputRef}
              aria-label="CSV file input"
              className="uploader-input"
              type="file"
              accept=".csv,text/csv"
              onChange={(event) => {
                const file = event.target.files?.[0] ?? null;
                setSelectedFile(file);
                setResult(null);
                setError(null);
              }}
            />

            <Row gap="12" wrap>
              <Button href="/tools/rfp-csv-to-pleading/tutorial/" variant="secondary">
                View tutorial
              </Button>
              <Button variant="secondary" onClick={() => fileInputRef.current?.click()}>
                Choose CSV
              </Button>
              <Button onClick={handleConvert} disabled={!selectedFile || isSubmitting} loading={isSubmitting}>
                Convert CSV
              </Button>
              <Button variant="tertiary" onClick={handleReset} disabled={!selectedFile && !result && !error}>
                Reset
              </Button>
              <Button variant="secondary" onClick={handleDownload} disabled={!result}>
                Download TXT
              </Button>
            </Row>

            <Switch
              ariaLabel="Include empty sections"
              label="Include empty sections"
              description='Keep sections with "No responsive documents." in the preview and downloaded TXT.'
              isChecked={includeEmpty}
              onToggle={() => setIncludeEmpty((current) => !current)}
            />

            {error ? (
              <Card padding="20" radius="l" background="danger-alpha-weak" border="danger-medium">
                <Text as="p">{error}</Text>
              </Card>
            ) : null}
          </Column>
        </Card>

        {result ? <StatsPanel result={result} /> : null}
        {result ? <WarningPanel warnings={result.warnings} /> : null}

        <Card className="surface-card" fillWidth padding="24" radius="xl">
          <Column gap="16">
            <div className="preview-header">
              <Column className="preview-header__copy" gap="8">
                <Heading as="h2" size="l" weight="strong">
                  Converted preview
                </Heading>
                <Text as="p">
                  Review the plain-text output before downloading it. The preview always reflects
                  the current empty-section toggle.
                </Text>
              </Column>
              <MetaBadge
                className="preview-mode-badge"
                label="Mode"
                value={includeEmpty ? "Showing all sections" : "Showing responsive sections only"}
              />
            </div>

            <Textarea
              id="rfp-preview"
              className={result ? "preview-textarea" : "placeholder-textarea"}
              label="Preview text"
              description="The download button uses the exact text shown here."
              lines={18}
              resize="vertical"
              readOnly
              value={
                previewText ||
                "Select a CSV file and run a conversion to preview the generated pleading text here."
              }
            />
          </Column>
        </Card>

        <Text as="p" className="footer-note" size="s">
          Uploaded CSV files are processed per request and are not persisted on the server.
        </Text>
      </Column>
    </PageShell>
  );
}
