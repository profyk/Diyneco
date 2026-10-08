// Generated from the Diyneco OpenAPI document. Do not edit by hand.

export interface paths {
    "/api/v1/auth/email/verify": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Verify Email */
        post: operations["verify_email_api_v1_auth_email_verify_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/invitations/{token}/accept": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Accept Invitation */
        post: operations["accept_invitation_api_v1_auth_invitations__token__accept_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Login */
        post: operations["login_api_v1_auth_login_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/logout": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Logout */
        post: operations["logout_api_v1_auth_logout_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/mfa/enroll": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Mfa Enroll */
        post: operations["mfa_enroll_api_v1_auth_mfa_enroll_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/mfa/verify": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Mfa Verify
         * @description With `mfa_token`: complete a sign-in. Without it, with a bearer token: confirm a new
         *     TOTP factor from /auth/mfa/enroll (returns new tokens and the recovery codes, once).
         */
        post: operations["mfa_verify_api_v1_auth_mfa_verify_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/password/forgot": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Forgot Password */
        post: operations["forgot_password_api_v1_auth_password_forgot_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/password/reset": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reset Password */
        post: operations["reset_password_api_v1_auth_password_reset_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/pin": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Set Pin */
        put: operations["set_pin_api_v1_auth_pin_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/refresh": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Refresh */
        post: operations["refresh_api_v1_auth_refresh_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/sessions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Sessions */
        get: operations["list_sessions_api_v1_auth_sessions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/sessions/{session_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Revoke Session */
        delete: operations["revoke_session_api_v1_auth_sessions__session_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/step-up": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Step Up */
        post: operations["step_up_api_v1_auth_step_up_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Health */
        get: operations["health_api_v1_health_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/hotel": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Hotel */
        get: operations["get_hotel_api_v1_hotel_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Patch Hotel */
        patch: operations["patch_hotel_api_v1_hotel_patch"];
        trace?: never;
    };
    "/api/v1/hotel/settings": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Settings */
        get: operations["get_settings_api_v1_hotel_settings_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Patch Settings */
        patch: operations["patch_settings_api_v1_hotel_settings_patch"];
        trace?: never;
    };
    "/api/v1/permissions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Permissions */
        get: operations["list_permissions_api_v1_permissions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/roles": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Roles */
        get: operations["list_roles_api_v1_roles_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/signup": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Signup */
        post: operations["signup_api_v1_signup_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /** AcceptInvitationRequest */
        AcceptInvitationRequest: {
            /** Name */
            name: string;
            /** Password */
            password: string;
            /** Pin */
            pin: string;
        };
        /** AcceptedResponse */
        AcceptedResponse: {
            /** Status */
            status: string;
        };
        /** Address */
        Address: {
            /** City */
            city?: string | null;
            /** Country */
            country?: string | null;
            /** Line1 */
            line1?: string | null;
            /** Line2 */
            line2?: string | null;
            /** Postal Code */
            postal_code?: string | null;
            /** Province */
            province?: string | null;
        };
        /** ForgotPasswordRequest */
        ForgotPasswordRequest: {
            /** Email */
            email: string;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** HotelMembershipOut */
        HotelMembershipOut: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
            /** Roles */
            roles: string[];
            /** Status */
            status: string;
        };
        /** HotelOut */
        HotelOut: {
            /** Address */
            address: {
                [key: string]: unknown;
            };
            /** Country */
            country: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Email */
            email: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Legal Name */
            legal_name: string | null;
            /** Logo Url */
            logo_url: string | null;
            /** Name */
            name: string;
            /** Phone */
            phone: string | null;
            plan: components["schemas"]["PlanOut"] | null;
            /** Slug */
            slug: string;
            /** Status */
            status: string;
            /** Version */
            version: number;
        };
        /** HotelPatch */
        HotelPatch: {
            address?: components["schemas"]["Address"] | null;
            /** Email */
            email?: string | null;
            /** Legal Name */
            legal_name?: string | null;
            /** Name */
            name?: string | null;
            /** Phone */
            phone?: string | null;
        };
        /** InvitationAcceptedResponse */
        InvitationAcceptedResponse: {
            /**
             * Hotel Id
             * Format: uuid
             */
            hotel_id: string;
            /** Status */
            status: string;
            /**
             * User Id
             * Format: uuid
             */
            user_id: string;
        };
        /** LoginRequest */
        LoginRequest: {
            /** Email */
            email: string;
            /** Hotel Id */
            hotel_id?: string | null;
            /** Password */
            password: string;
        };
        /** MfaChallengeResponse */
        MfaChallengeResponse: {
            /**
             * Mfa Required
             * @default true
             * @constant
             */
            mfa_required: true;
            /** Mfa Token */
            mfa_token: string;
        };
        /** MfaConfirmResponse */
        MfaConfirmResponse: {
            /** Access Token */
            access_token: string;
            /** Expires In */
            expires_in: number;
            /** Hotels */
            hotels: components["schemas"]["HotelMembershipOut"][];
            /**
             * Mfa Enrolment Required
             * @default false
             */
            mfa_enrolment_required: boolean;
            /** Recovery Codes */
            recovery_codes: string[];
            /** Refresh Token */
            refresh_token?: string | null;
            /**
             * Token Type
             * @default Bearer
             * @constant
             */
            token_type: "Bearer";
            user: components["schemas"]["UserOut"];
        };
        /** MfaEnrollResponse */
        MfaEnrollResponse: {
            /** Otpauth Uri */
            otpauth_uri: string;
            /** Secret */
            secret: string;
        };
        /** MfaVerifyRequest */
        MfaVerifyRequest: {
            /** Code */
            code?: string | null;
            /** Mfa Token */
            mfa_token?: string | null;
            /** Recovery Code */
            recovery_code?: string | null;
        };
        /** Money */
        Money: {
            /** Amount Minor */
            amount_minor: number;
            /** Currency */
            currency: string;
        };
        /** PermissionList */
        PermissionList: {
            /** Data */
            data: components["schemas"]["PermissionOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** PermissionOut */
        PermissionOut: {
            /** Code */
            code: string;
            /** Description */
            description: string;
            /** Sensitive */
            sensitive: boolean;
        };
        /** PlanOut */
        PlanOut: {
            /** Code */
            code: string;
            /** Name */
            name: string;
            /** Subscription Status */
            subscription_status: string;
        };
        /** RefreshRequest */
        RefreshRequest: {
            /** Hotel Id */
            hotel_id?: string | null;
            /** Refresh Token */
            refresh_token?: string | null;
        };
        /** ResetPasswordRequest */
        ResetPasswordRequest: {
            /** New Password */
            new_password: string;
            /** Token */
            token: string;
        };
        /** RoleList */
        RoleList: {
            /** Data */
            data: components["schemas"]["RoleOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** RoleOut */
        RoleOut: {
            /** Code */
            code: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Is System */
            is_system: boolean;
            /** Name */
            name: string;
            /** Permissions */
            permissions: string[];
        };
        /** SessionList */
        SessionList: {
            /** Data */
            data: components["schemas"]["SessionOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** SessionOut */
        SessionOut: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Current */
            current: boolean;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Ip */
            ip: string | null;
            /**
             * Last Used At
             * Format: date-time
             */
            last_used_at: string;
            /** User Agent */
            user_agent: string | null;
        };
        /** SetPinRequest */
        SetPinRequest: {
            /** Pin */
            pin: string;
        };
        /** SettingsOut */
        SettingsOut: {
            abridged_invoice_max: components["schemas"]["Money"];
            /** Accommodation Rates Include Vat */
            accommodation_rates_include_vat: boolean;
            /** Checkout Override Allowed */
            checkout_override_allowed: boolean;
            /** Checkout Time */
            checkout_time: string;
            /** Currency */
            currency: string;
            /** Guest Data Retention Days */
            guest_data_retention_days: number;
            /** Invoice Prefix */
            invoice_prefix: string;
            /** Menu Prices Include Vat */
            menu_prices_include_vat: boolean;
            room_charge_auto_approve_limit: components["schemas"]["Money"];
            /** Room Charging Enabled */
            room_charging_enabled: boolean;
            room_service_fee: components["schemas"]["Money"];
            /**
             * Room Status After Checkout
             * @enum {string}
             */
            room_status_after_checkout: "cleaning" | "available";
            /** Timezone */
            timezone: string;
            /** Vat Number */
            vat_number: string | null;
            /** Vat Rate Bp */
            vat_rate_bp: number;
            /** Vat Registered */
            vat_registered: boolean;
            /** Wifi Name */
            wifi_name: string | null;
        };
        /** SettingsPatch */
        SettingsPatch: {
            abridged_invoice_max?: components["schemas"]["Money"] | null;
            /** Accommodation Rates Include Vat */
            accommodation_rates_include_vat?: boolean | null;
            /** Checkout Override Allowed */
            checkout_override_allowed?: boolean | null;
            /** Checkout Time */
            checkout_time?: string | null;
            /** Currency */
            currency?: string | null;
            /** Guest Data Retention Days */
            guest_data_retention_days?: number | null;
            /** Invoice Prefix */
            invoice_prefix?: string | null;
            /** Menu Prices Include Vat */
            menu_prices_include_vat?: boolean | null;
            room_charge_auto_approve_limit?: components["schemas"]["Money"] | null;
            /** Room Charging Enabled */
            room_charging_enabled?: boolean | null;
            room_service_fee?: components["schemas"]["Money"] | null;
            /** Room Status After Checkout */
            room_status_after_checkout?: ("cleaning" | "available") | null;
            /** Timezone */
            timezone?: string | null;
            /** Vat Number */
            vat_number?: string | null;
            /** Vat Rate Bp */
            vat_rate_bp?: number | null;
            /** Vat Registered */
            vat_registered?: boolean | null;
            /** Wifi Name */
            wifi_name?: string | null;
        };
        /** SignupHotel */
        SignupHotel: {
            address?: components["schemas"]["Address"] | null;
            /** Email */
            email?: string | null;
            /** Legal Name */
            legal_name?: string | null;
            /** Name */
            name: string;
            /** Phone */
            phone?: string | null;
        };
        /** SignupOwner */
        SignupOwner: {
            /**
             * Email
             * Format: email
             */
            email: string;
            /** Name */
            name: string;
            /** Password */
            password: string;
        };
        /** SignupRequest */
        SignupRequest: {
            hotel: components["schemas"]["SignupHotel"];
            owner: components["schemas"]["SignupOwner"];
        };
        /** SignupResponse */
        SignupResponse: {
            /** Message */
            message: string;
            /** Status */
            status: string;
        };
        /** StepUpRequest */
        StepUpRequest: {
            /** Password */
            password?: string | null;
            /** Pin */
            pin?: string | null;
        };
        /** StepUpResponse */
        StepUpResponse: {
            /**
             * Expires At
             * Format: date-time
             */
            expires_at: string;
            /** Step Up Token */
            step_up_token: string;
        };
        /** TokenResponse */
        TokenResponse: {
            /** Access Token */
            access_token: string;
            /** Expires In */
            expires_in: number;
            /** Hotels */
            hotels: components["schemas"]["HotelMembershipOut"][];
            /**
             * Mfa Enrolment Required
             * @default false
             */
            mfa_enrolment_required: boolean;
            /** Refresh Token */
            refresh_token?: string | null;
            /**
             * Token Type
             * @default Bearer
             * @constant
             */
            token_type: "Bearer";
            user: components["schemas"]["UserOut"];
        };
        /** UserOut */
        UserOut: {
            /** Email */
            email: string;
            /** Email Verified */
            email_verified: boolean;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
        };
        /** ValidationError */
        ValidationError: {
            /** Context */
            ctx?: Record<string, never>;
            /** Input */
            input?: unknown;
            /** Location */
            loc: (string | number)[];
            /** Message */
            msg: string;
            /** Error Type */
            type: string;
        };
        /** VerifyEmailRequest */
        VerifyEmailRequest: {
            /** Token */
            token: string;
        };
    };
    responses: never;
    parameters: never;
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    verify_email_api_v1_auth_email_verify_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["VerifyEmailRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    accept_invitation_api_v1_auth_invitations__token__accept_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                token: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AcceptInvitationRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InvitationAcceptedResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    login_api_v1_auth_login_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LoginRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TokenResponse"] | components["schemas"]["MfaChallengeResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    logout_api_v1_auth_logout_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
        };
    };
    mfa_enroll_api_v1_auth_mfa_enroll_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MfaEnrollResponse"];
                };
            };
        };
    };
    mfa_verify_api_v1_auth_mfa_verify_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MfaVerifyRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TokenResponse"] | components["schemas"]["MfaConfirmResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    forgot_password_api_v1_auth_password_forgot_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ForgotPasswordRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AcceptedResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    reset_password_api_v1_auth_password_reset_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ResetPasswordRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    set_pin_api_v1_auth_pin_put: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SetPinRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    refresh_api_v1_auth_refresh_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RefreshRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TokenResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_sessions_api_v1_auth_sessions_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionList"];
                };
            };
        };
    };
    revoke_session_api_v1_auth_sessions__session_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    step_up_api_v1_auth_step_up_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["StepUpRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StepUpResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    health_api_v1_health_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": unknown;
                };
            };
        };
    };
    get_hotel_api_v1_hotel_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HotelOut"];
                };
            };
        };
    };
    patch_hotel_api_v1_hotel_patch: {
        parameters: {
            query?: never;
            header?: {
                "If-Match"?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["HotelPatch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HotelOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    get_settings_api_v1_hotel_settings_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SettingsOut"];
                };
            };
        };
    };
    patch_settings_api_v1_hotel_settings_patch: {
        parameters: {
            query?: never;
            header?: {
                "If-Match"?: string | null;
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SettingsPatch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SettingsOut"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
    list_permissions_api_v1_permissions_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PermissionList"];
                };
            };
        };
    };
    list_roles_api_v1_roles_get: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RoleList"];
                };
            };
        };
    };
    signup_api_v1_signup_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SignupRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SignupResponse"];
                };
            };
            /** @description Validation Error */
            422: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HTTPValidationError"];
                };
            };
        };
    };
}
