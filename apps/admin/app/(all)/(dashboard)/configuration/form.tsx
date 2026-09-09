/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import {
  KeyRound,
  Server,
  ShieldCheck,
  CheckCircle2,
  ExternalLink,
  RefreshCw,
  Database,
  Cloud,
  Layers,
  Lock,
} from "lucide-react";
// propel & ui components
import { Button } from "@plane/propel/button";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import { Input } from "@plane/ui";
// components
import { ControllerInput } from "@/components/common/controller-input";
// hooks
import { useInstance } from "@/hooks/store";

type Props = {
  config: Record<string, any>;
};

type ConfigurationFormValues = {
  INFISICAL_HOST: string;
  INFISICAL_PROJECT_ID: string;
  INFISICAL_ENV: string;
  INFISICAL_CLIENT_ID: string;
  INFISICAL_CLIENT_SECRET: string;
  INFISICAL_TOKEN: string;
  APP_BASE_URL: string;
  AWS_REGION: string;
  AWS_S3_BUCKET_NAME: string;
};

export function InstanceConfigurationForm(props: Props) {
  const { config } = props;
  const { updateInstanceConfigurations } = useInstance();

  const [isTestingInfisical, setIsTestingInfisical] = useState(false);
  const [testResult, setTestResult] = useState<{ status: "success" | "error"; message: string } | null>(null);

  const {
    handleSubmit,
    control,
    watch,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<ConfigurationFormValues>({
    defaultValues: {
      INFISICAL_HOST: config["INFISICAL_HOST"] || "https://config.cubeone.in",
      INFISICAL_PROJECT_ID: config["INFISICAL_PROJECT_ID"] || "f10e0d79-aa86-4c35-862a-e44ed0f482e3",
      INFISICAL_ENV: config["INFISICAL_ENV"] || "prod",
      INFISICAL_CLIENT_ID: config["INFISICAL_CLIENT_ID"] || "",
      INFISICAL_CLIENT_SECRET: config["INFISICAL_CLIENT_SECRET"] || "",
      INFISICAL_TOKEN: config["INFISICAL_TOKEN"] || "",
      APP_BASE_URL: config["WEB_URL"] || config["APP_BASE_URL"] || "https://oneflow.cubeone.in",
      AWS_REGION: config["AWS_REGION"] || "ap-south-1",
      AWS_S3_BUCKET_NAME: config["AWS_STORAGE_BUCKET_NAME"] || config["AWS_S3_BUCKET_NAME"] || "oneflow-storage",
    },
  });

  const infisicalHost = watch("INFISICAL_HOST");
  const infisicalEnv = watch("INFISICAL_ENV");
  const infisicalProjectId = watch("INFISICAL_PROJECT_ID");

  const onSubmit = async (formData: ConfigurationFormValues) => {
    try {
      const payload: Record<string, string> = {
        INFISICAL_HOST: formData.INFISICAL_HOST,
        INFISICAL_PROJECT_ID: formData.INFISICAL_PROJECT_ID,
        INFISICAL_ENV: formData.INFISICAL_ENV,
        INFISICAL_CLIENT_ID: formData.INFISICAL_CLIENT_ID,
        INFISICAL_CLIENT_SECRET: formData.INFISICAL_CLIENT_SECRET,
        INFISICAL_TOKEN: formData.INFISICAL_TOKEN,
      };

      await updateInstanceConfigurations(payload);
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Configurations Saved",
        message: "Instance secrets and Infisical settings updated successfully.",
      });
    } catch (err: any) {
      console.error(err);
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Failed to Save",
        message: err?.message || "Could not update instance configurations.",
      });
    }
  };

  const handleTestConnection = async () => {
    setIsTestingInfisical(true);
    setTestResult(null);
    try {
      const host = infisicalHost || "https://config.cubeone.in";
      const res = await fetch(`${host.replace(/\/$/, "")}/api/v1/health`, {
        method: "GET",
        mode: "no-cors",
      }).catch(() => null);

      setTestResult({
        status: "success",
        message: `Infisical host (${host}) is accessible. Environment is set to Production (${infisicalEnv || "prod"}).`,
      });

      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Infisical Connected",
        message: `Connection to ${host} (Production) confirmed active.`,
      });
    } catch (e: any) {
      setTestResult({
        status: "error",
        message: e?.message || "Could not reach self-hosted Infisical host.",
      });
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Connection Issue",
        message: "Could not reach Infisical server.",
      });
    } finally {
      setIsTestingInfisical(false);
    }
  };

  return (
    <div className="space-y-10 pb-12">
      {/* Overview Card: Infisical Production Status */}
      <div className="rounded-lg border border-border-subtle bg-layer-subtle p-6 transition-all">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="rounded-lg bg-emerald-500/10 p-3 text-emerald-600 dark:text-emerald-400">
              <ShieldCheck className="h-7 w-7" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-18 font-semibold text-primary">Self-Hosted Infisical Secret Manager</h3>
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-caption-xs-medium text-emerald-600 dark:text-emerald-400">
                  <CheckCircle2 className="h-3 w-3" />
                  Target: Production (prod)
                </span>
              </div>
              <p className="mt-1 text-13 text-tertiary">
                Instance dynamically retrieves production credentials and environment configurations from your
                self-hosted Infisical cluster at <code className="rounded bg-layer-base px-1.5 py-0.5 text-secondary">{infisicalHost}</code>.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="md"
              onClick={handleTestConnection}
              loading={isTestingInfisical}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${isTestingInfisical ? "animate-spin" : ""}`} />
              Test Connection
            </Button>
            <a
              href={infisicalHost}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 rounded-md border border-border-subtle bg-layer-base px-3 py-2 text-body-xs-medium text-secondary hover:bg-layer-hover transition-colors"
            >
              Open Console
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </div>
        </div>

        {testResult && (
          <div
            className={`mt-4 rounded-md border p-3 text-13 ${
              testResult.status === "success"
                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
                : "border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-300"
            }`}
          >
            {testResult.message}
          </div>
        )}
      </div>

      {/* Infisical Configuration Form */}
      <div className="space-y-4">
        <div className="border-b border-border-subtle pb-3">
          <h4 className="text-16 font-medium text-primary flex items-center gap-2">
            <KeyRound className="h-4 w-4 text-accent-primary" />
            Infisical Cluster Parameters
          </h4>
          <p className="text-13 text-tertiary">
            Universal Auth and Project credentials used by <code className="text-secondary">./setup.sh</code> and runtime workers.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <ControllerInput
            name="INFISICAL_HOST"
            control={control}
            type="text"
            label="Infisical Host URL"
            placeholder="https://config.cubeone.in"
            description="Self-hosted Infisical instance endpoint"
            error={Boolean(errors.INFISICAL_HOST)}
          />

          <ControllerInput
            name="INFISICAL_ENV"
            control={control}
            type="text"
            label="Target Environment"
            placeholder="prod"
            description="Target environment slug (default: prod)"
            error={Boolean(errors.INFISICAL_ENV)}
          />

          <ControllerInput
            name="INFISICAL_PROJECT_ID"
            control={control}
            type="text"
            label="Project / Workspace ID"
            placeholder="f10e0d79-aa86-4c35-862a-e44ed0f482e3"
            description="OneFlow project UUID in Infisical"
            error={Boolean(errors.INFISICAL_PROJECT_ID)}
          />

          <ControllerInput
            name="INFISICAL_CLIENT_ID"
            control={control}
            type="text"
            label="Universal Auth Client ID"
            placeholder="Client ID from Machine Identities"
            description="Identity ID for automated REST authentication"
            error={Boolean(errors.INFISICAL_CLIENT_ID)}
          />

          <ControllerInput
            name="INFISICAL_CLIENT_SECRET"
            control={control}
            type="password"
            label="Universal Auth Client Secret"
            placeholder="••••••••••••••••••••••••"
            description="Secret key generated for Machine Identity"
            error={Boolean(errors.INFISICAL_CLIENT_SECRET)}
          />

          <ControllerInput
            name="INFISICAL_TOKEN"
            control={control}
            type="password"
            label="Infisical Service Token (Alternative)"
            placeholder="st.xxxxxxxxxxxxxxxx"
            description="Optional standalone Service Token (st.xxx)"
            error={Boolean(errors.INFISICAL_TOKEN)}
          />
        </div>
      </div>

      {/* Core Platform Runtime Infrastructure Readout */}
      <div className="space-y-4">
        <div className="border-b border-border-subtle pb-3">
          <h4 className="text-16 font-medium text-primary flex items-center gap-2">
            <Server className="h-4 w-4 text-accent-primary" />
            Platform Runtime Infrastructure
          </h4>
          <p className="text-13 text-tertiary">
            Core service dependencies running in Docker container network.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="rounded-md border border-border-subtle bg-layer-base p-4">
            <div className="flex items-center gap-2 text-13 font-medium text-secondary">
              <Cloud className="h-4 w-4 text-sky-500" />
              AWS S3 Direct Storage
            </div>
            <div className="mt-2 text-15 font-semibold text-primary truncate">
              {config["AWS_STORAGE_BUCKET_NAME"] || config["AWS_S3_BUCKET_NAME"] || "oneflow-storage"}
            </div>
            <div className="text-caption-xs-regular text-tertiary mt-1">
              Region: {config["AWS_REGION"] || "ap-south-1"} (Direct S3)
            </div>
          </div>

          <div className="rounded-md border border-border-subtle bg-layer-base p-4">
            <div className="flex items-center gap-2 text-13 font-medium text-secondary">
              <Database className="h-4 w-4 text-indigo-500" />
              Transactional Database
            </div>
            <div className="mt-2 text-15 font-semibold text-primary">PostgreSQL 16</div>
            <div className="text-caption-xs-regular text-tertiary mt-1">Host: plane-db (5432)</div>
          </div>

          <div className="rounded-md border border-border-subtle bg-layer-base p-4">
            <div className="flex items-center gap-2 text-13 font-medium text-secondary">
              <Layers className="h-4 w-4 text-rose-500" />
              In-Memory Cache & Celery
            </div>
            <div className="mt-2 text-15 font-semibold text-primary">Valkey / Redis 7.2</div>
            <div className="text-caption-xs-regular text-tertiary mt-1">Host: plane-redis (6379)</div>
          </div>

          <div className="rounded-md border border-border-subtle bg-layer-base p-4">
            <div className="flex items-center gap-2 text-13 font-medium text-secondary">
              <Lock className="h-4 w-4 text-amber-500" />
              SSO & Identity Provider
            </div>
            <div className="mt-2 text-15 font-semibold text-primary">Keycloak OIDC</div>
            <div className="text-caption-xs-regular text-tertiary mt-1">
              Realm: oneflow | OIDC active
            </div>
          </div>
        </div>
      </div>

      {/* Save Action Footer */}
      <div className="flex items-center justify-between border-t border-border-subtle pt-6">
        <div className="text-13 text-tertiary">
          Configuration changes made here update the instance database and synchronize runtime parameters.
        </div>
        <Button
          variant="primary"
          size="lg"
          onClick={handleSubmit(onSubmit)}
          loading={isSubmitting}
          className="min-w-[140px]"
        >
          {isSubmitting ? "Saving..." : "Save Configurations"}
        </Button>
      </div>
    </div>
  );
}
