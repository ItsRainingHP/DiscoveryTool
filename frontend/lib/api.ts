export interface ConversionSection {
  label: string;
  ranges: string[];
  responsive: boolean;
  text: string;
}

export interface ConversionStats {
  total_rows: number;
  skipped_rows: number;
  total_sections: number;
  responsive_sections: number;
}

export interface ConversionResponse {
  sourceFilename: string;
  downloadFilename: string;
  warnings: string[];
  sections: ConversionSection[];
  documentTextWithEmpty: string;
  documentTextWithoutEmpty: string;
  stats: ConversionStats;
}

export interface PrivilegeConversionStats {
  total_rows: number;
  exported_rows: number;
  reason_columns: number;
}

export interface PrivilegeConversionResponse {
  sourceFilename: string;
  downloadFilename: string;
  headers: string[];
  rows: string[][];
  csvText: string;
  warnings: string[];
  stats: PrivilegeConversionStats;
}

function getApiBaseUrl() {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api";
  return baseUrl.endsWith("/") ? baseUrl.slice(0, -1) : baseUrl;
}

export async function convertRfpCsv(file: File): Promise<ConversionResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${getApiBaseUrl()}/rfp/convert`, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    let detail = "The CSV could not be converted.";

    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // Ignore JSON parsing errors and fall back to the default message.
    }

    throw new Error(detail);
  }

  return (await response.json()) as ConversionResponse;
}

export async function convertPrivilegeCsv(file: File): Promise<PrivilegeConversionResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${getApiBaseUrl()}/privilege/convert`, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    let detail = "The CSV could not be converted.";

    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // Ignore JSON parsing errors and fall back to the default message.
    }

    throw new Error(detail);
  }

  return (await response.json()) as PrivilegeConversionResponse;
}

function downloadFile(filename: string, content: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = filename;
  link.click();

  URL.revokeObjectURL(url);
}

export function downloadTextFile(filename: string, content: string) {
  downloadFile(filename, content, "text/plain;charset=utf-8");
}

export function downloadCsvFile(filename: string, content: string) {
  downloadFile(filename, content, "text/csv;charset=utf-8");
}
