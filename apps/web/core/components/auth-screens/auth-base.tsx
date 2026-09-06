/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React, { useEffect, useRef, useState } from "react";
import { observer } from "mobx-react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { AlertCircle, Eye, EyeOff, X } from "lucide-react";
import { API_BASE_URL } from "@plane/constants";
import { PlaneLockup } from "@plane/propel/icons";
import { checkEmailValidity, cn } from "@plane/utils";
import { PageHead } from "@/components/core/page-title";
import {
  EAuthenticationErrorCodes,
  EAuthModes,
  authErrorHandler,
} from "@/helpers/authentication.helper";
import { useAppRouter } from "@/hooks/use-app-router";
import { AuthService } from "@/services/auth.service";

type AuthBaseProps = {
  authType: EAuthModes;
};

const authService = new AuthService();

export const AuthBase = observer(function AuthBase({ authType }: AuthBaseProps) {
  const router = useAppRouter();
  const searchParams = useSearchParams();

  // Mode state (sign in vs sign up)
  const [mode, setMode] = useState<EAuthModes>(authType);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [csrfToken, setCsrfToken] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const formRef = useRef<HTMLFormElement>(null);
  const nextPath = searchParams.get("next_path");

  // Sync mode with prop change
  useEffect(() => {
    setMode(authType);
  }, [authType]);

  // Request CSRF token on mount
  useEffect(() => {
    authService
      .requestCSRFToken()
      .then((res) => {
        if (res?.csrf_token) {
          setCsrfToken(res.csrf_token);
        }
      })
      .catch(() => {});
  }, []);

  // Handle URL query errors and prefilled email
  useEffect(() => {
    const errorCode = searchParams.get("error_code");
    const errorMsg = searchParams.get("error_message");
    const emailParam = searchParams.get("email");

    if (emailParam && !email) {
      setEmail(emailParam);
    }

    if (errorCode) {
      const handler = authErrorHandler(errorCode as EAuthenticationErrorCodes, emailParam || email);
      if (handler) {
        if (typeof handler.message === "function") {
          const rendered = handler.message(emailParam || email);
          setErrorMessage(typeof rendered === "string" ? rendered : "Authentication failed");
        } else if (typeof handler.message === "string") {
          setErrorMessage(handler.message);
        }
      } else if (errorMsg) {
        setErrorMessage(errorMsg.replace(/_/g, " ").toLowerCase());
      }
    }
  }, [searchParams]);

  const switchMode = (newMode: EAuthModes) => {
    setMode(newMode);
    setErrorMessage(null);
    if (newMode === EAuthModes.SIGN_UP) {
      router.push("/sign-up");
    } else {
      router.push("/");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email || !checkEmailValidity(email)) {
      setErrorMessage("please enter a valid email address");
      return;
    }

    if (!password || password.length < 8) {
      setErrorMessage("password must be at least 8 characters");
      return;
    }

    if (mode === EAuthModes.SIGN_UP && password !== confirmPassword) {
      setErrorMessage("passwords do not match");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      let token = csrfToken;
      if (!token) {
        const res = await authService.requestCSRFToken();
        token = res?.csrf_token || "";
        setCsrfToken(token);
      }

      if (formRef.current) {
        const csrfInput = formRef.current.querySelector(
          'input[name="csrfmiddlewaretoken"]'
        ) as HTMLInputElement;
        if (csrfInput && token) {
          csrfInput.value = token;
          csrfInput.setAttribute("value", token);
        }
        const emailInput = formRef.current.querySelector(
          'input[name="email"]'
        ) as HTMLInputElement;
        if (emailInput) {
          const val = emailInput.value || email;
          emailInput.value = val;
          emailInput.setAttribute("value", val);
        }
        const passwordInput = formRef.current.querySelector(
          'input[name="password"]'
        ) as HTMLInputElement;
        if (passwordInput) {
          const val = passwordInput.value || password;
          passwordInput.value = val;
          passwordInput.setAttribute("value", val);
        }
        formRef.current.submit();
      }
    } catch {
      setIsSubmitting(false);
      setErrorMessage("something went wrong. please try again.");
    }
  };

  const pageTitle = mode === EAuthModes.SIGN_IN ? "sign in" : "create account";

  return (
    <>
      <PageHead title={`${pageTitle} - oneflow`} />
      <div className="relative flex min-h-screen w-full flex-col items-center justify-center bg-background px-4 py-8 select-none sm:px-6">
        {/* Brand Header */}
        <div className="mb-6 flex items-center justify-center">
          <PlaneLockup height={32} width={140} className="text-foreground" />
        </div>

        {/* Minimal Auth Card */}
        <div className="flex w-full max-w-[400px] flex-col gap-6 rounded-xl border border-subtle bg-surface-1 p-6 shadow-sm sm:p-8">
          {/* Segmented Tab Switcher */}
          <div className="flex h-9 w-full items-center rounded-lg bg-surface-2 p-1">
            <button
              type="button"
              onClick={() => switchMode(EAuthModes.SIGN_IN)}
              className={cn(
                "h-7 flex-1 rounded-md text-xs font-medium transition-all duration-200 lowercase",
                mode === EAuthModes.SIGN_IN
                  ? "bg-surface-1 text-primary shadow-xs"
                  : "text-secondary hover:text-primary"
              )}
            >
              sign in
            </button>
            <button
              type="button"
              onClick={() => switchMode(EAuthModes.SIGN_UP)}
              className={cn(
                "h-7 flex-1 rounded-md text-xs font-medium transition-all duration-200 lowercase",
                mode === EAuthModes.SIGN_UP
                  ? "bg-surface-1 text-primary shadow-xs"
                  : "text-secondary hover:text-primary"
              )}
            >
              sign up
            </button>
          </div>

          {/* Heading */}
          <div className="flex flex-col gap-1 text-center">
            <h1 className="text-lg font-semibold tracking-tight text-primary lowercase">
              {mode === EAuthModes.SIGN_IN ? "welcome back" : "create your account"}
            </h1>
            <p className="text-xs text-secondary lowercase">
              {mode === EAuthModes.SIGN_IN
                ? "enter your credentials to access your workspace"
                : "get started in just a few seconds"}
            </p>
          </div>

          {/* Alert Message */}
          {errorMessage && (
            <div className="flex items-start justify-between gap-2 rounded-md border border-danger-strong/30 bg-danger-subtle p-2.5 text-xs text-danger-primary">
              <div className="flex items-center gap-2">
                <AlertCircle className="size-4 shrink-0" />
                <span className="capitalize">{errorMessage}</span>
              </div>
              <button
                type="button"
                onClick={() => setErrorMessage(null)}
                className="shrink-0 opacity-70 hover:opacity-100"
              >
                <X className="size-3.5" />
              </button>
            </div>
          )}

          {/* Authentication Form */}
          <form
            ref={formRef}
            method="POST"
            action={`${API_BASE_URL}/auth/${mode === EAuthModes.SIGN_IN ? "sign-in" : "sign-up"}/`}
            onSubmit={handleSubmit}
            className="flex flex-col gap-4"
          >
            <input type="hidden" name="csrfmiddlewaretoken" value={csrfToken} />
            {nextPath && <input type="hidden" name="next_path" value={nextPath} />}

            {/* Email input */}
            <div className="flex flex-col gap-1.5">
              <label htmlFor="auth-email" className="text-xs font-medium text-secondary lowercase">
                email
              </label>
              <input
                id="auth-email"
                name="email"
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setErrorMessage(null);
                }}
                placeholder="name@example.com"
                required
                autoComplete="email"
                className="h-9 w-full rounded-md border border-subtle bg-transparent px-3 text-sm text-primary placeholder:text-placeholder transition-colors focus:border-accent-primary focus:outline-none focus:ring-1 focus:ring-accent-primary"
              />
            </div>

            {/* Password input */}
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between">
                <label htmlFor="auth-password" className="text-xs font-medium text-secondary lowercase">
                  password
                </label>
                {mode === EAuthModes.SIGN_IN && (
                  <Link
                    href={`/accounts/forgot-password?email=${encodeURIComponent(email)}`}
                    className="text-xs text-secondary hover:text-accent-primary hover:underline"
                  >
                    forgot password?
                  </Link>
                )}
              </div>
              <div className="relative flex items-center">
                <input
                  id="auth-password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    setErrorMessage(null);
                  }}
                  placeholder="••••••••"
                  required
                  autoComplete={mode === EAuthModes.SIGN_IN ? "current-password" : "new-password"}
                  className="h-9 w-full rounded-md border border-subtle bg-transparent px-3 pr-9 text-sm text-primary placeholder:text-placeholder transition-colors focus:border-accent-primary focus:outline-none focus:ring-1 focus:ring-accent-primary"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-2.5 text-secondary hover:text-primary transition-colors"
                >
                  {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </div>
            </div>

            {/* Confirm Password input (Sign Up only) */}
            {mode === EAuthModes.SIGN_UP && (
              <div className="flex flex-col gap-1.5">
                <label htmlFor="auth-confirm-password" className="text-xs font-medium text-secondary lowercase">
                  confirm password
                </label>
                <div className="relative flex items-center">
                  <input
                    id="auth-confirm-password"
                    name="confirm_password"
                    type={showConfirmPassword ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => {
                      setConfirmPassword(e.target.value);
                      setErrorMessage(null);
                    }}
                    placeholder="••••••••"
                    required
                    autoComplete="new-password"
                    className="h-9 w-full rounded-md border border-subtle bg-transparent px-3 pr-9 text-sm text-primary placeholder:text-placeholder transition-colors focus:border-accent-primary focus:outline-none focus:ring-1 focus:ring-accent-primary"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-2.5 text-secondary hover:text-primary transition-colors"
                  >
                    {showConfirmPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                  </button>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="mt-2 flex h-9 w-full items-center justify-center gap-2 rounded-lg bg-accent-primary text-sm font-medium text-on-color shadow-xs transition-all hover:opacity-90 active:opacity-100 disabled:cursor-not-allowed disabled:opacity-50 lowercase"
            >
              {isSubmitting ? (
                <svg className="size-4 animate-spin text-white" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              ) : mode === EAuthModes.SIGN_IN ? (
                "sign in"
              ) : (
                "create account"
              )}
            </button>
          </form>

          {/* Bottom Switch Link */}
          <div className="text-center text-xs text-secondary lowercase">
            {mode === EAuthModes.SIGN_IN ? (
              <span>
                don&apos;t have an account?{" "}
                <button
                  type="button"
                  onClick={() => switchMode(EAuthModes.SIGN_UP)}
                  className="font-medium text-accent-primary hover:underline"
                >
                  sign up
                </button>
              </span>
            ) : (
              <span>
                already have an account?{" "}
                <button
                  type="button"
                  onClick={() => switchMode(EAuthModes.SIGN_IN)}
                  className="font-medium text-accent-primary hover:underline"
                >
                  sign in
                </button>
              </span>
            )}
          </div>
        </div>
      </div>
    </>
  );
});
