/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React from "react";
import { isEmpty } from "lodash-es";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { Monitor, Lock } from "lucide-react";
// plane internal packages
import { API_BASE_URL } from "@plane/constants";
import { Button, getButtonStyling } from "@plane/propel/button";
import type { IFormattedInstanceConfiguration, TInstanceGithubAuthenticationConfigurationKeys } from "@plane/types";
// components
import type { TControllerInputFormField } from "@/components/common/controller-input";
import { ControllerInput } from "@/components/common/controller-input";
import type { TCopyField } from "@/components/common/copy-field";
import { CopyField } from "@/components/common/copy-field";
import { InfisicalBadgeBanner } from "@/components/common/infisical-badge-banner";

type Props = {
  config: IFormattedInstanceConfiguration;
};

type GithubConfigFormValues = Record<TInstanceGithubAuthenticationConfigurationKeys, string>;

export function InstanceGithubConfigForm(_props: Props) {
  // form data
  const { control } = useForm<GithubConfigFormValues>({
    defaultValues: {
      GITHUB_CLIENT_ID: "",
      GITHUB_CLIENT_SECRET: "",
      GITHUB_ORGANIZATION_ID: "",
      ENABLE_GITHUB_SYNC: "0",
    },
  });

  const originURL = !isEmpty(API_BASE_URL) ? API_BASE_URL : typeof window !== "undefined" ? window.location.origin : "";

  const GITHUB_FORM_FIELDS: TControllerInputFormField[] = [
    {
      key: "GITHUB_CLIENT_ID",
      type: "text",
      label: "Client ID (Value fetched from Infisical)",
      description: "GitHub OAuth application client ID configured in Infisical.",
      placeholder: "GITHUB_CLIENT_ID (Value fetched from Infisical)",
      error: false,
      required: false,
      disabled: true,
      readOnly: true,
    },
    {
      key: "GITHUB_CLIENT_SECRET",
      type: "password",
      label: "Client secret (Value fetched from Infisical)",
      description: "GitHub OAuth application client secret managed securely in Infisical.",
      placeholder: "GITHUB_CLIENT_SECRET (Value fetched from Infisical)",
      error: false,
      required: false,
      disabled: true,
      readOnly: true,
    },
    {
      key: "GITHUB_ORGANIZATION_ID",
      type: "text",
      label: "Organization ID (Optional) (Value fetched from Infisical)",
      description: "Organization GitHub ID managed via Infisical.",
      placeholder: "GITHUB_ORGANIZATION_ID (Value fetched from Infisical)",
      error: false,
      required: false,
      disabled: true,
      readOnly: true,
    },
  ];

  const GITHUB_COMMON_SERVICE_DETAILS: TCopyField[] = [
    {
      key: "Origin_URL",
      label: "Origin URL",
      url: originURL,
      description: (
        <p>
          We will auto-generate this. Add this to <span className="font-semibold">Homepage URL</span> in your GitHub OAuth
          application settings.
        </p>
      ),
    },
  ];

  const GITHUB_SERVICE_DETAILS: TCopyField[] = [
    {
      key: "Authorization_callback_URL",
      label: "Authorization callback URL",
      url: `${originURL}/auth/github/callback/`,
      description: (
        <p>
          Add this to <span className="font-semibold">Authorization callback URL</span> in your GitHub OAuth application
          settings.
        </p>
      ),
    },
  ];

  return (
    <>
      <div className="flex flex-col gap-8">
        <InfisicalBadgeBanner pageName="GitHub Authentication" />

        <div className="grid w-full grid-cols-2 gap-x-12 gap-y-8">
          <div className="col-span-2 flex flex-col gap-y-4 pt-1 md:col-span-1">
            <div className="pt-2.5 text-18 font-medium">
              GitHub-provided details for one flow (Value fetched from Infisical)
            </div>
            {GITHUB_FORM_FIELDS.map((field) => (
              <ControllerInput
                key={field.key}
                control={control}
                type={field.type}
                name={field.key}
                label={field.label}
                description={field.description}
                placeholder={field.placeholder}
                error={field.error}
                required={field.required}
                disabled={true}
                readOnly={true}
              />
            ))}
            <div className="flex flex-col gap-1 pt-4">
              <div className="flex flex-wrap items-center gap-4">
                <Link href="/configuration/" className={getButtonStyling("primary", "lg")}>
                  <Lock className="mr-2 h-4 w-4" />
                  <span>Configure in Infisical</span>
                </Link>
                <Button variant="secondary" size="lg" disabled>
                  Read-only (Value fetched from Infisical)
                </Button>
                <Link href="/authentication" className={getButtonStyling("secondary", "lg")}>
                  Go back
                </Link>
              </div>
            </div>
          </div>
          <div className="col-span-2 flex flex-col gap-y-6 md:col-span-1">
            <div className="pt-2 text-18 font-medium">one flow-provided details for GitHub</div>

            <div className="flex flex-col gap-y-4">
              <div className="flex flex-col gap-y-4 rounded-lg bg-layer-1 px-6 py-4">
                {GITHUB_COMMON_SERVICE_DETAILS.map((field) => (
                  <CopyField key={field.key} label={field.label} url={field.url} description={field.description} />
                ))}
              </div>

              <div className="flex flex-col overflow-hidden rounded-lg">
                <div className="flex items-center gap-x-3 bg-layer-3 px-6 py-3 text-11 font-medium text-secondary uppercase">
                  <Monitor className="h-3 w-3" />
                  Web
                </div>
                <div className="flex flex-col gap-y-4 bg-layer-1 px-6 py-4">
                  {GITHUB_SERVICE_DETAILS.map((field) => (
                    <CopyField key={field.key} label={field.label} url={field.url} description={field.description} />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
