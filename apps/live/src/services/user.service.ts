/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

// types
import { logger } from "@plane/logger";
import type { IUser } from "@plane/types";
// services
import { AppError } from "@/lib/errors";
import { APIService } from "@/services/api.service";

export class UserService extends APIService {
  constructor() {
    super();
  }

  currentUserConfig() {
    return {
      url: `${this.baseURL}/api/users/me/`,
    };
  }

  async currentUser(cookie: string): Promise<IUser> {
    logger.info(`[UserService] Fetching current user from: ${this.baseURL}/api/users/me/`);
    return this.get("/api/users/me/", {
      headers: {
        Cookie: cookie,
      },
    })
      .then((response) => response?.data)
      .catch((error) => {
        const appError = new AppError(error, {
          context: { operation: "currentUser", baseURL: this.baseURL },
        });
        logger.error(`[UserService] Failed to fetch current user from ${this.baseURL}/api/users/me/`, appError);
        throw appError;
      });
  }
}
