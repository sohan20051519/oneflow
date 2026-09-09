/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { Lock } from "lucide-react";
// types
import { Button, getButtonStyling } from "@plane/propel/button";
import type { IFormattedInstanceConfiguration, TInstanceEmailConfigurationKeys } from "@plane/types";
// components
import type { TControllerInputFormField } from "@/components/common/controller-input";
import { ControllerInput } from "@/components/common/controller-input";
import { InfisicalBadgeBanner } from "@/components/common/infisical-badge-banner";

type IInstanceEmailForm = {
  config: IFormattedInstanceConfiguration;
};

type EmailFormValues = Record<TInstanceEmailConfigurationKeys, string>;

export function InstanceEmailForm(_props: IInstanceEmailForm) {
  // form data
  const { control } = useForm<EmailFormValues>({
    defaultValues: {
      EMAIL_HOST: "",
      EMAIL_PORT: "",
      EMAIL_HOST_USER: "",
      EMAIL_HOST_PASSWORD: "",
      EMAIL_USE_TLS: "",
      EMAIL_USE_SSL: "",
      EMAIL_FROM: "",
      ENABLE_SMTP: "",
    },
  });

  const emailFormFields: TControllerInputFormField[] = [
    {
      key: "EMAIL_HOST",
      type: "text",
      label: "Host (Value fetched from Infisical)",
      placeholder: "EMAIL_HOST (Value fetched from Infisical)",
      description: "SMTP host address managed via Infisical.",
      error: false,
      required: false,
      disabled: true,
      readOnly: true,
    },
    {
      key: "EMAIL_PORT",
      type: "text",
      label: "Port (Value fetched from Infisical)",
      placeholder: "EMAIL_PORT (Value fetched from Infisical)",
      description: "SMTP port number managed via Infisical.",
      error: false,
      required: false,
      disabled: true,
      readOnly: true,
    },
    {
      key: "EMAIL_FROM",
      type: "text",
      label: "Sender's email address (Value fetched from Infisical)",
      description: "Default sender email address managed via Infisical.",
      placeholder: "EMAIL_FROM (Value fetched from Infisical)",
      error: false,
      required: false,
      disabled: true,
      readOnly: true,
    },
  ];

  const OptionalEmailFormFields: TControllerInputFormField[] = [
    {
      key: "EMAIL_HOST_USER",
      type: "text",
      label: "Username (Value fetched from Infisical)",
      placeholder: "EMAIL_HOST_USER (Value fetched from Infisical)",
      description: "SMTP user authentication credential managed via Infisical.",
      error: false,
      required: false,
      disabled: true,
      readOnly: true,
    },
    {
      key: "EMAIL_HOST_PASSWORD",
      type: "password",
      label: "Password (Value fetched from Infisical)",
      placeholder: "EMAIL_HOST_PASSWORD (Value fetched from Infisical)",
      description: "SMTP password credential managed securely in Infisical.",
      error: false,
      required: false,
      disabled: true,
      readOnly: true,
    },
  ];

  return (
    <div className="space-y-8">
      <InfisicalBadgeBanner pageName="Email SMTP Server" />

      <div>
        <div className="grid-col grid w-full max-w-4xl grid-cols-1 items-start justify-between gap-10 lg:grid-cols-2">
          {emailFormFields.map((field) => (
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
          <div className="flex flex-col gap-1">
            <h4 className="text-13 text-tertiary">Email security (Value fetched from Infisical)</h4>
            <div className="flex h-10 w-full items-center rounded-md border border-subtle bg-layer-subtle px-3 text-13 font-medium text-placeholder cursor-not-allowed">
              EMAIL_USE_TLS / EMAIL_USE_SSL (Value fetched from Infisical)
            </div>
            <p className="pt-0.5 text-11 text-tertiary">TLS/SSL security protocols configured in Infisical.</p>
          </div>
        </div>

        <div className="my-6 flex flex-col gap-6 border-t border-subtle pt-4">
          <div className="flex w-full max-w-xl flex-col gap-y-10 px-1">
            <div className="mr-8 flex items-center gap-10 pt-4">
              <div className="grow">
                <div className="text-13 font-medium text-primary">Authentication (Value fetched from Infisical)</div>
                <div className="text-11 font-regular text-tertiary">
                  SMTP credentials are centrally managed in Infisical.
                </div>
              </div>
            </div>
          </div>
          <div className="grid-col grid w-full max-w-4xl grid-cols-1 items-center justify-between gap-10 lg:grid-cols-2">
            {OptionalEmailFormFields.map((field) => (
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
          </div>
        </div>
      </div>

      <div className="flex max-w-4xl flex-wrap items-center gap-4 py-1 border-t border-subtle pt-4">
        <Link href="/configuration/" className={getButtonStyling("primary", "lg")}>
          <Lock className="mr-2 h-4 w-4" />
          <span>Configure in Infisical</span>
        </Link>
        <Button variant="secondary" size="lg" disabled>
          Read-only (Value fetched from Infisical)
        </Button>
      </div>
    </div>
  );
}
