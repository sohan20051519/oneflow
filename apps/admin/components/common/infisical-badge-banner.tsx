/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React from "react";
import Link from "next/link";
import { Lock, ArrowRight, ShieldCheck } from "lucide-react";
import { getButtonStyling } from "@plane/propel/button";

interface InfisicalBadgeBannerProps {
  pageName: string;
}

export function InfisicalBadgeBanner({ pageName }: InfisicalBadgeBannerProps) {
  return (
    <div className="mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4 rounded-lg border border-border-subtle bg-layer-subtle p-4">
      <div className="flex items-start gap-3">
        <div className="rounded-md bg-blue-500/10 p-2 text-blue-600 dark:text-blue-400 shrink-0">
          <ShieldCheck className="h-5 w-5" />
        </div>
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h4 className="text-14 font-semibold text-primary">
              Infisical Centralized Secret Management
            </h4>
            <span className="rounded bg-layer-base px-2 py-0.5 text-11 font-medium text-secondary">
              (Value fetched from Infisical)
            </span>
          </div>
          <p className="mt-1 text-12 text-tertiary">
            All variables for <strong>{pageName}</strong> are passed and loaded directly from Self-Hosted Infisical. Direct edits are disabled and values are masked with placeholders for security.
          </p>
        </div>
      </div>
      <div className="shrink-0 flex items-center gap-2">
        <Link
          href="/configuration/"
          className={getButtonStyling("outline", "sm")}
        >
          <Lock className="mr-1.5 h-3.5 w-3.5 text-tertiary" />
          <span>Infisical Configuration</span>
          <ArrowRight className="ml-1 h-3.5 w-3.5" />
        </Link>
      </div>
    </div>
  );
}
