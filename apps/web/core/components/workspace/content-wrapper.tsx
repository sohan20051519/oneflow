/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React from "react";
import { observer } from "mobx-react";
import { TopNavigationRoot } from "@/components/navigation/top-navigation-root";


export const WorkspaceContentWrapper = observer(function WorkspaceContentWrapper({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative flex size-full flex-col overflow-hidden bg-background text-foreground">
      <TopNavigationRoot />
      <div className="relative flex size-full overflow-hidden">
        <div className="relative size-full flex-grow overflow-hidden">
          {children}
        </div>
      </div>
    </div>
  );
});
