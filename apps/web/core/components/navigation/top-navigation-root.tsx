/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

// components
import { observer } from "mobx-react";
import { useParams, usePathname } from "next/navigation";
import { cn } from "@plane/utils";
import { TopNavPowerK } from "@/components/navigation";
import { HelpMenuRoot } from "@/components/workspace/sidebar/help-section/root";
import { UserMenuRoot } from "@/components/workspace/sidebar/user-menu-root";
import { WorkspaceMenuRoot } from "@/components/workspace/sidebar/workspace-menu-root";
import { useAppRailPreferences } from "@/hooks/use-navigation-preferences";
import { Tooltip } from "@plane/propel/tooltip";
import { AppSidebarItem } from "@/components/sidebar/sidebar-item";
import { InboxIcon } from "@plane/propel/icons";
import useSWR from "swr";
import { useWorkspaceNotifications } from "@/hooks/store/notifications";
import { PlaneLockup } from "@plane/propel/icons";
import Link from "next/link";

export const TopNavigationRoot = observer(function TopNavigationRoot() {
  // router
  const { workspaceSlug } = useParams();
  const pathname = usePathname();

  // store hooks
  const { unreadNotificationsCount, getUnreadNotificationsCount } = useWorkspaceNotifications();
  const { preferences } = useAppRailPreferences();

  const showLabel = preferences.displayMode === "icon_with_label";

  // Fetch notification count
  useSWR(
    workspaceSlug ? "WORKSPACE_UNREAD_NOTIFICATION_COUNT" : null,
    workspaceSlug ? () => getUnreadNotificationsCount(workspaceSlug.toString()) : null
  );

  // Calculate notification count
  const isMentionsEnabled = unreadNotificationsCount.mention_unread_notifications_count > 0;
  const totalNotifications = isMentionsEnabled
    ? unreadNotificationsCount.mention_unread_notifications_count
    : unreadNotificationsCount.total_unread_notifications_count;

  return (
    <div
      className={cn(
        "relative z-[27] flex h-12 w-full items-center justify-between border-b border-subtle-1 bg-card px-4 shadow-xs transition-all duration-300",
        {
          "px-3": !showLabel,
        }
      )}
    >
      {/* Brand Lockup */}
      <div className="flex shrink-0 items-center gap-2 z-10">
        <Link
          href={workspaceSlug ? `/${workspaceSlug}` : "/"}
          className="flex items-center pr-2 transition-opacity hover:opacity-85 shrink-0"
        >
          <PlaneLockup height={26} className="text-foreground" />
        </Link>
      </div>

      {/* Power K Search - Centered in Top Bar */}
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 flex items-center justify-center pointer-events-auto z-10">
        <TopNavPowerK />
      </div>

      {/* Additional Actions */}
      <div className="flex shrink-0 items-center justify-end gap-1.5 sm:gap-2 z-10 ml-auto">
        <WorkspaceMenuRoot variant="top-navigation" />
        <Tooltip tooltipContent="Inbox" position="bottom">
          <AppSidebarItem
            variant="link"
            item={{
              href: `/${workspaceSlug?.toString()}/notifications/`,
              icon: (
                <div className="relative">
                  <InboxIcon className="size-5 text-muted-foreground hover:text-foreground transition-colors" />
                  {totalNotifications > 0 && (
                    <span className="absolute top-0 right-0 size-2 rounded-full bg-[hsl(352,82%,52%)]" />
                  )}
                </div>
              ),
              isActive: pathname?.includes("/notifications/"),
            }}
          />
        </Tooltip>
        <HelpMenuRoot />
        <div className="flex size-8 items-center justify-center rounded-full hover:ring-2 hover:ring-[hsl(352,82%,52%)]/30 transition-all">
          <UserMenuRoot />
        </div>
      </div>
    </div>
  );
});
