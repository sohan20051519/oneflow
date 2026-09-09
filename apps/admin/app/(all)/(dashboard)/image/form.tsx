/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useForm } from "react-hook-form";
import { Lock } from "lucide-react";
import { Button } from "@plane/propel/button";
import type { IFormattedInstanceConfiguration, TInstanceImageConfigurationKeys } from "@plane/types";
// components
import { ControllerInput } from "@/components/common/controller-input";
import { InfisicalBadgeBanner } from "@/components/common/infisical-badge-banner";

type IInstanceImageConfigForm = {
  config: IFormattedInstanceConfiguration;
};

type ImageConfigFormValues = Record<TInstanceImageConfigurationKeys, string>;

export function InstanceImageConfigForm(_props: IInstanceImageConfigForm) {
  // form data locked to placeholders
  const {
    control,
    formState: { errors },
  } = useForm<ImageConfigFormValues>({
    defaultValues: {
      UNSPLASH_ACCESS_KEY: "",
    },
  });

  return (
    <div className="space-y-8">
      <InfisicalBadgeBanner pageName="Third-Party Image Libraries" />

      <div className="grid-col grid w-full grid-cols-1 items-center justify-between gap-x-16 gap-y-8 lg:grid-cols-2">
        <ControllerInput
          control={control}
          type="text"
          name="UNSPLASH_ACCESS_KEY"
          label="Access key from your Unsplash account (Value fetched from Infisical)"
          description={
            <>
              Unsplash access credentials are provisioned securely through Infisical Secret Manager.&nbsp;
              <a
                href="https://unsplash.com/documentation#creating-a-developer-account"
                target="_blank"
                className="text-accent-primary hover:underline"
                rel="noreferrer"
                aria-label="Unsplash developer account documentation"
              >
                Learn more.
              </a>
            </>
          }
          placeholder="UNSPLASH_ACCESS_KEY (Value fetched from Infisical)"
          error={Boolean(errors.UNSPLASH_ACCESS_KEY)}
          disabled
          readOnly
        />
      </div>

      <div>
        <Button variant="secondary" size="lg" disabled className="opacity-75 cursor-not-allowed">
          <Lock className="mr-2 h-4 w-4 inline" />
          Locked (Managed via Infisical)
        </Button>
      </div>
    </div>
  );
}
