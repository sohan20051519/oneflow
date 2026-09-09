/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useState } from "react";
import { observer } from "mobx-react";
import { useParams } from "next/navigation";
import { Archive, Trash2, X } from "lucide-react";
import { setPromiseToast } from "@plane/propel/toast";
import { cn } from "@plane/utils";
// hooks
import { useMultipleSelectStore } from "@/hooks/store/use-multiple-select-store";
// services
import { IssueService } from "@/services/issue";

type Props = {
  className?: string;
};

const issueService = new IssueService();

export const BulkOperationsUpgradeBanner = observer(function BulkOperationsUpgradeBanner(props: Props) {
  const { className } = props;

  // router (workspace slug from URL params)
  const params = useParams();
  const workspaceSlug = params?.workspaceSlug as string | undefined;
  const projectId = params?.projectId as string | undefined;

  // store hooks
  const { selectedEntityIds, clearSelection } = useMultipleSelectStore();

  // local state
  const [isArchiving, setIsArchiving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const count = selectedEntityIds.length;

  if (count === 0 || !workspaceSlug || !projectId) return null;

  const handleBulkArchive = async () => {
    if (isArchiving) return;
    setIsArchiving(true);

    const archivePromise = issueService
      .bulkArchiveIssues(workspaceSlug, projectId, { issue_ids: selectedEntityIds })
      .then(() => { clearSelection(); });

    setPromiseToast(archivePromise, {
      loading: `Archiving ${count} issue${count !== 1 ? "s" : ""}…`,
      success: {
        title: "Archived!",
        message: () => `${count} issue${count !== 1 ? "s" : ""} archived successfully.`,
      },
      error: {
        title: "Error",
        message: () => "Something went wrong while archiving. Please try again.",
      },
    });

    archivePromise.finally(() => setIsArchiving(false));
  };

  const handleBulkDelete = async () => {
    if (isDeleting) return;
    setIsDeleting(true);

    const deletePromise = issueService
      .bulkDeleteIssues(workspaceSlug, projectId, { issue_ids: selectedEntityIds })
      .then(() => { clearSelection(); });

    setPromiseToast(deletePromise, {
      loading: `Deleting ${count} issue${count !== 1 ? "s" : ""}…`,
      success: {
        title: "Deleted!",
        message: () => `${count} issue${count !== 1 ? "s" : ""} deleted successfully.`,
      },
      error: {
        title: "Error",
        message: () => "Something went wrong while deleting. Please try again.",
      },
    });

    deletePromise.finally(() => setIsDeleting(false));
  };

  return (
    <div className={cn("sticky bottom-0 left-0 z-[2] grid h-20 place-items-center px-3.5", className)}>
      <div className="flex h-14 w-full items-center justify-between gap-3 rounded-md border-[0.5px] border-custom-border-200 bg-custom-background-100 px-4 py-2 shadow-sm">
        {/* Selection count + clear */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={clearSelection}
            className="flex h-6 w-6 items-center justify-center rounded hover:bg-custom-background-80 text-custom-text-400 hover:text-custom-text-200"
            title="Clear selection"
          >
            <X className="h-4 w-4" />
          </button>
          <span className="text-sm font-medium text-custom-text-200">
            {count} issue{count !== 1 ? "s" : ""} selected
          </span>
        </div>

        {/* Bulk action buttons */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleBulkArchive}
            disabled={isArchiving || isDeleting}
            className="flex items-center gap-1.5 rounded border border-custom-border-200 bg-custom-background-100 px-3 py-1.5 text-xs font-medium text-custom-text-300 hover:bg-custom-background-80 hover:text-custom-text-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Archive className="h-3.5 w-3.5" />
            {isArchiving ? "Archiving…" : "Archive"}
          </button>
          <button
            type="button"
            onClick={handleBulkDelete}
            disabled={isArchiving || isDeleting}
            className="flex items-center gap-1.5 rounded border border-red-500/30 bg-red-500/10 px-3 py-1.5 text-xs font-medium text-red-500 hover:bg-red-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Trash2 className="h-3.5 w-3.5" />
            {isDeleting ? "Deleting…" : "Delete"}
          </button>
        </div>
      </div>
    </div>
  );
});
