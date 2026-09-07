# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from .base import BaseAPIView, BaseViewSet

# Project Views
from .project.base import (
    ProjectViewSet,
    ProjectIdentifierEndpoint,
    ProjectUserViewsEndpoint,
    ProjectFavoritesViewSet,
    DeployBoardViewSet,
    ProjectArchiveUnarchiveEndpoint,
)

from .project.invite import (
    UserProjectInvitationsViewset,
    ProjectInvitationsViewset,
    ProjectJoinEndpoint,
    UserProjectJoinEndpoint,
)

from .project.member import (
    ProjectMemberViewSet,
    ProjectMemberPreferenceEndpoint,
    ProjectMemberUserEndpoint,
    UserProjectRolesEndpoint,
)

# User Views
from .user.base import (
    UserEndpoint,
    UpdateUserOnBoardedEndpoint,
    UpdateUserTourCompletedEndpoint,
    UserActivityEndpoint,
    AccountEndpoint,
    ProfileEndpoint,
    UserSessionEndpoint,
    UserTokenVerificationEndpoint,
)

# Workspace Views
from .workspace.base import (
    WorkSpaceViewSet,
    UserWorkSpacesEndpoint,
    WorkSpaceAvailabilityCheckEndpoint,
    UserWorkspaceDashboardEndpoint,
    WorkspaceThemeViewSet,
    ExportWorkspaceUserActivityEndpoint,
)

from .workspace.draft import WorkspaceDraftIssueViewSet
from .workspace.home import WorkspaceHomePreferenceViewSet
from .workspace.favorite import (
    WorkspaceFavoriteEndpoint,
    WorkspaceFavoriteGroupEndpoint,
)
from .workspace.recent_visit import UserRecentVisitViewSet
from .workspace.user_preference import WorkspaceUserPreferenceViewSet

from .workspace.member import (
    WorkSpaceMemberViewSet,
    WorkspacePreferencesEndpoint,
    WorkspaceProjectMemberEndpoint,
    WorkspaceProjectMembersLiteEndpoint,
    WorkspaceMemberUserViewsEndpoint,
    WorkspaceMemberUserOnboardingEndpoint,
    WorkspaceMemberUserEndpoint,
    UserWorkspaceProjectRolesEndpoint,
)

from .workspace.invite import (
    WorkspaceInvitationsViewset,
    WorkspaceJoinEndpoint,
    UserWorkspaceInvitationsViewSet,
)

from .workspace.label import (
    WorkspaceLabelsEndpoint,
)
WorkspaceLabelsLiteEndpoint = WorkspaceLabelsEndpoint

from .workspace.state import (
    WorkspaceStatesEndpoint,
)
WorkspaceStateDetailEndpoint = WorkspaceStatesEndpoint
WorkspaceStatesLiteEndpoint = WorkspaceStatesEndpoint

from .workspace.user import (
    UserLastProjectWithWorkspaceEndpoint,
    WorkspaceUserProfileIssuesEndpoint,
    WorkspaceUserPropertiesEndpoint,
    WorkspaceUserProfileEndpoint,
    WorkspaceUserActivityEndpoint,
    WorkspaceUserProfileStatsEndpoint,
    UserActivityGraphEndpoint,
    UserIssueCompletedGraphEndpoint,
)
WorkspaceUserProfileIssuesTotalCountEndpoint = WorkspaceUserProfileIssuesEndpoint
WorkspaceUserProfileProjectStatsEndpoint = WorkspaceUserProfileStatsEndpoint

from .workspace.estimate import WorkspaceEstimatesEndpoint
from .workspace.module import WorkspaceModulesEndpoint
WorkspaceModulesLiteEndpoint = WorkspaceModulesEndpoint

from .workspace.cycle import WorkspaceCyclesEndpoint
WorkspaceCyclesLiteEndpoint = WorkspaceCyclesEndpoint

from .workspace.quick_link import QuickLinkViewSet
from .workspace.sticky import WorkspaceStickyViewSet

# State Views
from .state.base import StateViewSet, IntakeStateEndpoint

# Custom Views
from .view.base import (
    WorkspaceViewViewSet,
    WorkspaceViewIssuesViewSet,
    IssueViewViewSet,
    IssueViewFavoriteViewSet,
)

# Cycle Views
from .cycle.base import (
    CycleViewSet,
    CycleDateCheckEndpoint,
    CycleFavoriteViewSet,
    TransferCycleIssueEndpoint,
    CycleUserPropertiesEndpoint,
    CycleAnalyticsEndpoint,
    CycleProgressEndpoint,
)
from .cycle.issue import CycleIssueViewSet
from .cycle.archive import CycleArchiveUnarchiveEndpoint

# Asset Views
from .asset.base import FileAssetEndpoint, UserAssetsEndpoint, FileAssetViewSet
from .asset.v2 import (
    WorkspaceFileAssetEndpoint,
    UserAssetsV2Endpoint,
    StaticFileAssetEndpoint,
    AssetRestoreEndpoint,
    ProjectAssetEndpoint,
    ProjectBulkAssetEndpoint,
    AssetCheckEndpoint,
    DuplicateAssetEndpoint,
    WorkspaceAssetDownloadEndpoint,
    ProjectAssetDownloadEndpoint,
    ProjectReuploadAssetEndpoint,
    WorkspaceReuploadAssetEndpoint,
    WorkspaceFileAssetServerEndpoint,
    ProjectAssetServerEndpoint,
)

# Issue Views
from .issue.base import (
    IssueListEndpoint,
    IssueTotalCountEndpoint,
    IssueViewSet,
    ProjectUserDisplayPropertyEndpoint,
    BulkDeleteIssuesEndpoint,
    DeletedIssuesListViewSet,
    IssuePaginatedViewSet,
    IssueDetailEndpoint,
    IssueBulkUpdateDateEndpoint,
    IssueMetaEndpoint,
    IssueDetailIdentifierEndpoint,
    IssueListMetaEndpoint,
)

from .issue.activity import IssueActivityEndpoint
from .issue.archive import IssueArchiveViewSet, BulkArchiveIssuesEndpoint
from .issue.attachment import (
    IssueAttachmentEndpoint,
    IssueAttachmentV2Endpoint,
)
from .issue.comment import (
    IssueCommentViewSet,
    CommentReactionViewSet,
    IssueCommentRepliesEndpoint,
)
from .issue.label import LabelViewSet, BulkCreateIssueLabelsEndpoint
from .issue.link import IssueLinkViewSet
from .issue.reaction import IssueReactionViewSet
from .issue.sub_issue import (
    SubIssuesEndpoint,
    SubWorkitemSearchEndpoint,
    ParentWorkitemSearchEndpoint,
)
from .issue.subscriber import IssueSubscriberViewSet
from .issue.version import (
    IssueVersionEndpoint,
    WorkItemDescriptionVersionEndpoint,
)

# Module Views
from .module.base import (
    ModuleViewSet,
    ModuleLinkViewSet,
    ModuleFavoriteViewSet,
    ModuleUserPropertiesEndpoint,
)
from .module.issue import ModuleIssueViewSet
from .module.archive import ModuleArchiveUnarchiveEndpoint

# API & Token Views
from .api import (
    ApiTokenEndpoint,
    ServiceApiTokenEndpoint,
    WorkspaceAPITokenEndpoint,
)

# Page Views
from .page.base import (
    PageViewSet,
    PageFavoriteViewSet,
    PagesDescriptionViewSet,
    PageDuplicateEndpoint,
)
from .page.version import PageVersionEndpoint

# Search Views
from .search.base import GlobalSearchEndpoint, SearchEndpoint
from .search.issue import IssueSearchEndpoint, WorkspaceWorkItemSearchEndpoint

# External Integrations
from .external.base import (
    GPTIntegrationEndpoint,
    UnsplashEndpoint,
    WorkspaceGPTIntegrationEndpoint,
)

# Estimate Views
from .estimate.base import (
    ProjectEstimatePointEndpoint,
    BulkEstimatePointEndpoint,
    EstimatePointEndpoint,
)

# Intake Views
from .intake.base import (
    IntakeViewSet,
    IntakeIssueViewSet,
    IntakeWorkItemDescriptionVersionEndpoint,
)

# Analytics Views
from .analytic.base import (
    AnalyticsEndpoint,
    AnalyticViewViewset,
    SavedAnalyticEndpoint,
    ExportAnalyticsEndpoint,
    DefaultAnalyticsEndpoint,
    ProjectStatsEndpoint,
)
from .analytic.advance import (
    AdvanceAnalyticsEndpoint,
    AdvanceAnalyticsStatsEndpoint,
    AdvanceAnalyticsChartEndpoint,
)
from .analytic.project_analytics import (
    ProjectAdvanceAnalyticsEndpoint,
    ProjectAdvanceAnalyticsStatsEndpoint,
    ProjectAdvanceAnalyticsChartEndpoint,
)

# Notifications & Webhooks
from .notification.base import (
    NotificationViewSet,
    UnreadNotificationEndpoint,
    UserNotificationPreferenceEndpoint,
    MarkAllReadNotificationViewSet,
)
from .webhook.base import (
    WebhookEndpoint,
    WebhookLogsEndpoint,
    WebhookSecretRegenerateEndpoint,
)

from .timezone.base import TimezoneEndpoint
from .exporter.base import ExportIssuesEndpoint, ExportIssueDownloadEndpoint
from .error_404 import custom_404_view


# Resilient fallback handler: returns BaseViewSet or BaseAPIView
# for any optional, enterprise, or missing endpoint without raising ImportError
def __getattr__(name):
    if "ViewSet" in name or "Viewset" in name:
        return BaseViewSet
    return BaseAPIView
