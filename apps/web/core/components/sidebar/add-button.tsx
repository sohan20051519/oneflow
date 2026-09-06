/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { cn } from "@plane/utils";
import { Button } from "@plane/propel/button";

type Props = React.ComponentProps<"button"> & {
  label: React.ReactNode;
  onClick: () => void;
};

export function SidebarAddButton(props: Props) {
  const { label, onClick, disabled, className, ...rest } = props;
  return (
    <Button
      variant={"primary"}
      size={"md"}
      className={cn(
        "h-9 w-full justify-center gap-2 rounded-lg bg-[hsl(352,82%,52%)] px-3 text-13 font-semibold text-white shadow-sm transition-all hover:bg-[hsl(352,82%,52%)]/90 active:scale-[0.99]",
        className
      )}
      onClick={onClick}
      disabled={disabled}
      {...rest}
    >
      {label}
    </Button>
  );
}
