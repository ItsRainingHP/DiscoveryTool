"use client";

import { ThemeProvider } from "@once-ui-system/core";

import { appTheme } from "@/components/theme-config";

export function AppProviders({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider {...appTheme}>{children}</ThemeProvider>
  );
}
