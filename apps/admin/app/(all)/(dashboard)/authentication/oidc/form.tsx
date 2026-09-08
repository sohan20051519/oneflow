/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React, { useState } from "react";
import { isEmpty } from "lodash-es";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { Monitor } from "lucide-react";
// plane internal packages
import { API_BASE_URL } from "@plane/constants";
import { Button, getButtonStyling } from "@plane/propel/button";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import type { IFormattedInstanceConfiguration, TInstanceOidcAuthenticationConfigurationKeys } from "@plane/types";
// components
import { CodeBlock } from "@/components/common/code-block";
import { ConfirmDiscardModal } from "@/components/common/confirm-discard-modal";
import type { TControllerInputFormField } from "@/components/common/controller-input";
import type { TControllerSwitchFormField } from "@/components/common/controller-switch";
import { ControllerSwitch } from "@/components/common/controller-switch";
import { ControllerInput } from "@/components/common/controller-input";
import type { TCopyField } from "@/components/common/copy-field";
import { CopyField } from "@/components/common/copy-field";
// hooks
import { useInstance } from "@/hooks/store";

type Props = {
  config: IFormattedInstanceConfiguration;
};

type OidcConfigFormValues = Record<TInstanceOidcAuthenticationConfigurationKeys, string>;

const OIDC_FORM_SWITCH_FIELD: TControllerSwitchFormField<OidcConfigFormValues> = {
  name: "ENABLE_OIDC_IDP_SYNC",
  label: "Refresh user attributes from IdP during sign in",
};

export function InstanceOidcConfigForm(props: Props) {
  const { config } = props;
  // states
  const [isDiscardChangesModalOpen, setIsDiscardChangesModalOpen] = useState(false);
  // store hooks
  const { updateInstanceConfigurations } = useInstance();
  // form data
  const {
    handleSubmit,
    control,
    reset,
    formState: { errors, isDirty, isSubmitting },
  } = useForm<OidcConfigFormValues>({
    defaultValues: {
      OIDC_CLIENT_ID: config["OIDC_CLIENT_ID"] || config["KEYCLOAK_CLIENT_ID"] || "",
      OIDC_CLIENT_SECRET: config["OIDC_CLIENT_SECRET"] || config["KEYCLOAK_CLIENT_SECRET"] || "",
      OIDC_AUTHORIZE_URL: config["OIDC_AUTHORIZE_URL"] || "",
      OIDC_TOKEN_URL: config["OIDC_TOKEN_URL"] || "",
      OIDC_USERINFO_URL: config["OIDC_USERINFO_URL"] || "",
      OIDC_LOGOUT_URL: config["OIDC_LOGOUT_URL"] || "",
      OIDC_PROVIDER_NAME: config["OIDC_PROVIDER_NAME"] || "Keycloak",
      ENABLE_OIDC_IDP_SYNC: config["ENABLE_OIDC_IDP_SYNC"] || "0",
    },
  });

  const originURL = !isEmpty(API_BASE_URL) ? API_BASE_URL : typeof window !== "undefined" ? window.location.origin : "";

  const OIDC_FORM_FIELDS: TControllerInputFormField[] = [
    {
      key: "OIDC_CLIENT_ID",
      type: "text",
      label: "Client ID",
      description: "A unique ID for this one flow app that you register on Keycloak or your IdP.",
      placeholder: "OneFlow",
      error: Boolean(errors.OIDC_CLIENT_ID),
      required: true,
    },
    {
      key: "OIDC_CLIENT_SECRET",
      type: "password",
      label: "Client secret",
      description: "The client secret that authenticates this one flow app to your IdP.",
      placeholder: "Client secret key",
      error: Boolean(errors.OIDC_CLIENT_SECRET),
      required: true,
    },
    {
      key: "OIDC_AUTHORIZE_URL",
      type: "text",
      label: "Authorize URL",
      description: "The URL that initiates the OpenID Connect sign-in flow on your IdP.",
      placeholder: "https://sso.example.com/realms/realm-name/protocol/openid-connect/auth",
      error: Boolean(errors.OIDC_AUTHORIZE_URL),
      required: true,
    },
    {
      key: "OIDC_TOKEN_URL",
      type: "text",
      label: "Token URL",
      description: "The URL that exchanges the auth code for access and ID tokens.",
      placeholder: "https://sso.example.com/realms/realm-name/protocol/openid-connect/token",
      error: Boolean(errors.OIDC_TOKEN_URL),
      required: true,
    },
    {
      key: "OIDC_USERINFO_URL",
      type: "text",
      label: "Userinfo URL",
      description: "The URL that fetches user profile information from your IdP.",
      placeholder: "https://sso.example.com/realms/realm-name/protocol/openid-connect/userinfo",
      error: Boolean(errors.OIDC_USERINFO_URL),
      required: true,
    },
    {
      key: "OIDC_LOGOUT_URL",
      type: "text",
      label: "Logout URL",
      description: "Optional URL to redirect users to when logging out of SSO session.",
      placeholder: "https://sso.example.com/realms/realm-name/protocol/openid-connect/logout",
      error: Boolean(errors.OIDC_LOGOUT_URL),
      required: false,
    },
    {
      key: "OIDC_PROVIDER_NAME",
      type: "text",
      label: "Provider name",
      description: "The name displayed on the sign-in button (e.g. Keycloak, OneSSO).",
      placeholder: "Keycloak",
      error: Boolean(errors.OIDC_PROVIDER_NAME),
      required: false,
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

  const onSubmit = async (formData: OidcConfigFormValues) => {
    const payload: Partial<OidcConfigFormValues> = { ...formData };

    try {
      const response = await updateInstanceConfigurations(payload);
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Done!",
        message: "Your Keycloak / OIDC authentication is configured. You should test it now.",
      });
      reset({
        OIDC_CLIENT_ID: response.find((item) => item.key === "OIDC_CLIENT_ID")?.value,
        OIDC_CLIENT_SECRET: response.find((item) => item.key === "OIDC_CLIENT_SECRET")?.value,
        OIDC_AUTHORIZE_URL: response.find((item) => item.key === "OIDC_AUTHORIZE_URL")?.value,
        OIDC_TOKEN_URL: response.find((item) => item.key === "OIDC_TOKEN_URL")?.value,
        OIDC_USERINFO_URL: response.find((item) => item.key === "OIDC_USERINFO_URL")?.value,
        OIDC_LOGOUT_URL: response.find((item) => item.key === "OIDC_LOGOUT_URL")?.value,
        OIDC_PROVIDER_NAME: response.find((item) => item.key === "OIDC_PROVIDER_NAME")?.value,
        ENABLE_OIDC_IDP_SYNC: response.find((item) => item.key === "ENABLE_OIDC_IDP_SYNC")?.value,
      });
    } catch (err) {
      console.error(err);
    }
  };

  const handleGoBack = (e: React.MouseEvent<HTMLAnchorElement, MouseEvent>) => {
    if (isDirty) {
      e.preventDefault();
      setIsDiscardChangesModalOpen(true);
    }
  };

  return (
    <>
      <ConfirmDiscardModal
        isOpen={isDiscardChangesModalOpen}
        onDiscardHref="/authentication"
        handleClose={() => setIsDiscardChangesModalOpen(false)}
      />
      <div className="flex flex-col gap-8">
        <div className="grid w-full grid-cols-2 gap-x-12 gap-y-8">
          <div className="col-span-2 flex flex-col gap-y-4 pt-1 md:col-span-1">
            <div className="pt-2.5 text-18 font-medium">IdP-provided details for one flow</div>
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
              />
            ))}
            <ControllerSwitch control={control} field={OIDC_FORM_SWITCH_FIELD} />
            <div className="flex flex-col gap-1 pt-4">
              <div className="flex items-center gap-4">
                <Button
                  variant="primary"
                  size="lg"
                  onClick={(e) => void handleSubmit(onSubmit)(e)}
                  loading={isSubmitting}
                  disabled={!isDirty}
                >
                  {isSubmitting ? "Saving" : "Save changes"}
                </Button>
                <Link href="/authentication" className={getButtonStyling("secondary", "lg")} onClick={handleGoBack}>
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
