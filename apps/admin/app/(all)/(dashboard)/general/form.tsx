/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { observer } from "mobx-react";
import Link from "next/link";
import { Controller, useForm } from "react-hook-form";
import { Telescope, Lock } from "lucide-react";
// plane imports
import { Button, getButtonStyling } from "@plane/propel/button";
import type { IInstance, IInstanceAdmin } from "@plane/types";
import { Input, ToggleSwitch } from "@plane/ui";
// components
import { ControllerInput } from "@/components/common/controller-input";
import { InfisicalBadgeBanner } from "@/components/common/infisical-badge-banner";

export interface IGeneralConfigurationForm {
  instance: IInstance;
  instanceAdmins: IInstanceAdmin[];
}

export const GeneralConfigurationForm = observer(function GeneralConfigurationForm(_props: IGeneralConfigurationForm) {
  // form data
  const { control } = useForm<Partial<IInstance>>({
    defaultValues: {
      instance_name: "",
      is_telemetry_enabled: false,
    },
  });

  return (
    <div className="space-y-8">
      <InfisicalBadgeBanner pageName="General Settings" />

      <div className="space-y-4">
        <div className="text-16 font-medium text-primary">Instance details (Value fetched from Infisical)</div>
        <div className="grid-col grid w-full grid-cols-1 items-center justify-between gap-8 md:grid-cols-2 lg:grid-cols-3">
          <ControllerInput
            key="instance_name"
            name="instance_name"
            control={control}
            type="text"
            label="Name of instance (Value fetched from Infisical)"
            placeholder="INSTANCE_NAME (Value fetched from Infisical)"
            error={false}
            required={false}
            disabled={true}
            readOnly={true}
          />

          <div className="flex flex-col gap-1">
            <h4 className="text-13 text-tertiary">Email (Value fetched from Infisical)</h4>
            <Input
              id="email"
              name="email"
              type="email"
              value=""
              placeholder="ADMIN_EMAIL (Value fetched from Infisical)"
              className="w-full cursor-not-allowed !text-placeholder bg-layer-subtle"
              autoComplete="on"
              disabled
              readOnly
            />
          </div>

          <div className="flex flex-col gap-1">
            <h4 className="text-13 text-tertiary">Instance ID (Value fetched from Infisical)</h4>
            <Input
              id="instance_id"
              name="instance_id"
              type="text"
              value=""
              placeholder="INSTANCE_ID (Value fetched from Infisical)"
              className="w-full cursor-not-allowed rounded-md font-medium !text-placeholder bg-layer-subtle"
              disabled
              readOnly
            />
          </div>
        </div>
      </div>

      <div className="space-y-6">
        <div className="border-b border-subtle pb-1.5 text-16 font-medium text-primary">
          Telemetry (Value fetched from Infisical)
        </div>
        <div className="flex items-center gap-14">
          <div className="flex grow items-center gap-4">
            <div className="shrink-0">
              <div className="flex size-11 items-center justify-center rounded-lg bg-layer-1">
                <Telescope className="size-5 text-tertiary" />
              </div>
            </div>
            <div className="grow">
              <div className="text-13 leading-5 font-medium text-primary">
                Let one flow collect anonymous usage data (Value fetched from Infisical)
              </div>
              <div className="text-11 leading-5 font-regular text-tertiary">
                Managed centrally via Infisical runtime variables.
              </div>
            </div>
          </div>
          <div className="shrink-0 opacity-70">
            <ToggleSwitch value={false} onChange={() => {}} size="sm" disabled={true} />
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-4 pt-4 border-t border-subtle">
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
});
