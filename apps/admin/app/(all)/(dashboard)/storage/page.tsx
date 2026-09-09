/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { observer } from "mobx-react";
// components
import { PageWrapper } from "@/components/common/page-wrapper";
// local imports
import { InstanceStorageForm } from "./storage-config-form";

function InstanceStoragePage() {
  return (
    <PageWrapper
      header={{
        title: "AWS S3 Storage (Value fetched from Infisical)",
        description:
          "Manage object storage bucket, access keys, and storage parameters. All values are fetched dynamically from Infisical.",
      }}
    >
      <InstanceStorageForm />
    </PageWrapper>
  );
}

export const meta = () => [{ title: "AWS S3 Storage (Value fetched from Infisical) - God Mode" }];

export default observer(InstanceStoragePage);
