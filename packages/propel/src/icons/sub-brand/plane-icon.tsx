/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import * as React from "react";

import { IconWrapper } from "../icon-wrapper";
import type { ISvgIcons } from "../type";

export function PlaneNewIcon({ color = "currentColor", className, ...rest }: ISvgIcons) {
  return (
    <img
      src="/logos/cube.png"
      alt="oneflow"
      className={`size-5 object-contain select-none ${className ?? ""}`}
    />
  );
}
