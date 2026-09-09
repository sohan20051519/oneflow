/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { observer } from "mobx-react";
import useSWR from "swr";
import { Loader } from "@plane/ui";
// components
import { PageWrapper } from "@/components/common/page-wrapper";
// hooks
import { useInstance } from "@/hooks/store";
// local
import { InstanceConfigurationForm } from "./form";

function InstanceConfigurationPage() {
  // store
  const { fetchInstanceConfigurations, formattedConfig } = useInstance();

  const { isLoading } = useSWR("INSTANCE_CONFIGURATIONS", () => fetchInstanceConfigurations());

  return (
    <PageWrapper
      header={{
        title: "Instance Configurations & Secret Management",
        description:
          "Manage Self-Hosted Infisical secret manager integration, environment synchronization, and core OneFlow platform runtime parameters.",
      }}
    >
      {formattedConfig && !isLoading ? (
        <InstanceConfigurationForm config={formattedConfig} />
      ) : (
        <Loader className="space-y-8">
          <Loader.Item height="60px" width="50%" />
          <div className="grid w-full grid-cols-1 gap-6 md:grid-cols-2">
            <Loader.Item height="140px" />
            <Loader.Item height="140px" />
          </div>
          <Loader.Item height="200px" width="100%" />
        </Loader>
      )}
    </PageWrapper>
  );
}

export const meta = () => [{ title: "Instance Configurations & Secrets - God Mode" }];

export default observer(InstanceConfigurationPage);
