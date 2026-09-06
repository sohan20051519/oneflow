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

# Python imports
import json
import logging

# Django imports
from django.db.models import Count, Prefetch, Q, Exists, OuterRef
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder

# Third party modules
from rest_framework import status
from rest_framework.response import Response

from plane.permissions import (
    WorkspacePermissions,
    WorkspaceMemberPermissions,
    ProjectMemberPermissions,
    PermissionContext,
    permission_engine,
    can,
)
from plane.permissions.system_roles import (
    get_workspace_role_slug,
    get_workspace_roles_for_workspace,
    can_manage_role,
    can_assign_role,
    member_role_from_role_ref,
    role_from_member_role,
    ROLE_SLUG_MAP,
)
from plane.utils.member_listing import (
    search_members,
    filter_members_by_roles,
    order_members,
    parse_roles_param,
)
from plane.utils.filters import MemberFilterSet

# Module imports
from plane.app.serializers import (
    ProjectMemberRoleSerializer,
    ProjectMembersLiteSerializer,
    WorkspaceMemberAdminSerializer,
    WorkspaceMemberDataLayerLiteSerializer,
    WorkspaceAgentAppSerializer,
    WorkspacePreferencesSerializer,
    WorkSpaceMemberSerializer,
    WorkspaceMemberUserOnboardingSerializer,
)
from plane.app.views.base import BaseAPIView
from plane.utils.cache import invalidate_cache
from plane.utils.global_paginator import paginate
from plane.utils.uuid import parse_uuid_list
from plane.db.models import (
    Project,
    ProjectMember,
    WorkspaceMember,
    BotTypeEnum,
    User,
)
from plane.authentication.models import WorkspaceAppInstallation
from plane.ee.models import TeamspaceMember, PageUser
from plane.payment.bgtasks.member_sync_task import member_sync_task
from plane.payment.flags.flag import FeatureFlag
from plane.payment.flags.flag_decorator import check_workspace_feature_flag
from plane.payment.utils.member_payment_count import workspace_member_check
from .. import BaseViewSet
from plane.ee.bgtasks.workspace_member_activities_task import workspace_members_activity

logger = logging.getLogger("plane.api")


class WorkSpaceMemberViewSet(BaseViewSet):
    serializer_class = WorkspaceMemberAdminSerializer
    model = WorkspaceMember
    filterset_class = MemberFilterSet

    search_fields = ["member__display_name", "member__first_name"]
    use_read_replica = True

    def get_queryset(self):
        return self.filter_queryset(
            super()
            .get_queryset()
            .filter(workspace_id=self.request.workspace_id)
            .select_related("member", "member__avatar_asset", "role_ref")
        )

    @can(WorkspaceMemberPermissions.VIEW, resource_param="workspace_id")
    def lite(self, request, slug):
        """Resource-data-layer lite roster. Three modes:

          • ``?ids=``  → by-id resolver: member identities only, UNPAGINATED (the stray-reference
            fallback). Unchanged.
          • default    → cursor-paginated ``TPaginatedResponse`` of the full roster rows (incl.
            suspended + bots), ordered by ``member__display_name`` — backs the paginated member picker
            (the lite endpoint is the picker's data source now that the eager bootstrap is gone).
          • ``?filter=assignable|mentionable|invitable|active`` → server-side visibility predicate
            mirroring the FE curated lists; ``?search=`` narrows by name. No filter = everyone (parity
            with old roster). ``active`` = active members incl. guests + mentionable bots (the Inbox
            "Notification from" picker). ``invitable`` additionally excludes members already on
            ``?project_id=``'s roster — the project "invite member" picker's data source.

        TODO(members-authorized-listing): harden with AuthorizedListingView + `.authorized_for()` +
        a `WorkspaceMember.PermissionMeta.scope_map` (per the migrate-resource playbook). Gated by
        `@can(VIEW)` today — parity with the existing member-list endpoint.
        """

        queryset = (
            WorkspaceMember.objects.filter(workspace__slug=slug)
            .annotate(
                is_mentionable=Exists(
                    WorkspaceAppInstallation.objects.filter(
                        app_bot_id=OuterRef("member_id"),
                        application__is_mentionable=True,
                    )
                ),
            )
            .filter(
                Q(member__is_bot=True, is_mentionable=True)
                | Q(member__is_bot=False)
                | Q(member__is_bot=True, member__bot_type=BotTypeEnum.NATIVE_AGENT_BOT.value)
            )
            .select_related("member", "member__avatar_asset", "role_ref")
            .order_by("member__display_name")
        )

        # by-id mode: unchanged — filter to the requested ids and return member IDENTITY only
        if "ids" in request.GET:
            member_ids = parse_uuid_list(request.GET.get("ids", ""))
            rows = WorkspaceMemberDataLayerLiteSerializer(queryset.filter(member_id__in=member_ids), many=True).data
            return Response([row["member"] for row in rows], status=status.HTTP_200_OK)

        # server-side visibility predicate (mirrors the FE curated lists: getActive*/getAssignable*/getMentionable*)
        filter_param = request.GET.get("filter")
        if filter_param in ("assignable", "mentionable", "invitable", "active"):
            queryset = queryset.filter(is_active=True)
            # `active` adds no further narrowing beyond is_active — active members incl. guests and
            # mentionable bots (parity with the FE `getActiveWorkspaceMemberSummaries` roster, which is
            # derived from this same base queryset). Backs the Inbox "Notification from" filter.
            if filter_param == "assignable":
                # drop guests: the role_ref slug OR the legacy numeric fallback (role=5, role_ref null),
                # matching get_role_slug() / isGuestRole(role_slug === "guest").
                queryset = queryset.exclude(Q(role_ref__slug="guest") | Q(role_ref__isnull=True, role=5))
            elif filter_param == "invitable":
                queryset = queryset.filter(member__is_bot=False)  # bots are never invitable

                project_id = request.GET.get("project_id")
                if project_id:
                    queryset = queryset.exclude(
                        member_id__in=ProjectMember.objects.filter(
                            project_id=project_id, workspace__slug=slug, is_active=True
                        ).values_list("member_id", flat=True)
                    )

                # the teamspace add-members picker: exclude members already on the teamspace's roster.
                # Teamspaces don't admit guests (the add-member endpoint drops them), so exclude guests
                # here too, keeping the picker in parity with what can actually be added.
                exclude_teamspace_id = request.GET.get("exclude_teamspace_id")
                if exclude_teamspace_id:
                    queryset = queryset.exclude(Q(role_ref__slug="guest") | Q(role_ref__isnull=True, role=5)).exclude(
                        member_id__in=TeamspaceMember.objects.filter(
                            team_space_id=exclude_teamspace_id, workspace_id=request.workspace_id
                        ).values_list("member_id", flat=True)
                    )

        queryset = self.filter_queryset(queryset)

        # ?search= — case-insensitive substring across the three name fields
        search = request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(member__display_name__icontains=search)
                | Q(member__first_name__icontains=search)
                | Q(member__last_name__icontains=search)
            )

        return Response(
            paginate(
                base_queryset=queryset,
                queryset=queryset,
                cursor=request.GET.get("cursor"),
                on_result=lambda members: WorkspaceMemberDataLayerLiteSerializer(members, many=True).data,
                max_limit=100,
                per_page=request.GET.get("per_page"),
            ),
            status=status.HTTP_200_OK,
        )

    @can(WorkspaceMemberPermissions.VIEW, resource_param="workspace_id")
    def list(self, request, slug):
        # The "Agents and apps" settings tab is the bot-member slice of this same roster (bots that
        # are the app_bot of an installed app), served here so the FE reuses one endpoint/paginator.
        if request.GET.get("membership_type") == "agents_apps":
            return self._list_agents_and_apps(request)

        workspace_member = WorkspaceMember.objects.select_related("role_ref").get(
            member=request.user, workspace_id=request.workspace_id, is_active=True
        )
        is_admin = bool(workspace_member.role_ref and workspace_member.role_ref.slug != "guest")

        # The roster is unbounded (tens of thousands of members on large workspaces). It is
        # served as a cursor-paginated `TPaginatedResponse` with server-side search / role
        # filter / ordering (the settings list pipeline, previously client-side), so a page
        # only ever fetches ~25–100 rows. `.only()` keeps even that page from hydrating the
        # large `*_props` JSONB columns the serializers never render.
        queryset = self.get_queryset().only(
            "id",
            "role",
            "role_ref_id",
            "is_active",
            "created_at",
            "member__id",
            "member__first_name",
            "member__last_name",
            "member__avatar",
            "member__avatar_asset_id",
            "member__is_bot",
            "member__display_name",
            "member__email",
            "member__last_login_medium",
            "member__avatar_asset__id",
            "member__avatar_asset__entity_type",
            "role_ref__id",
            "role_ref__slug",
        )
        # People tab excludes bots (agents/apps live on their own tab). Absent `membership_type` keeps
        # the historical behaviour (humans + bots), so other callers of this endpoint are unaffected.
        if request.GET.get("membership_type") == "people":
            queryset = queryset.filter(member__is_bot=False)
        queryset = search_members(queryset, request.GET.get("search"))
        queryset = filter_members_by_roles(queryset, parse_roles_param(request), ROLE_SLUG_MAP)
        queryset = order_members(queryset, request.GET.get("order_by"), ROLE_SLUG_MAP)

        serializer_class = WorkspaceMemberAdminSerializer if is_admin else WorkSpaceMemberSerializer
        # `self.paginate` (BasePaginator) reads `cursor`/`per_page` off the request itself and returns
        # the `total_count` + `next_cursor` envelope the data layer's `paginatedScopeResult` consumes —
        # same call shape as the cycle list endpoint.
        return self.paginate(
            request=request,
            queryset=queryset,
            on_results=lambda members: serializer_class(members, many=True).data,
            default_per_page=25,
            max_per_page=100,
        )

    def _list_agents_and_apps(self, request):
        """The `?membership_type=agents_apps` roster: workspace bot members that are either the
        `app_bot` of an INSTALLED `WorkspaceAppInstallation`, or a native agent (`bot_type
        NATIVE_AGENT_BOT`) — native agents have no installation record, so they're included
        unconditionally. Each row's installation (if any) is attached via a filtered prefetch, and each
        native agent's `NativeAgent.created_by` is attached via select_related, so the serializer renders
        `type` / `created_by` without an N+1. Silo and internal system bots have no installation and
        aren't native agents, so only real installed apps/agents and native agents appear here."""
        installed = WorkspaceAppInstallation.objects.filter(
            workspace_id=request.workspace_id,
            status=WorkspaceAppInstallation.Status.INSTALLED,
        )
        queryset = (
            WorkspaceMember.objects.filter(workspace_id=request.workspace_id, is_active=True)
            .filter(
                Q(member_id__in=installed.filter(app_bot__isnull=False).values_list("app_bot_id", flat=True))
                | Q(member__is_bot=True, member__bot_type=BotTypeEnum.NATIVE_AGENT_BOT.value)
            )
            .select_related(
                "member",
                "member__avatar_asset",
                # native agents have no installation row, so their creator comes from this join instead
                # (see WorkspaceAgentAppSerializer.get_created_by)
                "member__native_agent__created_by",
                "member__native_agent__created_by__avatar_asset",
            )
            .prefetch_related(
                Prefetch(
                    "member__app_bots",
                    # deterministic order so the serializer's first installation (→ created_by) is stable
                    # when a bot somehow has more than one installed record in the workspace.
                    queryset=installed.select_related("installed_by", "installed_by__avatar_asset").order_by(
                        "-created_at"
                    ),
                    to_attr="workspace_installations",
                )
            )
            # only the columns WorkspaceAgentAppSerializer reads — skips the large `*_props` JSONB
            # the People list guards the same way (see .only() in list()).
            .only(
                "id",
                "created_at",
                "member__id",
                "member__first_name",
                "member__last_name",
                "member__avatar",
                "member__avatar_asset_id",
                "member__is_bot",
                "member__bot_type",
                "member__display_name",
                "member__last_active",
                "member__avatar_asset__id",
                "member__avatar_asset__entity_type",
                "member__native_agent__id",
                "member__native_agent__created_by__id",
                "member__native_agent__created_by__first_name",
                "member__native_agent__created_by__last_name",
                "member__native_agent__created_by__display_name",
                "member__native_agent__created_by__avatar",
                "member__native_agent__created_by__is_bot",
                "member__native_agent__created_by__avatar_asset_id",
                "member__native_agent__created_by__avatar_asset__id",
                "member__native_agent__created_by__avatar_asset__entity_type",
            )
            .order_by("member__display_name", "id")
        )
        # `agent_type=agent|app` (the tab's Filters control) narrows by mentionability: an "agent" is
        # a mentionable app bot or a native agent (bot_type APP_BOT / NATIVE_AGENT_BOT, mirrors
        # WorkspaceAgentAppSerializer.get_type); an "app" is any other installed app bot.
        agent_type = request.GET.get("agent_type")
        mentionable_bot_types = [BotTypeEnum.APP_BOT.value, BotTypeEnum.NATIVE_AGENT_BOT.value]
        if agent_type == "agent":
            queryset = queryset.filter(member__bot_type__in=mentionable_bot_types)
        elif agent_type == "app":
            queryset = queryset.exclude(member__bot_type__in=mentionable_bot_types)
        queryset = search_members(queryset, request.GET.get("search"))
        return self.paginate(
            request=request,
            queryset=queryset,
            on_results=lambda members: WorkspaceAgentAppSerializer(members, many=True).data,
            default_per_page=25,
            max_per_page=100,
        )

    # TODO: Unused endpoint — not called by FE. Migrate to @can before re-enabling.
    def retrieve(self, request, slug, pk):
        workspace_member = WorkspaceMember.objects.select_related("role_ref").get(
            member=request.user, workspace__slug=slug, is_active=True
        )

        try:
            # Get the specific workspace member by pk
            member = self.get_queryset().get(pk=pk)
        except WorkspaceMember.DoesNotExist:
            return Response(
                {"error": "Workspace member not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if workspace_member.role_ref and workspace_member.role_ref.slug != "guest":
            serializer = WorkspaceMemberAdminSerializer(member)
        else:
            serializer = WorkSpaceMemberSerializer(member)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @can(WorkspaceMemberPermissions.CHANGE_ROLE, resource_param="pk")
    def partial_update(self, request, slug, pk):
        workspace_member = WorkspaceMember.objects.select_related("role_ref").get(
            pk=pk, workspace__slug=slug, member__is_bot=False, is_active=True
        )
        if request.user.id == workspace_member.member_id:
            return Response(
                {"error": "You cannot update your own role"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Tier protection — resolve actor role
        actor_member = WorkspaceMember.objects.select_related("role_ref").get(
            workspace__slug=slug, member=request.user, is_active=True
        )
        actor_slug = get_workspace_role_slug(actor_member)
        target_slug = get_workspace_role_slug(workspace_member)

        # Can the actor manage the target's CURRENT role?
        allowed, error = can_manage_role(actor_slug, target_slug)
        if not allowed:
            return Response({"error": error}, status=status.HTTP_403_FORBIDDEN)

        # Capture current state before mutation for accurate audit trail
        current_instance = json.dumps(WorkSpaceMemberSerializer(workspace_member).data, cls=DjangoJSONEncoder)

        # Resolve role_slug to role level if provided
        target_role = None
        target_ws_role = None
        if "role_slug" in request.data:
            ws_role_cache = get_workspace_roles_for_workspace(workspace_member.workspace_id)
            target_ws_role = ws_role_cache.get(request.data["role_slug"])
            if not target_ws_role:
                return Response(
                    {"error": f"Invalid role_slug: {request.data['role_slug']}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            target_role = member_role_from_role_ref(target_ws_role)
            # Can the actor assign the NEW role?
            allowed, error = can_assign_role(actor_slug, target_ws_role.slug)
            if not allowed:
                return Response({"error": error}, status=status.HTTP_403_FORBIDDEN)
            if target_ws_role.slug == "admin" and not check_workspace_feature_flag(
                feature_key=FeatureFlag.WORKSPACE_ADMIN_ROLE,
                slug=slug,
                user_id=str(request.user.id),
            ):
                return Response(
                    {"error": "Admin role is not available on this plan"},
                    status=status.HTTP_403_FORBIDDEN,
                )
        elif "role" in request.data:
            return Response(
                {"error": "Use role_slug instead of role"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if target_role is not None:
            # Seat limit check FIRST (before any side effects)
            allowed, _, _ = workspace_member_check(
                slug=slug,
                requested_role_slug=target_ws_role.slug if target_ws_role else None,
                current_role_slug=(
                    workspace_member.role_ref.slug
                    if workspace_member.role_ref
                    else role_from_member_role(workspace_member.role)
                ),
            )
            if not allowed:
                return Response(
                    {"error": "Cannot update the role as it exceeds the purchased seat limit"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Guest demotion side effects (only after seat check passes).
            # role_ref_id must be updated alongside role: role_ref is the source
            # of truth for permission resolution, and the post_bulk_update sync
            # handler reads role_ref.slug to compute the new ResourcePermission
            # relation. Updating only the legacy numeric role would leave
            # ResourcePermission pointing at the old project relation.
            if target_ws_role and target_ws_role.slug == "guest":
                from plane.db.models.permission import Role

                project_guest_role = Role.objects.filter(
                    workspace_id=workspace_member.workspace_id,
                    namespace="project",
                    slug="guest",
                    is_system=True,
                    deleted_at__isnull=True,
                ).first()
                if not project_guest_role:
                    # Refuse to half-update: writing role=5 without role_ref_id
                    # would recreate the same drift this code path is meant to
                    # prevent. Every workspace is bootstrapped with system roles,
                    # so this signals a real invariant violation.
                    logger.error(
                        "Project guest Role missing for workspace %s during guest demotion of member %s; "
                        "aborting role update to avoid inconsistent project memberships.",
                        workspace_member.workspace_id,
                        workspace_member.member_id,
                    )
                    return Response(
                        {"error": "Cannot update the role because the system project guest role is missing."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                ProjectMember.objects.filter(
                    workspace_id=workspace_member.workspace_id,
                    member_id=workspace_member.member_id,
                ).update(
                    role=5,
                    role_ref_id=project_guest_role.id,
                    updated_by_id=request.user.id,
                    updated_at=timezone.now(),
                )
                TeamspaceMember.objects.filter(
                    workspace_id=workspace_member.workspace_id,
                    member_id=workspace_member.member_id,
                ).delete()

            # Set role and role_ref
            workspace_member.role = target_role
            workspace_member.role_ref = target_ws_role

        # Identify the actor for the audit trail and the Layer 2 management
        # authority guard in PermissionSyncMixin. Without this, role changes
        # that cross a protected tier (admin/owner) fail the guard because
        # actor_id resolves to None.
        workspace_member.updated_by_id = request.user.id

        serializer = WorkSpaceMemberSerializer(workspace_member, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()

            workspace_members_activity.delay(
                type="workspace_member.activity.updated",
                requested_data=request.data,
                current_instance=current_instance,
                actor_id=request.user.id,
                workspace_id=workspace_member.workspace_id,
                epoch=int(timezone.now().timestamp()),
                notification=True,
                workspace_member_id=workspace_member.id,
            )
            # Sync workspace members
            member_sync_task.delay(slug)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @can(WorkspaceMemberPermissions.REMOVE, resource_param="pk")
    def destroy(self, request, slug, pk):
        # Check the user role who is deleting the user
        workspace_member = WorkspaceMember.objects.select_related("role_ref").get(
            workspace__slug=slug, pk=pk, member__is_bot=False, is_active=True
        )

        if request.user.id == workspace_member.member_id:
            return Response(
                {"error": "You cannot remove yourself from the workspace. Please use leave workspace"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Tier protection — can actor remove this member?
        actor_member = WorkspaceMember.objects.select_related("role_ref").get(
            workspace__slug=slug, member=request.user, is_active=True
        )
        actor_slug = get_workspace_role_slug(actor_member)
        target_slug = get_workspace_role_slug(workspace_member)

        allowed, error = can_manage_role(actor_slug, target_slug)
        if not allowed:
            return Response({"error": error}, status=status.HTTP_403_FORBIDDEN)

        if (
            Project.objects.annotate(
                total_members=Count("project_projectmember"),
                member_with_role=Count(
                    "project_projectmember",
                    filter=Q(
                        project_projectmember__member_id=workspace_member.id,
                        project_projectmember__role=20,
                    ),
                ),
            )
            .filter(total_members=1, member_with_role=1, workspace__slug=slug)
            .exists()
        ):
            return Response(
                {
                    "error": "User is a part of some projects where they are the only admin, they should either leave that project or promote another user to admin."  # noqa: E501
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Deactivate the users from the projects where the user is part of
        _ = ProjectMember.objects.filter(
            workspace__slug=slug, member_id=workspace_member.member_id, is_active=True
        ).update(is_active=False, updated_at=timezone.now())

        removed_member_name = workspace_member.member.display_name
        workspace_member.is_active = False
        workspace_member.save()

        # Remove the user from the teamspaces where the user is part of
        TeamspaceMember.objects.filter(workspace__slug=slug, member_id=workspace_member.member_id).delete()

        # Remove the user from the pages where the user is part of
        PageUser.objects.filter(workspace__slug=slug, user_id=workspace_member.member_id).delete()

        # Sync workspace members
        member_sync_task.delay(slug)

        workspace_members_activity.delay(
            type="workspace_member.activity.removed",
            requested_data={"name": removed_member_name},
            current_instance=None,
            actor_id=request.user.id,
            workspace_id=workspace_member.workspace_id,
            epoch=int(timezone.now().timestamp()),
            notification=True,
        )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @invalidate_cache(
        path="/api/workspaces/:slug/members/",
        url_params=True,
        user=False,
        multiple=True,
    )
    @invalidate_cache(path="/api/users/me/settings/")
    @invalidate_cache(path="api/users/me/workspaces/", user=False, multiple=True)
    @can(WorkspacePermissions.VIEW, resource_param="workspace_id")
    def leave(self, request, slug):
        workspace_member = WorkspaceMember.objects.select_related("role_ref").get(
            workspace__slug=slug, member=request.user, is_active=True
        )

        # Check if the leaving user is the only admin/owner of the workspace
        if (
            workspace_member.role_ref
            and workspace_member.role_ref.slug in ("admin", "owner")
            and not WorkspaceMember.objects.filter(
                workspace__slug=slug, role_ref__slug__in=["admin", "owner"], is_active=True
            ).count()
            > 1
        ):
            return Response(
                {
                    "error": "You cannot leave the workspace as you are the only admin of the workspace you will have to either delete the workspace or promote another user to admin."  # noqa: E501
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            Project.objects.annotate(
                total_members=Count("project_projectmember"),
                member_with_role=Count(
                    "project_projectmember",
                    filter=Q(
                        project_projectmember__member_id=request.user.id,
                        project_projectmember__role_ref__slug="admin",
                    ),
                ),
            )
            .filter(total_members=1, member_with_role=1, workspace__slug=slug)
            .exists()
        ):
            return Response(
                {
                    "error": "You are a part of some projects where you are the only admin, you should either leave the project or promote another user to admin."  # noqa: E501
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # # Deactivate the users from the projects where the user is part of
        _ = ProjectMember.objects.filter(
            workspace__slug=slug, member_id=workspace_member.member_id, is_active=True
        ).update(is_active=False, updated_at=timezone.now())

        # # Deactivate the user
        workspace_member._removal_reason = "left"
        workspace_member.is_active = False
        workspace_member.save()

        # Remove the user from the teamspaces where the user is part of
        TeamspaceMember.objects.filter(workspace__slug=slug, member_id=workspace_member.member_id).delete()

        # Remove the user from the pages where the user is part of
        PageUser.objects.filter(workspace__slug=slug, user_id=workspace_member.member_id).delete()

        # # Sync workspace members
        member_sync_task.delay(slug)

        workspace_members_activity.delay(
            type="workspace_member.activity.left",
            requested_data=None,
            current_instance=None,
            actor_id=request.user.id,
            workspace_id=workspace_member.workspace_id,
            epoch=int(timezone.now().timestamp()),
            notification=True,
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkspaceMemberUserViewsEndpoint(BaseAPIView):
    @can(WorkspacePermissions.VIEW, resource_param="workspace_id")
    def post(self, request, slug):
        workspace_member = WorkspaceMember.objects.get(workspace__slug=slug, member=request.user, is_active=True)
        workspace_member.view_props = request.data.get("view_props", {})
        workspace_member.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkspacePreferencesEndpoint(BaseAPIView):
    use_read_replica = True

    def _get_annotated_member(self, request, slug):
        return (
            WorkspaceMember.objects.filter(member=request.user, workspace__slug=slug, is_active=True)
            .select_related("role_ref")
            .first()
        )

    @can(WorkspacePermissions.VIEW, resource_param="workspace_id")
    def get(self, request, slug):
        workspace_member = self._get_annotated_member(request, slug)
        if workspace_member:
            serializer = WorkspacePreferencesSerializer(workspace_member)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not a member of this workspace"}, status=status.HTTP_403_FORBIDDEN)

    @can(WorkspacePermissions.VIEW, resource_param="workspace_id")
    def patch(self, request, slug):
        workspace_member = self._get_annotated_member(request, slug)
        if not workspace_member:
            return Response(
                {"error": "You are not a member of this workspace"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = WorkspacePreferencesSerializer(workspace_member, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# For WorkspaceMember fields:
# - getting_started_checklist
# - tips
# - explored_features
class WorkspaceMemberUserOnboardingEndpoint(BaseAPIView):
    @can(WorkspacePermissions.VIEW, resource_param="workspace_id")
    def patch(self, request, slug):
        try:
            workspace_member = WorkspaceMember.objects.get(workspace__slug=slug, member=request.user, is_active=True)

        except WorkspaceMember.DoesNotExist:
            return Response(
                {"error": "You are not a member of this workspace"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = WorkspaceMemberUserOnboardingSerializer(
            workspace_member,
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorkspaceProjectMemberEndpoint(BaseAPIView):
    serializer_class = ProjectMemberRoleSerializer
    model = ProjectMember

    @can(WorkspacePermissions.VIEW, resource_param="workspace_id")
    def get(self, request, slug):
        # Fetch all project IDs where the user is involved
        project_ids = (
            ProjectMember.objects.filter(member=request.user, is_active=True)
            .values_list("project_id", flat=True)
            .distinct()
        )

        # Get all the project members in which the user is involved
        project_members = ProjectMember.objects.filter(
            workspace__slug=slug, project_id__in=project_ids, is_active=True
        ).select_related("project", "member", "workspace", "role_ref")
        project_members = ProjectMemberRoleSerializer(project_members, many=True).data

        project_members_dict = dict()

        # Construct a dictionary with project_id as key and project_members as value
        for project_member in project_members:
            project_id = project_member.pop("project")
            if str(project_id) not in project_members_dict:
                project_members_dict[str(project_id)] = []
            project_members_dict[str(project_id)].append(project_member)

        return Response(project_members_dict, status=status.HTTP_200_OK)


class WorkspaceProjectMembersLiteEndpoint(BaseAPIView):
    """Lite roster (workspace scope): deduped member identities across a caller-supplied set of
    projects (``?project_ids=<uuid>,<uuid>,...``), scoped to only the projects the requester can
    view. A member appears once even if they belong to more than one requested project —
    per-project fields (role, is_active, joined date) don't apply to a cross-project identity
    roster. See docs/data-layer/resources/members.md.
    """

    @can(WorkspacePermissions.VIEW, resource_param="workspace_id")
    def get(self, request, slug):
        project_ids = parse_uuid_list(request.GET.get("project_ids", ""))
        search = request.GET.get("search")

        if not project_ids:
            return Response(
                {"error": "project_ids is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ProjectMember has no PermissionMeta yet (see the members-authorized-listing TODO on
        # ProjectMemberViewSet.lite), so queryset.authorized_for() can't resolve a scope spec for
        # it. Check VIEW per requested project via the engine directly instead.
        workspace_id = request.workspace_id
        authorized_project_ids = [
            project_id
            for project_id in project_ids
            if permission_engine.check(
                user=request.user,
                permission=ProjectMemberPermissions.VIEW,
                context=PermissionContext.project(project_id=project_id, workspace_id=workspace_id),
            )
        ]

        bot_filter = Q(member__is_bot=False) | Q(member__bot_type=BotTypeEnum.APP_BOT.value)
        member_ids = (
            ProjectMember.objects.filter(
                bot_filter,
                workspace__slug=slug,
                project_id__in=authorized_project_ids,
                is_active=True,
                member__member_workspace__workspace__slug=slug,
                member__member_workspace__is_active=True,
            )
            .values_list("member_id", flat=True)
            .distinct()
        )
        users = User.objects.filter(id__in=member_ids).order_by("display_name")
        if search:
            users = users.filter(
                Q(display_name__icontains=search) | Q(first_name__icontains=search) | Q(last_name__icontains=search)
            )

        return Response(
            paginate(
                base_queryset=users,
                queryset=users,
                cursor=request.GET.get("cursor"),
                on_result=lambda members: ProjectMembersLiteSerializer(
                    members, many=True, context={"workspace_id": workspace_id}
                ).data,
                max_limit=50,
                per_page=request.GET.get("per_page") or "10",
            ),
            status=status.HTTP_200_OK,
        )


class WorkspaceMemberUserEndpoint(BaseAPIView):
    use_read_replica = True

    def get(self, request, slug):
        workspace_member = (
            WorkspaceMember.objects.filter(member=request.user, workspace__slug=slug, is_active=True)
            .select_related("member", "role_ref")
            .first()
        )
        if not workspace_member:
            return Response({"error": "You are not a member of this workspace"}, status=status.HTTP_403_FORBIDDEN)

        data = {
            "id": str(workspace_member.id),
            "member": str(request.user.id),
            "role": workspace_member.role,
            "workspace": str(workspace_member.workspace_id),
            "company_role": getattr(workspace_member, "company_role", None),
            "created_at": workspace_member.created_at.isoformat() if workspace_member.created_at else None,
            "created_by": str(workspace_member.created_by_id) if workspace_member.created_by_id else None,
            "updated_at": workspace_member.updated_at.isoformat() if workspace_member.updated_at else None,
            "updated_by": str(workspace_member.updated_by_id) if workspace_member.updated_by_id else None,
            "default_props": getattr(workspace_member, "default_props", {}),
            "view_props": getattr(workspace_member, "view_props", {}),
            "draft_issue_count": 0,
        }
        return Response(data, status=status.HTTP_200_OK)


class UserWorkspaceProjectRolesEndpoint(BaseAPIView):
    use_read_replica = True

    def get(self, request, slug):
        project_members = ProjectMember.objects.filter(
            workspace__slug=slug, member=request.user, is_active=True
        ).values("project_id", "role")
        roles = {str(pm["project_id"]): pm["role"] for pm in project_members}
        return Response(roles, status=status.HTTP_200_OK)
