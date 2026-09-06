/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { GOD_MODE_URL } from "@plane/constants";
import DefaultLayout from "@/layouts/default-layout";
import { PlaneLogo, PlaneLockup } from "@plane/propel/icons";
import { Button } from "@plane/propel/button";

export function InstanceNotReady() {
  return (
    <DefaultLayout>
      <div className="relative z-10 flex h-screen w-screen overflow-hidden bg-background text-foreground">
        {/* Subtle onebiz aurora glow */}
        <div className="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-[hsl(352,82%,52%)] opacity-[0.07] blur-[120px] rounded-full" />
        
        {/* Main content */}
        <div className="flex h-full w-full flex-col items-center px-8 pt-8 pb-10 justify-between">
          <header className="flex w-full shrink-0 items-center justify-between max-w-[1400px]">
            <PlaneLockup height={28} width={130} className="text-foreground" />
          </header>

          <main className="flex flex-col items-center justify-center gap-8 max-w-md w-full text-center">
            <div className="p-4 rounded-2xl bg-[hsl(352,82%,52%)]/10 text-[hsl(352,82%,52%)] ring-1 ring-[hsl(352,82%,52%)]/20 shadow-sm">
              <PlaneLogo height={44} width={44} />
            </div>

            <div className="flex flex-col items-center gap-2">
              <h1 className="text-2xl font-bold tracking-tight text-foreground">
                Welcome to OneFlow
              </h1>
              <p className="text-sm text-muted-foreground max-w-sm">
                Set up your instance and launch your workspace to streamline projects and cycles.
              </p>
            </div>

            <a href={GOD_MODE_URL} className="w-full">
              <Button
                variant="primary"
                className="w-full h-10 rounded-lg font-medium shadow-sm bg-[hsl(352,82%,52%)] hover:bg-[hsl(352,82%,52%)]/90 text-white transition-colors"
                size="lg"
              >
                Get started
              </Button>
            </a>
          </main>

          <footer className="text-xs text-muted-foreground">
            oneflow platform
          </footer>
        </div>
      </div>
    </DefaultLayout>
  );
}
