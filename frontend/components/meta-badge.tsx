import { type ComponentProps, type ReactNode, useId } from "react";

import { Badge } from "@once-ui-system/core";

type MetaBadgeProps = Omit<ComponentProps<typeof Badge>, "children" | "title"> & {
  label: string;
  value: ReactNode;
};

export function MetaBadge({
  label,
  value,
  className,
  effect = false,
  id,
  ...props
}: MetaBadgeProps) {
  const generatedId = useId().replace(/:/g, "");
  const badgeClassName = ["meta-badge", className].filter(Boolean).join(" ");

  return (
    <Badge className={badgeClassName} effect={effect} id={id ?? generatedId} {...props}>
      <span className="meta-badge__heading">
        <span className="meta-badge__label">{label}</span>
        <span className="meta-badge__separator" aria-hidden="true">
          /
        </span>
      </span>
      <span className="meta-badge__value">{value}</span>
    </Badge>
  );
}
