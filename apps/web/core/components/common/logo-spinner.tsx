/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React from "react";

export function LogoSpinner({ className = "h-8 w-8" }: { className?: string }) {
  return (
    <div className="flex items-center justify-center p-4" style={{ width: "48px", height: "48px", margin: "auto" }}>
      <div className="relative flex items-center justify-center" style={{ width: "40px", height: "40px" }}>
        {/* Glow effect */}
        <div className="absolute h-10 w-10 rounded-full bg-[hsl(352,82%,52%)] opacity-20 blur-md animate-pulse" style={{ width: "40px", height: "40px" }} />
        {/* Sleek 270 degree arc spinner */}
        <svg
          className={`animate-spin text-[hsl(352,82%,52%)] ${className}`}
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          width={32}
          height={32}
          style={{ width: "32px", height: "32px", maxWidth: "32px", maxHeight: "32px", color: "hsl(352,82%,52%)" }}
        >
          <circle
            className="opacity-20"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="2.5"
          />
          <path
            className="opacity-100"
            fill="hsl(352,82%,52%)"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      </div>
    </div>
  );
}
