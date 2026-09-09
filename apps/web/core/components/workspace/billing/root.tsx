/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { observer } from "mobx-react";
import { CheckCircle2, ShieldCheck, Zap, Users, FolderGit2, Layers, FileText, BarChart3, Database } from "lucide-react";
// components
import { SettingsHeading } from "@/components/settings/heading";

const UNLOCKED_FEATURES = [
  {
    icon: Users,
    title: "Unlimited Team Members & Seats",
    description: "Invite unlimited administrators, members, and collaborators without restrictions.",
  },
  {
    icon: FolderGit2,
    title: "Unlimited Projects & Workspaces",
    description: "Create and manage unlimited projects with custom views and workflows.",
  },
  {
    icon: Zap,
    title: "Active Cycles & Advanced Sprints",
    description: "Cross-project active cycles, burndown charts, and progress tracking.",
  },
  {
    icon: Layers,
    title: "Bulk Operations & Triage",
    description: "Batch issue updates, archiving, deletion, and intake triage workflows.",
  },
  {
    icon: FileText,
    title: "Pages & Realtime Collaboration",
    description: "Live collaborative documents, nested pages, and document sharing.",
  },
  {
    icon: BarChart3,
    title: "Analytics & Custom Insights",
    description: "Project analytics, cycle metrics, custom insights, and export capabilities.",
  },
  {
    icon: Database,
    title: "AWS S3 Cloud Storage",
    description: "Secure cloud storage for assets, attachments, and profile images.",
  },
  {
    icon: ShieldCheck,
    title: "Full Enterprise Security & SSO",
    description: "Google, GitHub, GitLab, Gitea, OIDC, and custom authentications included.",
  },
];

export const BillingRoot = observer(function BillingRoot() {
  return (
    <section className="relative scrollbar-hide size-full overflow-y-auto">
      <div>
        <SettingsHeading
          title="Billing & Plans"
          description="View your active OneFlow subscription plan and unlocked capabilities."
        />

        {/* Current Active Plan Card */}
        <div className="mt-6 rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-6 backdrop-blur-sm">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-500">
                <ShieldCheck className="h-6 w-6" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-18 font-semibold text-primary">OneFlow Enterprise</h3>
                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-11 font-medium text-emerald-600 dark:text-emerald-400">
                    <CheckCircle2 className="h-3 w-3" />
                    Lifetime Free & Active
                  </span>
                </div>
                <p className="mt-0.5 text-13 text-secondary">
                  All enterprise features, modules, integrations, and tools are unlocked without purchasing or licensing.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-20 font-bold text-primary">$0</span>
              <span className="text-12 text-tertiary">/ forever</span>
            </div>
          </div>
        </div>

        {/* Unlocked Features Grid */}
        <div className="mt-8">
          <h4 className="text-14 font-semibold text-primary mb-4">Included Enterprise Features</h4>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {UNLOCKED_FEATURES.map((feature) => (
              <div
                key={feature.title}
                className="flex items-start gap-3 rounded-lg border border-subtle bg-surface-1 p-3.5 transition-colors"
              >
                <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-layer-1 text-primary">
                  <feature.icon className="h-4 w-4" />
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-13 font-medium text-primary">{feature.title}</span>
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                  </div>
                  <p className="mt-0.5 text-12 text-tertiary leading-normal">{feature.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
});
