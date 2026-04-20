import type { Metadata } from "next";
import { ThemeInit } from "@once-ui-system/core";
import "@once-ui-system/core/css/tokens.css";
import "@once-ui-system/core/css/styles.css";
import "./globals.css";

import { AppProviders } from "@/components/app-providers";
import { appThemeInitConfig } from "@/components/theme-config";

export const metadata: Metadata = {
  title: "Discovery Tool",
  description: "Discovery workflow tools for CSV conversion and privilege log preparation."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <ThemeInit config={appThemeInitConfig} /><title></title>
      </head>
      <body>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
