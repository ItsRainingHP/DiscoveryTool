const PUBLIC_ASSET_PREFIX = /(\()((?:\.\/)?frontend\/public\/)/g;

export function normalizeTutorialMarkdown(markdown: string): string {
  return markdown.replaceAll(PUBLIC_ASSET_PREFIX, "$1/");
}
