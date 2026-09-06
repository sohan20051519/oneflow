from plane.app.views.workspace.member import WorkspaceMemberUserEndpoint, UserWorkspaceProjectRolesEndpoint
# SPDX-FileCopyrightText: 2023-present Plane Software, Inc.
# SPDX-License-Identifier: LicenseRef-Plane-Commercial
#
# Licensed under the Plane Commercial License (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# https://plane.so/legals/eula
#
# DO NOT remove or modify this notice.
# NOTICE: Proprietary and confidential. Unauthorized use or distribution is prohibited.

from django.urls import path


from plane.app.views import (
    UserWorkspaceInvitationsViewSet,
    WorkSpaceViewSet,
    WorkspaceJoinEndpoint,
    WorkSpaceMemberViewSet,
    WorkspaceInvitationsViewset,
    WorkspacePreferencesEndpoint,
    WorkspaceMemberUserViewsEndpoint,
    WorkSpaceAvailabilityCheckEndpoint,
    UserLastProjectWithWorkspaceEndpoint,
    WorkspaceUserProfileStatsEndpoint,
    WorkspaceUserActivityEndpoint,
    WorkspaceUserProfileEndpoint,
    WorkspaceUserProfileProjectStatsEndpoint,
    WorkspaceUserProfileIssuesEndpoint,
    WorkspaceUserProfileIssuesTotalCountEndpoint,
    WorkspaceLabelsEndpoint,
    WorkspaceLabelsLiteEndpoint,
    PageLabelDetailEndpoint,
    PageLabelsEndpoint,
    WorkspaceAuditLogEndpoint,
    WorkspaceAuditLogExportEndpoint,
    WorkspaceAuditLogExportDownloadEndpoint,
    WorkspaceAuditLogVerifyEndpoint,
    WorkspaceProjectMemberEndpoint,
    WorkspaceProjectMembersLiteEndpoint,
    WorkspaceUserPropertiesEndpoint,
    WorkspaceStatesEndpoint,
    WorkspaceStateDetailEndpoint,
    WorkspaceStatesLiteEndpoint,
    WorkspaceEstimatesEndpoint,
    ExportWorkspaceUserActivityEndpoint,
    WorkspaceModulesEndpoint,
    WorkspaceModulesLiteEndpoint,
    WorkspaceCyclesEndpoint,
    WorkspaceCyclesLiteEndpoint,
    WorkspaceFavoriteEndpoint,
    WorkspaceFavoriteGroupEndpoint,
    WorkspaceDraftIssueViewSet,
    QuickLinkViewSet,
    UserRecentVisitViewSet,
    WorkspaceHomePreferenceViewSet,
    WorkspaceStickyViewSet,
    WorkspaceUserPreferenceViewSet,
    WorkspaceMemberUserOnboardingEndpoint,
)


urlpatterns = [
    path(
        "workspace-slug-check/",
        WorkSpaceAvailabilityCheckEndpoint.as_view(),
        name="workspace-availability",
    ),
    path(
        "workspaces/",
        # TODO: "get": "list" removed — unused by FE (uses UserWorkSpacesEndpoint). Migrate to @can before re-enabling.
        WorkSpaceViewSet.as_view({"post": "create"}),
        name="workspace",
    ),
    path(
        "workspaces/<str:slug>/",
        # TODO: "put": "update" removed — unused by FE (uses PATCH only). Migrate to @can before re-enabling.
        WorkSpaceViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="workspace",
    ),
    path(
        "workspaces/<str:slug>/invitations/",
        WorkspaceInvitationsViewset.as_view({"get": "list", "post": "create"}),
        name="workspace-invitations",
    ),
    path(
        "workspaces/<str:slug>/invitations/<uuid:pk>/",
        WorkspaceInvitationsViewset.as_view({"delete": "destroy", "get": "retrieve", "patch": "partial_update"}),
        name="workspace-invitations",
    ),
    # user workspace invitations
    path(
        "users/me/workspaces/invitations/",
        UserWorkspaceInvitationsViewSet.as_view({"get": "list", "post": "create"}),
        name="user-workspace-invitations",
    ),
    path(
        "workspaces/<str:slug>/invitations/<uuid:pk>/join/",
        WorkspaceJoinEndpoint.as_view(),
        name="workspace-join",
    ),
    # user join workspace
    path(
        "workspaces/<str:slug>/members/",
        WorkSpaceMemberViewSet.as_view({"get": "list"}),
        name="workspace-member",
    ),
    path(
        "workspaces/<str:slug>/members-lite/",
        WorkSpaceMemberViewSet.as_view({"get": "lite"}),
        name="workspace-members-lite",
    ),
    path(
        "workspaces/<str:slug>/project-members/",
        WorkspaceProjectMemberEndpoint.as_view(),
        name="workspace-member-roles",
    ),
    path(
        "workspaces/<str:slug>/project-members-lite/",
        WorkspaceProjectMembersLiteEndpoint.as_view(),
        name="workspace-project-members-lite",
    ),
    path(
        "workspaces/<str:slug>/members/<uuid:pk>/",
        # TODO: retrieve action removed — not called by FE. Migrate to @can before re-enabling.
        WorkSpaceMemberViewSet.as_view({"patch": "partial_update", "delete": "destroy"}),
        name="workspace-member",
    ),
    path(
        "workspaces/<str:slug>/members/leave/",
        WorkSpaceMemberViewSet.as_view({"post": "leave"}),
        name="leave-workspace-members",
    ),
    path(
        "users/last-visited-workspace/",
        UserLastProjectWithWorkspaceEndpoint.as_view(),
        name="workspace-project-details",
    ),
    path(
        "workspaces/<str:slug>/preferences/",
        WorkspacePreferencesEndpoint.as_view(),
        name="workspace-preferences",
    ),
    path(
        "workspaces/<str:slug>/workspace-views/",
        WorkspaceMemberUserViewsEndpoint.as_view(),
        name="workspace-member-views-details",
    ),
    # TODO: Unused endpoint — not called by FE. Migrate to @can before re-enabling.
    # path(
    #     "workspaces/<str:slug>/workspace-themes/",
    #     WorkspaceThemeViewSet.as_view({"get": "list", "post": "create"}),
    #     name="workspace-themes",
    # ),
    # path(
    #     "workspaces/<str:slug>/workspace-themes/<uuid:pk>/",
    #     WorkspaceThemeViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"}),
    #     name="workspace-themes",
    # ),
    path(
        "workspaces/<str:slug>/user-stats/<uuid:user_id>/",
        WorkspaceUserProfileStatsEndpoint.as_view(),
        name="workspace-user-stats",
    ),
    path(
        "workspaces/<str:slug>/user-activity/<uuid:user_id>/",
        WorkspaceUserActivityEndpoint.as_view(),
        name="workspace-user-activity",
    ),
    path(
        "workspaces/<str:slug>/user-activity/<uuid:user_id>/export/",
        ExportWorkspaceUserActivityEndpoint.as_view(),
        name="export-workspace-user-activity",
    ),
    path(
        "workspaces/<str:slug>/user-profile/<uuid:user_id>/",
        WorkspaceUserProfileEndpoint.as_view(),
        name="workspace-user-profile-page",
    ),
    path(
        "workspaces/<str:slug>/user-profile/<uuid:user_id>/project-stats/",
        WorkspaceUserProfileProjectStatsEndpoint.as_view(),
        name="workspace-user-profile-project-stats",
    ),
    path(
        "workspaces/<str:slug>/user-issues/<uuid:user_id>/",
        WorkspaceUserProfileIssuesEndpoint.as_view(),
        name="workspace-user-profile-issues",
    ),
    path(
        "workspaces/<str:slug>/user-work-items/<uuid:user_id>/total-count/",
        WorkspaceUserProfileIssuesTotalCountEndpoint.as_view(),
        name="workspace-user-profile-issues-total-count",
    ),
    path(
        "workspaces/<str:slug>/labels/",
        WorkspaceLabelsEndpoint.as_view(),
        name="workspace-labels",
    ),
    path(
        "workspaces/<str:slug>/labels-lite/",
        WorkspaceLabelsLiteEndpoint.as_view(),
        name="workspace-labels-lite",
    ),
    path(
        "workspaces/<str:slug>/page-labels/",
        PageLabelsEndpoint.as_view(),
        name="workspace-page-labels",
    ),
    path(
        "workspaces/<str:slug>/page-labels/<uuid:page_label_id>/",
        PageLabelDetailEndpoint.as_view(),
        name="workspace-page-labels-detail",
    ),
    path(
        "workspaces/<str:slug>/user-properties/",
        WorkspaceUserPropertiesEndpoint.as_view(),
        name="workspace-user-filters",
    ),
    path(
        "workspaces/<str:slug>/states/",
        WorkspaceStatesEndpoint.as_view(),
        name="workspace-state",
    ),
    path(
        "workspaces/<str:slug>/states/<uuid:pk>/",
        WorkspaceStateDetailEndpoint.as_view(),
        name="workspace-state-detail",
    ),
    path(
        "workspaces/<str:slug>/states-lite/",
        WorkspaceStatesLiteEndpoint.as_view(),
        name="workspace-states-lite",
    ),
    path(
        "workspaces/<str:slug>/estimates/",
        WorkspaceEstimatesEndpoint.as_view(),
        name="workspace-estimate",
    ),
    path(
        "workspaces/<str:slug>/modules/",
        WorkspaceModulesEndpoint.as_view(),
        name="workspace-modules",
    ),
    path(
        "workspaces/<str:slug>/modules-lite/",
        WorkspaceModulesLiteEndpoint.as_view(),
        name="workspace-modules-lite",
    ),
    path(
        "workspaces/<str:slug>/cycles/",
        WorkspaceCyclesEndpoint.as_view(),
        name="workspace-cycles",
    ),
    path(
        "workspaces/<str:slug>/cycles-lite/",
        WorkspaceCyclesLiteEndpoint.as_view(),
        name="workspace-cycles-lite",
    ),
    path(
        "workspaces/<str:slug>/user-favorites/",
        WorkspaceFavoriteEndpoint.as_view(),
        name="workspace-user-favorites",
    ),
    path(
        "workspaces/<str:slug>/user-favorites/<uuid:favorite_id>/",
        WorkspaceFavoriteEndpoint.as_view(),
        name="workspace-user-favorites",
    ),
    path(
        "workspaces/<str:slug>/user-favorites/<uuid:favorite_id>/group/",
        WorkspaceFavoriteGroupEndpoint.as_view(),
        name="workspace-user-favorites-groups",
    ),
    path(
        "workspaces/<str:slug>/draft-issues/",
        WorkspaceDraftIssueViewSet.as_view({"get": "list", "post": "create"}),
        name="workspace-draft-issues",
    ),
    path(
        "workspaces/<str:slug>/draft-issues/<uuid:pk>/",
        WorkspaceDraftIssueViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"}),
        name="workspace-drafts-issues",
    ),
    path(
        "workspaces/<str:slug>/draft-to-issue/<uuid:draft_id>/",
        WorkspaceDraftIssueViewSet.as_view({"post": "create_draft_to_issue"}),
        name="workspace-drafts-issues",
    ),
    # quick link
    path(
        "workspaces/<str:slug>/quick-links/",
        QuickLinkViewSet.as_view({"get": "list", "post": "create"}),
        name="workspace-quick-links",
    ),
    path(
        "workspaces/<str:slug>/quick-links/<uuid:pk>/",
        QuickLinkViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"}),
        name="workspace-quick-links",
    ),
    # Widgets
    path(
        "workspaces/<str:slug>/home-preferences/",
        WorkspaceHomePreferenceViewSet.as_view(),
        name="workspace-home-preference",
    ),
    path(
        "workspaces/<str:slug>/home-preferences/<str:key>/",
        WorkspaceHomePreferenceViewSet.as_view(),
        name="workspace-home-preference",
    ),
    path(
        "workspaces/<str:slug>/recent-visits/",
        UserRecentVisitViewSet.as_view({"get": "list"}),
        name="workspace-recent-visits",
    ),
    path(
        "workspaces/<str:slug>/stickies/",
        WorkspaceStickyViewSet.as_view({"get": "list", "post": "create"}),
        name="workspace-sticky",
    ),
    path(
        "workspaces/<str:slug>/stickies/<uuid:pk>/",
        WorkspaceStickyViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"}),
        name="workspace-sticky",
    ),
    # User Preference
    path(
        "workspaces/<str:slug>/sidebar-preferences/",
        WorkspaceUserPreferenceViewSet.as_view(),
        name="workspace-user-preference",
    ),
    # Onboarding product tour
    path(
        "workspaces/<str:slug>/workspace-member/me/onboarding/",
        WorkspaceMemberUserOnboardingEndpoint.as_view(),
        name="workspace-member-onboarding",
    ),
    # Workspace audit logs (admin/owner only)
    path(
        "workspaces/<str:slug>/audit-logs/",
        WorkspaceAuditLogEndpoint.as_view(),
        name="workspace-audit-logs",
    ),
    path(
        "workspaces/<str:slug>/audit-logs/export/",
        WorkspaceAuditLogExportEndpoint.as_view(),
        name="workspace-audit-logs-export",
    ),
    path(
        "workspaces/<str:slug>/audit-logs/export/<uuid:pk>/download/",
        WorkspaceAuditLogExportDownloadEndpoint.as_view(),
        name="workspace-audit-logs-export-download",
    ),
    path(
        "workspaces/<str:slug>/audit-logs/verify/",
        WorkspaceAuditLogVerifyEndpoint.as_view(),
        name="workspace-audit-logs-verify",
    ),
    path(
        "workspaces/<str:slug>/workspace-members/me/",
        WorkspaceMemberUserEndpoint.as_view(),
        name="workspace-member-details",
    ),
    path(
        "users/me/workspaces/<str:slug>/project-roles/",
        UserWorkspaceProjectRolesEndpoint.as_view(),
        name="user-workspace-project-roles",
    ),
]
