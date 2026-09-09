/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { Cloud, Lock, Database } from "lucide-react";
import { Button, getButtonStyling } from "@plane/propel/button";
import { ControllerInput } from "@/components/common/controller-input";
import { InfisicalBadgeBanner } from "@/components/common/infisical-badge-banner";

type StorageFormValues = {
  AWS_REGION: string;
  AWS_STORAGE_BUCKET_NAME: string;
  AWS_ACCESS_KEY_ID: string;
  AWS_SECRET_ACCESS_KEY: string;
  AWS_S3_ENDPOINT_URL: string;
  USE_MINIO: string;
};

export function InstanceStorageForm() {
  const { control } = useForm<StorageFormValues>({
    defaultValues: {
      AWS_REGION: "",
      AWS_STORAGE_BUCKET_NAME: "",
      AWS_ACCESS_KEY_ID: "",
      AWS_SECRET_ACCESS_KEY: "",
      AWS_S3_ENDPOINT_URL: "",
      USE_MINIO: "",
    },
  });

  return (
    <div className="space-y-8">
      <InfisicalBadgeBanner pageName="Amazon S3 Object Storage" />

      <div className="space-y-4">
        <div>
          <div className="flex items-center gap-2 pb-1 text-18 font-medium text-primary">
            <Database className="size-5 text-accent-primary" />
            <span>AWS S3 Storage Configuration</span>
            <span className="text-13 text-tertiary font-normal">(Value fetched from Infisical)</span>
          </div>
          <div className="text-13 font-regular text-tertiary">
            Amazon Web Services (AWS) S3 bucket credentials and endpoint controls. Values are fetched directly from Infisical into runtime.
          </div>
        </div>

        <div className="grid grid-cols-1 gap-x-12 gap-y-8 lg:grid-cols-2">
          <ControllerInput
            key="AWS_REGION"
            control={control}
            type="text"
            name="AWS_REGION"
            label="AWS Region (Value fetched from Infisical)"
            placeholder="AWS_REGION (Value fetched from Infisical)"
            description="The AWS geographical region where your S3 bucket resides."
            error={false}
            required={false}
            disabled={true}
            readOnly={true}
          />

          <ControllerInput
            key="AWS_STORAGE_BUCKET_NAME"
            control={control}
            type="text"
            name="AWS_STORAGE_BUCKET_NAME"
            label="S3 Bucket Name (Value fetched from Infisical)"
            placeholder="AWS_STORAGE_BUCKET_NAME (Value fetched from Infisical)"
            description="The name of your dedicated Amazon S3 bucket."
            error={false}
            required={false}
            disabled={true}
            readOnly={true}
          />

          <ControllerInput
            key="AWS_ACCESS_KEY_ID"
            control={control}
            type="text"
            name="AWS_ACCESS_KEY_ID"
            label="AWS Access Key ID (Value fetched from Infisical)"
            placeholder="AWS_ACCESS_KEY_ID (Value fetched from Infisical)"
            description="IAM access key identifier with S3 read/write permissions."
            error={false}
            required={false}
            disabled={true}
            readOnly={true}
          />

          <ControllerInput
            key="AWS_SECRET_ACCESS_KEY"
            control={control}
            type="password"
            name="AWS_SECRET_ACCESS_KEY"
            label="AWS Secret Access Key (Value fetched from Infisical)"
            placeholder="AWS_SECRET_ACCESS_KEY (Value fetched from Infisical)"
            description="IAM secret access key for S3 authorization."
            error={false}
            required={false}
            disabled={true}
            readOnly={true}
          />

          <ControllerInput
            key="AWS_S3_ENDPOINT_URL"
            control={control}
            type="text"
            name="AWS_S3_ENDPOINT_URL"
            label="Custom S3 Endpoint URL (Optional) (Value fetched from Infisical)"
            placeholder="AWS_S3_ENDPOINT_URL (Value fetched from Infisical)"
            description="Custom S3 endpoint or CDN URL if using MinIO, Wasabi, or Cloudflare R2."
            error={false}
            required={false}
            disabled={true}
            readOnly={true}
          />

          <ControllerInput
            key="USE_MINIO"
            control={control}
            type="text"
            name="USE_MINIO"
            label="MinIO / S3 Compatible Mode (Value fetched from Infisical)"
            placeholder="USE_MINIO (Value fetched from Infisical)"
            description="Set to 1 if using self-hosted MinIO instead of AWS S3."
            error={false}
            required={false}
            disabled={true}
            readOnly={true}
          />
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
}
