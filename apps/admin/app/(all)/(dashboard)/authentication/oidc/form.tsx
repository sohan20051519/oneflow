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
import type { IFormattedInstanceConfiguration, TInstanceOidcAuthenticationConfigurationKeys } from "@plane/types";
// components
import { CodeBlock } from "@/components/common/code-block";
import type { TControllerInputFormField } from "@/components/common/controller-input";
import { ControllerInput } from "@/components/common/controller-input";
import type { TCopyField } from "@/components/common/copy-field";
import { CopyField } from "@/components/common/copy-field";
import { InfisicalBadgeBanner } from "@/components/common/infisical-badge-banner";

type Props = {
  config: IFormattedInstanceConfiguration;
};

type OidcConfigFormValues = Record<TInstanceOidcAuthenticationConfigurationKeys, string>;

export function InstanceOidcConfigForm(_props: Props) {
  // form data
  const { control } = useForm<OidcConfigFormValues>({
    defaultValues: {
      OIDC_CLIENT_ID: "",
      OIDC_CLIENT_SECRET: "",
      OIDC_AUTHORIZE_URL: "",
      OIDC_TOKEN_URL: "",
      OIDC_USERINFO_URL: "",
      OIDC_LOGOUT_URL: "",
      OIDC_PROVIDER_NAME: "",
      ENABLE_OIDC_IDP_SYNC: "0",
    },
  });

  const originURL = !isEmpty(API_BASE_URL) ? API_BASE_URL : typeof window !== "undefined" ? window.location.origin : "";

  const OIDC_FORM_FIELDS: TControllerInputFormField[] = [
    {
      key: "OIDC_CLIENT_ID",
      type: "text",
      label: "Client ID (Value fetched from Infisical)",
      description: "A unique ID for this one flow app registered on Keycloak or your IdP.",
      placeholder: "OIDC_CLIENT_ID (Value fetched from Infisical)",
      error: false,
      required: false,
      disabled: true,
      readOnly: true,
    },
    {
      key: "OIDC_CLIENT_SECRET",
      type: "password",
      label: "Client secret (Value fetched from Infisical)",
      description: "The client secret that authenticates this one flow app to your IdP.",
      placeholder: "OIDC_CLIENT_SECRET (Value fetched from Infisical)",
      error: false,
      required: false,
      disabled: true,
      readOnly: true,
    },
    {
      key: "OIDC_AUTHORIZE_URL",
      type: "text",
      label: "Authorize URL (Value fetched from Infisical)",
      description: "The URL that initiates the OpenID Connect sign-in flow on your IdP.",
      placeholder: "OIDC_AUTHORIZE_URL (Value fetched from Infisical)",
      error: false,
      required: false,
      disabled: true,
      readOnly: true,
    },
    {
      key: "OIDC_TOKEN_URL",
      type: "text",
      label: "Token URL (Value fetched from Infisical)",
      description: "The URL that exchanges the auth code for access and ID tokens.",
      placeholder: "OIDC_TOKEN_URL (Value fetched from Infisical)",
      error: false,
      required: false,
      disabled: true,
      readOnly: true,
    },
    {
      key: "OIDC_USERINFO_URL",
      type: "text",
      label: "Userinfo URL (Value fetched from Infisical)",
      description: "The URL that fetches user profile information from your IdP.",
      placeholder: "OIDC_USERINFO_URL (Value fetched from Infisical)",
      error: false,
      required: false,
      disabled: true,
      readOnly: true,
    },
    {
      key: "OIDC_LOGOUT_URL",
      type: "text",
      label: "Logout URL (Value fetched from Infisical)",
      description: "Optional URL to redirect users to when logging out of SSO session.",
      placeholder: "OIDC_LOGOUT_URL (Value fetched from Infisical)",
      error: false,
      required: false,
      disabled: true,
      readOnly: true,
    },
    {
      key: "OIDC_PROVIDER_NAME",
      type: "text",
      label: "Provider name (Value fetched from Infisical)",
      description: "The name displayed on the sign-in button (e.g. Keycloak, OneSSO).",
      placeholder: "OIDC_PROVIDER_NAME (Value fetched from Infisical)",
      error: false,
      required: false,
      disabled: true,
      readOnly: true,
    },
  ];

  const OIDC_COMMON_SERVICE_DETAILS: TCopyField[] = [
    {
      key: "Origin_URL",
      label: "Origin URL",
      url: originURL,
      description: (
        <p>
          We will auto-generate this. Add this as a <CodeBlock darkerShade>Valid redirect URI / Web origin</CodeBlock>{" "}
          on your Keycloak client.
        </p>
      ),
    },
  ];

  const OIDC_SERVICE_DETAILS: TCopyField[] = [
    {
      key: "Callback_URI",
      label: "Sign-in Redirect URL",
      url: `${originURL}/auth/oidc/callback/`,
      description: (
        <p>
          Add this to <CodeBlock darkerShade>Valid Redirect URIs</CodeBlock> in your Keycloak / IdP client configuration.
        </p>
      ),
    },
    {
      key: "Logout_URI",
      label: "Logout Redirect URL",
      url: `${originURL}/auth/oidc/logout/`,
      description: (
        <p>
          Add this to <CodeBlock darkerShade>Post logout redirect URIs</CodeBlock> in your Keycloak / IdP client.
        </p>
      ),
    },
  ];

  return (
    <>
      <div className="flex flex-col gap-8">
        <InfisicalBadgeBanner pageName="Keycloak / OIDC Authentication" />

        <div className="grid w-full grid-cols-2 gap-x-12 gap-y-8">
          <div className="col-span-2 flex flex-col gap-y-4 pt-1 md:col-span-1">
            <div className="pt-2.5 text-18 font-medium">
              IdP-provided details for one flow (Value fetched from Infisical)
            </div>
            {OIDC_FORM_FIELDS.map((field) => (
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
            <div className="pt-2 text-18 font-medium">one flow-provided details for Keycloak / IdP</div>

            <div className="flex flex-col gap-y-4">
              {/* common service details */}
              <div className="flex flex-col gap-y-4 rounded-lg bg-layer-1 px-6 py-4">
                {OIDC_COMMON_SERVICE_DETAILS.map((field) => (
                  <CopyField key={field.key} label={field.label} url={field.url} description={field.description} />
                ))}
              </div>

              {/* web service details */}
              <div className="flex flex-col overflow-hidden rounded-lg">
                <div className="flex items-center gap-x-3 bg-layer-3 px-6 py-3 text-11 font-medium text-secondary uppercase">
                  <Monitor className="h-3 w-3" />
                  Web
                </div>
                <div className="flex flex-col gap-y-4 bg-layer-1 px-6 py-4">
                  {OIDC_SERVICE_DETAILS.map((field) => (
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
