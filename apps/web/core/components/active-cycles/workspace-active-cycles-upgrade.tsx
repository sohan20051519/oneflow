/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useEffect, useState } from "react";
import { observer } from "mobx-react";
import Link from "next/link";
import { useParams } from "next/navigation";
// plane imports
import { useTranslation } from "@plane/i18n";
import { ContentWrapper } from "@plane/ui";
import { CircularProgressIndicator } from "@plane/ui";
import { calculateCycleProgress } from "@plane/utils";
import type { ICycle } from "@plane/types";
// hooks
import { useCycle } from "@/hooks/store/use-cycle";
import { useProject } from "@/hooks/store/use-project";

type TActiveCycleCard = {
  cycle: ICycle;
  workspaceSlug: string;
};

const ActiveCycleCard = observer(function ActiveCycleCard({ cycle, workspaceSlug }: TActiveCycleCard) {
  const { getProjectById } = useProject();
  const project = cycle.project_id ? getProjectById(cycle.project_id) : undefined;

  const totalIssues = cycle.total_issues ?? 0;
  const completedIssues = cycle.completed_issues ?? 0;
  const progress = calculateCycleProgress(completedIssues, totalIssues);

  const progressColor = progress >= 66 ? "#22c55e" : progress >= 33 ? "#f59e0b" : "#ef4444";

  return (
    <Link
      href={`/${workspaceSlug}/projects/${cycle.project_id}/cycles/${cycle.id}`}
      className="flex flex-col gap-3 rounded-lg border border-subtle bg-surface-1 p-4 hover:bg-surface-2 transition-colors"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-primary truncate">{cycle.name}</p>
          {project && (
            <p className="text-xs text-tertiary mt-0.5 truncate">{project.name}</p>
          )}
        </div>
        <div className="flex-shrink-0">
          <CircularProgressIndicator
            size={36}
            percentage={progress}
            strokeColor={progressColor}
          >
            <span className="text-[9px] font-medium" style={{ color: progressColor }}>
              {progress}%
            </span>
          </CircularProgressIndicator>
        </div>
      </div>
      <div className="flex items-center justify-between text-xs text-tertiary">
        <span>
          {completedIssues}/{totalIssues} issues complete
        </span>
        {cycle.end_date && (
          <span>
            Ends {new Date(cycle.end_date).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
          </span>
        )}
      </div>
      <div className="h-1.5 w-full rounded-full bg-surface-3 overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${progress}%`, backgroundColor: progressColor }}
        />
      </div>
    </Link>
  );
});

export const WorkspaceActiveCyclesUpgrade = observer(function WorkspaceActiveCyclesUpgrade() {
  const { workspaceSlug } = useParams();
  const { t } = useTranslation();
  // store hooks
  const { fetchWorkspaceCycles, cycleMap } = useCycle();
  // local state
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!workspaceSlug) return;
    setIsLoading(true);
    fetchWorkspaceCycles(workspaceSlug.toString()).finally(() => setIsLoading(false));
  }, [workspaceSlug, fetchWorkspaceCycles]);

  // Get all active (current status) cycles across the workspace
  const activeCycles = Object.values(cycleMap ?? {}).filter(
    (cycle) => cycle.status?.toLowerCase() === "current" && !cycle.archived_at
  );

  return (
    <ContentWrapper>
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-primary">{t("active_cycles")}</h1>
        <p className="text-sm text-tertiary mt-1">
          All currently active cycles across your workspace projects.
        </p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="flex flex-col items-center gap-3">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent-primary border-t-transparent" />
            <span className="text-sm text-tertiary">Loading active cycles…</span>
          </div>
        </div>
      ) : activeCycles.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 gap-3">
          <div className="h-16 w-16 rounded-full bg-surface-2 flex items-center justify-center">
            <svg className="h-8 w-8 text-tertiary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M12 6v6l4 2m6-2a10 10 0 11-20 0 10 10 0 0120 0z" />
            </svg>
          </div>
          <p className="text-base font-medium text-secondary">No active cycles</p>
          <p className="text-sm text-tertiary text-center max-w-xs">
            None of your projects have an active cycle running right now. Start a cycle in any project to see it here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {activeCycles.map((cycle) => (
            <ActiveCycleCard
              key={cycle.id}
              cycle={cycle}
              workspaceSlug={workspaceSlug?.toString() ?? ""}
            />
          ))}
        </div>
      )}
    </ContentWrapper>
  );
});
