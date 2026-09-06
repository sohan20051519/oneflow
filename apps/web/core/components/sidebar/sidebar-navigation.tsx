/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { cn } from "@plane/utils";

type TSidebarNavItem = {
  className?: string;
  isActive?: boolean;
  children?: React.ReactNode;
};

export function SidebarNavItem(props: TSidebarNavItem) {
  const { className, isActive, children } = props;
  return (
    <div
      className={cn(
        "group relative flex h-9 w-full cursor-pointer items-center justify-between gap-2.5 rounded-lg px-3 py-2 text-13 font-medium transition-all duration-200 outline-none select-none",
        {
          "bg-primary/10 text-primary font-semibold shadow-xs": isActive,
          "text-muted-foreground hover:bg-accent/70 hover:text-foreground": !isActive,
        },
        className
      )}
    >
      {children}
    </div>
  );
}
