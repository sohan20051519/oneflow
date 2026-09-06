/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React from "react";
import { observer } from "mobx-react";
import Link from "next/link";
import { AUTH_TRACKER_ELEMENTS } from "@plane/constants";
import { useTranslation } from "@plane/i18n";
import { PageHead } from "@/components/core/page-title";
import { EAuthModes } from "@/helpers/authentication.helper";
import { useInstance } from "@/hooks/store/use-instance";

const authContentMap = {
  [EAuthModes.SIGN_IN]: {
    pageTitle: "sign up",
    text: "auth.common.new_to_plane",
    linkText: "sign up",
    linkHref: "/sign-up",
  },
  [EAuthModes.SIGN_UP]: {
    pageTitle: "sign in",
    text: "auth.common.already_have_an_account",
    linkText: "sign in",
    linkHref: "/",
  },
};

type AuthHeaderProps = {
  type: EAuthModes;
};

export const AuthHeader = observer(function AuthHeader({ type }: AuthHeaderProps) {
  const { t } = useTranslation();
  const { config } = useInstance();
  const enableSignUpConfig = config?.enable_signup ?? false;

  return (
    <AuthHeaderBase
      pageTitle={authContentMap[type].pageTitle}
      additionalAction={
        enableSignUpConfig && (
          <div className="flex items-center gap-2 text-xs text-secondary lowercase">
            <span>{t(authContentMap[type].text)}</span>
            <Link
              data-ph-element={AUTH_TRACKER_ELEMENTS.NAVIGATE_TO_SIGN_UP}
              href={authContentMap[type].linkHref}
              className="font-medium text-accent-primary hover:underline"
            >
              {authContentMap[type].linkText}
            </Link>
          </div>
        )
      }
    />
  );
});

type TAuthHeaderBase = {
  pageTitle: string;
  additionalAction?: React.ReactNode;
};

import { PlaneLockup } from "@plane/propel/icons";

export function AuthHeaderBase(props: TAuthHeaderBase) {
  const { pageTitle, additionalAction } = props;
  return (
    <>
      <PageHead title={`${pageTitle} - oneflow`} />
      <div className="sticky top-0 flex w-full flex-shrink-0 items-center justify-between gap-6 py-4">
        <Link href="/" className="flex items-center gap-2">
          <PlaneLockup height={32} className="shrink-0" />
        </Link>
        {additionalAction}
      </div>
    </>
  );
}
