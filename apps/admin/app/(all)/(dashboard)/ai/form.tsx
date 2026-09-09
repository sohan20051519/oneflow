/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useForm } from "react-hook-form";
import { Lightbulb, Lock } from "lucide-react";
import { Button } from "@plane/propel/button";
import type { IFormattedInstanceConfiguration, TInstanceAIConfigurationKeys } from "@plane/types";
// components
import type { TControllerInputFormField } from "@/components/common/controller-input";
import { ControllerInput } from "@/components/common/controller-input";
import { InfisicalBadgeBanner } from "@/components/common/infisical-badge-banner";

type IInstanceAIForm = {
  config: IFormattedInstanceConfiguration;
};

type AIFormValues = Record<TInstanceAIConfigurationKeys, string>;

export function InstanceAIForm(_props: IInstanceAIForm) {
  // form data locked to placeholders
  const {
    control,
    formState: { errors },
  } = useForm<AIFormValues>({
    defaultValues: {
      LLM_API_KEY: "",
      LLM_MODEL: "",
    },
  });

  const aiFormFields: TControllerInputFormField[] = [
    {
      key: "LLM_MODEL",
      type: "text",
      label: "LLM Model (Value fetched from Infisical)",
      description: <>Choose an OpenAI engine configured in Infisical.</>,
      placeholder: "LLM_MODEL (Value fetched from Infisical)",
      error: Boolean(errors.LLM_MODEL),
      required: false,
    },
    {
      key: "LLM_API_KEY",
      type: "text",
      label: "API key (Value fetched from Infisical)",
      description: <>LLM secret key provisioned securely from Infisical.</>,
      placeholder: "LLM_API_KEY (Value fetched from Infisical)",
      error: Boolean(errors.LLM_API_KEY),
      required: false,
    },
  ];

  return (
    <div className="space-y-8">
      <InfisicalBadgeBanner pageName="Artificial Intelligence Settings" />

      <div className="space-y-3">
        <div>
          <div className="pb-1 text-18 font-medium text-primary">OpenAI (Value fetched from Infisical)</div>
          <div className="text-13 font-regular text-tertiary">
            OpenAI model parameters and credentials are automatically injected from Infisical.
          </div>
        </div>
        <div className="grid-col grid w-full grid-cols-1 items-center justify-between gap-x-12 gap-y-8 lg:grid-cols-3">
          {aiFormFields.map((field) => (
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
              disabled
              readOnly
            />
          ))}
        </div>
      </div>

      <div className="flex flex-col items-start gap-4">
        <Button variant="secondary" size="lg" disabled className="opacity-75 cursor-not-allowed">
          <Lock className="mr-2 h-4 w-4 inline" />
          Locked (Managed via Infisical)
        </Button>

        <div className="relative inline-flex items-center gap-1.5 rounded-sm border border-accent-subtle bg-accent-subtle px-4 py-2 text-caption-sm-regular text-accent-secondary">
          <Lightbulb className="size-4" />
          <div>
            AI credentials and models are provisioned securely via Infisical Secret Manager. To change these settings, update them in Infisical.
          </div>
        </div>
      </div>
    </div>
  );
}
