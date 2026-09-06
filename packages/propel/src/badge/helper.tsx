/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import * as React from "react";
import type { VariantProps } from "class-variance-authority";
import { cva } from "class-variance-authority";

export const badgeVariants = cva("inline-flex items-center justify-center gap-1.5 whitespace-nowrap font-semibold transition-all duration-200", {
  variants: {
    variant: {
      neutral: "bg-layer-1 text-secondary border border-subtle",
      brand: "bg-accent-primary text-on-color shadow-xs",
      warning: "bg-warning-subtle text-warning-primary",
      success: "bg-success-subtle text-success-primary",
      danger: "bg-danger-subtle text-danger-primary",
    },
    size: {
      sm: "h-5 rounded-md px-2 py-0.5 text-11",
      base: "h-6 rounded-md px-2.5 py-0.5 text-12",
      lg: "h-7 rounded-md px-3 py-1 text-12",
    },
  },
  defaultVariants: {
    variant: "neutral",
    size: "base",
  },
});

export type BadgeProps = Omit<React.HTMLAttributes<HTMLSpanElement>, "className"> &
  VariantProps<typeof badgeVariants> & {
    appendIcon?: React.ReactElement;
    prependIcon?: React.ReactElement;
  };

export type TBadgeVariant = NonNullable<BadgeProps["variant"]>;
export type TBadgeSize = NonNullable<BadgeProps["size"]>;

const badgeIconStyling: Record<TBadgeSize, string> = {
  sm: "size-3.5",
  base: "size-3.5",
  lg: "size-4",
};

export function getBadgeIconStyling(size: TBadgeSize): string {
  return badgeIconStyling[size];
}

export function getBadgeStyling(variant: TBadgeVariant, size: TBadgeSize): string {
  return badgeVariants({ variant, size });
}
