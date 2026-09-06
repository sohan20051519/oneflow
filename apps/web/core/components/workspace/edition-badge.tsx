/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { observer } from "mobx-react";

export const WorkspaceEditionBadge = observer(function WorkspaceEditionBadge() {

  return (
    <span className="rounded-md px-2 py-0.5 text-[11px] font-medium text-muted-foreground bg-secondary/80">
      oneflow core
    </span>
  );
});

