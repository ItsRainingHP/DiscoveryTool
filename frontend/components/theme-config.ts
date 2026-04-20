export const appTheme = {
  theme: "dark",
  neutral: "gray",
  brand: "blue",
  accent: "cyan",
  solid: "contrast",
  solidStyle: "flat",
  border: "rounded",
  surface: "translucent",
  transition: "all",
  scaling: "100"
} as const;

export const appThemeInitConfig = {
  theme: appTheme.theme,
  neutral: appTheme.neutral,
  brand: appTheme.brand,
  accent: appTheme.accent,
  solid: appTheme.solid,
  "solid-style": appTheme.solidStyle,
  border: appTheme.border,
  surface: appTheme.surface,
  transition: appTheme.transition,
  scaling: appTheme.scaling,
  "viz-style": "categorical"
} as const;
