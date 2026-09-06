/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import * as React from "react";
import { Input as BaseInput } from "@base-ui-components/react/input";
// helpers
import { cn } from "../utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  mode?: "primary" | "transparent" | "true-transparent";
  inputSize?: "xs" | "sm" | "md";
  hasError?: boolean;
}

const Input = React.forwardRef(function Input(props: InputProps, ref: React.ForwardedRef<HTMLInputElement>) {
  const {
    id,
    type,
    name,
    mode = "primary",
    inputSize = "sm",
    hasError = false,
    className = "",
    autoComplete = "off",
    ...rest
  } = props;

  return (
    <BaseInput
      id={id}
      ref={ref}
      type={type}
      name={name}
      className={cn(
        "placeholder-tertiary block w-full rounded-md border border-subtle bg-transparent text-sm shadow-xs transition-all duration-200 focus:outline-none focus:ring-1 focus:ring-accent-primary focus:border-accent-primary disabled:opacity-50 disabled:cursor-not-allowed",
        {
          "h-7 px-2 text-xs": inputSize === "xs",
          "h-9 px-3 py-1.5": inputSize === "sm",
          "h-10 px-3.5 py-2": inputSize === "md",
          "rounded-md border border-subtle bg-layer-2": mode === "primary",
          "border-none bg-transparent shadow-none focus:ring-1 focus:ring-accent-primary":
            mode === "transparent",
          "border-none bg-transparent shadow-none ring-0": mode === "true-transparent",
          "border-danger-strong focus:border-danger-strong focus:ring-danger-strong": hasError,
        },
        className
      )}
      aria-invalid={hasError || undefined}
      autoComplete={autoComplete}
      {...rest}
    />
  );
});

Input.displayName = "form-input-field";

export { Input };
