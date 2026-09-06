/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import * as React from "react";
import type { ISvgIcons } from "../type";

export function PlaneLockup({ width, height = "28", className }: ISvgIcons) {
  const hStyle = typeof height === "number" ? `${height}px` : (height ?? "28px");
  const wStyle = width ? (typeof width === "number" ? `${width}px` : width) : "auto";

  return (
    <div
      className={`inline-flex items-center shrink-0 ${className ?? ""}`}
      style={{ height: hStyle, width: wStyle }}
    >
      <img
        src="/logos/dark.png"
        alt="oneflow"
        className="oneflow-logo-dark h-full w-auto object-contain select-none"
      />
      <img
        src="/logos/light.png"
        alt="oneflow"
        className="oneflow-logo-light h-full w-auto object-contain select-none"
      />
    </div>
  );
}

