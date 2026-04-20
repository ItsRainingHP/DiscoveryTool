"use client";

import { startTransition, useRef, useState } from "react";
import { Button, Card, Column, Heading, Row, Text } from "@once-ui-system/core";

import { MetaBadge } from "@/components/meta-badge";
import { PageShell } from "@/components/page-shell";
import {
  convertPrivilegeCsv,
  downloadCsvFile,
  type PrivilegeConversionResponse
} from "@/lib/api";

function StatsPanel({ result }: { result: PrivilegeConversionResponse }) {
  return (
    <Card className="surface-card" fillWidth padding="24" radius="xl">
      <Column gap="12">
        <Heading as="h2" size="l" weight="strong">
          Conversion summary
        </Heading>
        <ul className="stats-list">
          <li>{result.stats.total_rows} CSV rows scanned</li>
          <li>{result.stats.exported_rows} rows exported</li>
          <li>{result.stats.reason_columns} dynamic reason columns discovered</li>
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
          Recoverable formatting issues were preserved in the output and called out here for review.
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

function CsvPreviewTable({
  headers,
  rows
}: {
  headers: string[];
  rows: string[][];
}) {
  return (
    <div className="csv-preview-shell">
      <div className="csv-preview-scroll">
        <table aria-label="Preview CSV" className="csv-preview-table">
          <thead>
            <tr>
              {headers.map((header, headerIndex) => (
                <th key={`${header}-${headerIndex}`} scope="col">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={`row-${rowIndex}`}>
                {headers.map((header, columnIndex) => (
                  <td key={`row-${rowIndex}-${header}-${columnIndex}`}>{row[columnIndex] ?? ""}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function PrivilegeConverter() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [result, setResult] = useState<PrivilegeConversionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleConvert() {
    if (!selectedFile) {
      setError("Choose a CSV file before converting.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const payload = await convertPrivilegeCsv(selectedFile);
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

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function handleDownload() {
    if (!result) {
      return;
    }

    downloadCsvFile(result.downloadFilename, result.csvText);
  }

  return (
    <PageShell
      badge="Privilege log preparation"
      title="Convert privilege export CSVs into review-ready log rows."
      description="Upload a privilege export CSV, review the exact reordered output, and download a copy/paste-ready CSV file."
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
                  The converter merges recipients, applies the subject-to-file-name fallback, and
                  builds the privilege text from redact or withhold plus any dynamic reason tags.
                </Text>
              </Column>
              <MetaBadge
                label="CSV output"
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
              <Button variant="secondary" onClick={() => fileInputRef.current?.click()}>
                Choose CSV
              </Button>
              <Button
                onClick={handleConvert}
                disabled={!selectedFile || isSubmitting}
                loading={isSubmitting}
              >
                Convert CSV
              </Button>
              <Button
                variant="tertiary"
                onClick={handleReset}
                disabled={!selectedFile && !result && !error}
              >
                Reset
              </Button>
              <Button variant="secondary" onClick={handleDownload} disabled={!result}>
                Download CSV
              </Button>
            </Row>

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
                  Review the converted rows in a spreadsheet-style preview before downloading or
                  pasting the final CSV.
                </Text>
              </Column>
              <MetaBadge
                className="preview-mode-badge"
                label="Rows"
                value={result ? `${result.rows.length} rows ready` : "No converted rows yet"}
              />
            </div>

            <Column gap="12">
              <Text as="p" size="s" className="csv-preview-note">
                The download button keeps the exact CSV text. This preview only changes how it is
                displayed for easier review.
              </Text>

              {result ? (
                <Text as="p" className="csv-preview-warning" role="alert">
                  Review this privilege log and redact any privileged names before using or sharing
                  it.
                </Text>
              ) : null}

              {result ? (
                <CsvPreviewTable headers={result.headers} rows={result.rows} />
              ) : (
                <div className="csv-preview-empty" role="status">
                  Select a CSV file and run a conversion to preview the generated privilege log CSV
                  here.
                </div>
              )}
            </Column>
          </Column>
        </Card>

        <Text as="p" className="footer-note" size="s">
          Uploaded CSV files are processed per request and are not persisted on the server.
        </Text>
      </Column>
    </PageShell>
  );
}
