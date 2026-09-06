/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import * as React from "react";
import type { ISvgIcons } from "../type";

export function PlaneLogo({ width = "32", height = "32", className }: ISvgIcons) {
  const hStyle = typeof height === "number" ? `${height}px` : (height ?? "32px");
  const wStyle = typeof width === "number" ? `${width}px` : (width ?? "32px");

  return (
    <div
      className={`inline-flex items-center justify-center shrink-0 ${className ?? ""}`}
      style={{ height: hStyle, width: wStyle }}
    >
      <img
        src="/logos/cube.png"
        alt="oneflow"
        className="h-full w-full object-contain select-none"
      />
    </div>
  );
}

