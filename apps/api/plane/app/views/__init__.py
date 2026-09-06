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
)

from .project.label import (
    ProjectLabelsEndpoint,
    ProjectLabelDetailEndpoint,
)

from .project.label_import import ProjectLabelsImportEndpoint

from .project.subscriber import ProjectSubscriberEndpoint

from .project.audit_log import (
    ProjectAuditLogEndpoint,
    ProjectAuditLogExportDownloadEndpoint,
    ProjectAuditLogExportEndpoint,
)

from .user.base import (
    UserEndpoint,
    UpdateUserOnBoardedEndpoint,
    UpdateUserTourCompletedEndpoint,
    UserActivityEndpoint,
)


from .base import BaseAPIView, BaseViewSet
from .work_item_types import ProjectWorkItemTypesLiteEndpoint

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
from .workspace.label import WorkspaceLabelsEndpoint, WorkspaceLabelsLiteEndpoint
from .workspace.page_label import PageLabelDetailEndpoint, PageLabelsEndpoint
from .workspace.state import (
    WorkspaceStatesEndpoint,
    WorkspaceStateDetailEndpoint,
    WorkspaceStatesLiteEndpoint,
)
from .workspace.audit_log import (
    WorkspaceAuditLogEndpoint,
    WorkspaceAuditLogExportEndpoint,
    WorkspaceAuditLogExportDownloadEndpoint,
    WorkspaceAuditLogVerifyEndpoint,
)
from .workspace.user import (
    UserLastProjectWithWorkspaceEndpoint,
    WorkspaceUserProfileIssuesEndpoint,
    WorkspaceUserProfileIssuesTotalCountEndpoint,
    WorkspaceUserPropertiesEndpoint,
    WorkspaceUserProfileEndpoint,
    WorkspaceUserProfileProjectStatsEndpoint,
    WorkspaceUserActivityEndpoint,
    WorkspaceUserProfileStatsEndpoint,
    UserActivityGraphEndpoint,
    UserIssueCompletedGraphEndpoint,
)
from .workspace.estimate import WorkspaceEstimatesEndpoint
from .workspace.module import WorkspaceModulesEndpoint, WorkspaceModulesLiteEndpoint
from .workspace.cycle import WorkspaceCyclesEndpoint, WorkspaceCyclesLiteEndpoint
from .workspace.quick_link import QuickLinkViewSet
from .workspace.sticky import WorkspaceStickyViewSet

from .state.base import StateViewSet, IntakeStateEndpoint
from .view.base import (
    WorkspaceViewViewSet,
    WorkspaceViewIssuesViewSet,
    IssueViewViewSet,
    IssueViewFavoriteViewSet,
)
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
from .asset.export import ExportAssetsEndpoint
from .asset.silo import SiloAssetsEndpoint

from .release import (
    ReleaseEndpoint,
    ReleaseTagEndpoint,
    ReleaseLabelEndpoint,
    ReleaseCommentViewSet,
    ReleaseCommentReactionViewSet,
    ReleaseWorkItemEndpoint,
    ReleaseWorkItemTotalCountEndpoint,
    ReleaseActivityEndpoint,
    ReleaseChangelogEndpoint,
    ReleaseLinkViewSet,
    ReleasePageEndpoint,
    ReleaseAttachmentEndpoint,
)

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

from .issue.work_item import (
    WorkItemListProjectEndpoint,
    WorkItemListWorkspaceEndpoint,
    WorkspaceWorkItemsLiteEndpoint,
)

from .issue.activity import IssueActivityEndpoint

from .issue.state_duration import WorkItemStateDurationEndpoint

from .issue.archive import IssueArchiveViewSet

from .issue.attachment import (
    IssueAttachmentEndpoint,
    # V2
    IssueAttachmentV2Endpoint,
)

from .issue.comment import IssueCommentViewSet, CommentReactionViewSet, IssueCommentRepliesEndpoint

from .issue.label import LabelViewSet, BulkCreateIssueLabelsEndpoint

from .issue.link import IssueLinkViewSet

from .issue.reaction import IssueReactionViewSet

from .issue.sub_issue import SubIssuesEndpoint

from .issue.subscriber import IssueSubscriberViewSet

from .issue.version import IssueVersionEndpoint, WorkItemDescriptionVersionEndpoint

from .module.base import (
    ModuleViewSet,
    ModuleLinkViewSet,
    ModuleFavoriteViewSet,
    ModuleUserPropertiesEndpoint,
)

from .module.issue import ModuleIssueViewSet

from .module.archive import ModuleArchiveUnarchiveEndpoint

from .api import ApiTokenEndpoint, ServiceApiTokenEndpoint, WorkspaceAPITokenEndpoint

from .page.base import (
    PageViewSet,
    PageFavoriteViewSet,
    PagesDescriptionViewSet,
    PageDuplicateEndpoint,
)
from .page.live import PagesLiveServerDescriptionViewSet
from .page.subscriber import PageSubscriberViewSet
from .page.version import PageVersionEndpoint

from .search.base import GlobalSearchEndpoint, SearchEndpoint
from .search.issue import IssueSearchEndpoint, WorkspaceWorkItemSearchEndpoint

from .search.workspace import WorkspaceSearchEndpoint

from .external.base import (
    GPTIntegrationEndpoint,
    UnsplashEndpoint,
    WorkspaceGPTIntegrationEndpoint,
)
from .estimate.base import (
    ProjectEstimatePointEndpoint,
    BulkEstimatePointEndpoint,
    EstimatePointEndpoint,
)

from .intake.base import (
    IntakeViewSet,
    IntakeIssueViewSet,
    IntakeWorkItemDescriptionVersionEndpoint,
)

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

from .notification.base import (
    NotificationViewSet,
    UnreadNotificationEndpoint,
    UserNotificationPreferenceEndpoint,
)


from .webhook.base import (
    WebhookEndpoint,
    WebhookLogsEndpoint,
    WebhookSecretRegenerateEndpoint,
)

from .error_404 import custom_404_view

from .importer.base import (
    ServiceIssueImportSummaryEndpoint,
    ImportServiceEndpoint,
    UpdateServiceImportStatusEndpoint,
    BulkImportIssuesEndpoint,
    BulkImportModulesEndpoint,
)

from .integration.base import IntegrationViewSet, WorkspaceIntegrationViewSet

from .integration.github import (
    GithubRepositoriesEndpoint,
    GithubRepositorySyncViewSet,
    GithubIssueSyncViewSet,
    GithubCommentSyncViewSet,
    BulkCreateGithubIssueSyncEndpoint,
)

from .integration.slack import SlackProjectSyncViewSet

from .notification.base import MarkAllReadNotificationViewSet

from .user.base import (
    AccountEndpoint,
    ProfileEndpoint,
    UserSessionEndpoint,
    UserTokenVerificationEndpoint,
)

from .timezone.base import TimezoneEndpoint


from .asset.proxy import ProxyUploadEndpoint, ProxyDownloadEndpoint
from .asset.external_asset_edit import (
    WorkspaceAssetExternalEditEndpoint,
    ProjectAssetExternalEditEndpoint,
)

from .exporter.base import ExportIssuesEndpoint, ExportIssueDownloadEndpoint
from .exporter.worklog import WorkspaceExportWorkLogsDownloadEndpoint, ProjectExportWorkLogsDownloadEndpoint


# work item relation definition
from .issue.relation_definition import WorkItemRelationDefinitionViewSet

# work item relation
from .issue.relation import IssueRelationViewSet, WorkItemRelationDependencyViewSet, WorkItemRelationRelationViewSet

# hierarchy search endpoints
from .issue.sub_issue import SubWorkitemSearchEndpoint, ParentWorkitemSearchEndpoint
from .issue.vote import IssueVoteEndpoint

from .desktop.handoff import (
    HandoffNonceEndpoint,
    HandoffAckEndpoint,
    HandoffStatusEndpoint,
)

# dashboard
from .dashboard import DashboardCopyEndpoint
