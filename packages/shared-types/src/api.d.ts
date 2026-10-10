// Generated from the Diyneco OpenAPI document. Do not edit by hand.

export interface paths {
    "/api/v1/adjustments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Adjustments */
        get: operations["list_adjustments_api_v1_adjustments_get"];
        put?: never;
        /** Request Adjustment */
        post: operations["request_adjustment_api_v1_adjustments_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/adjustments/{adjustment_id}/approve": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Approve Adjustment */
        post: operations["approve_adjustment_api_v1_adjustments__adjustment_id__approve_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/adjustments/{adjustment_id}/reject": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reject Adjustment */
        post: operations["reject_adjustment_api_v1_adjustments__adjustment_id__reject_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/activity": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Activity */
        get: operations["activity_api_v1_admin_activity_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/analytics": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Analytics */
        get: operations["analytics_api_v1_admin_analytics_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/feature-flags": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Flags */
        get: operations["flags_api_v1_admin_feature_flags_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Set Flags */
        patch: operations["set_flags_api_v1_admin_feature_flags_patch"];
        trace?: never;
    };
    "/api/v1/admin/health": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Health */
        get: operations["health_api_v1_admin_health_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/hotels": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Hotels */
        get: operations["hotels_api_v1_admin_hotels_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/hotels/{hotel_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Hotel Detail
         * @description One hotel: contacts, subscription, usage, support access and platform actions taken.
         */
        get: operations["hotel_detail_api_v1_admin_hotels__hotel_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/hotels/{hotel_id}/approve": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Approve */
        post: operations["approve_api_v1_admin_hotels__hotel_id__approve_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/hotels/{hotel_id}/reactivate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reactivate */
        post: operations["reactivate_api_v1_admin_hotels__hotel_id__reactivate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/hotels/{hotel_id}/subscription": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Put Subscription */
        put: operations["put_subscription_api_v1_admin_hotels__hotel_id__subscription_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/hotels/{hotel_id}/support-access": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Support Access */
        post: operations["support_access_api_v1_admin_hotels__hotel_id__support_access_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/hotels/{hotel_id}/suspend": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Suspend */
        post: operations["suspend_api_v1_admin_hotels__hotel_id__suspend_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/metrics": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Metrics */
        get: operations["metrics_api_v1_admin_metrics_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/plans": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Plans */
        get: operations["plans_api_v1_admin_plans_get"];
        put?: never;
        /** Create Plan */
        post: operations["create_plan_api_v1_admin_plans_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/plans/{plan_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Update Plan */
        patch: operations["update_plan_api_v1_admin_plans__plan_id__patch"];
        trace?: never;
    };
    "/api/v1/api-keys": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Keys */
        get: operations["list_keys_api_v1_api_keys_get"];
        put?: never;
        /** Create Key */
        post: operations["create_key_api_v1_api_keys_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/api-keys/{key_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Revoke Key */
        delete: operations["revoke_key_api_v1_api_keys__key_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/audit-logs": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Audit Logs */
        get: operations["audit_logs_api_v1_audit_logs_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
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
    "/api/v1/auth/kitchen/sign-in": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Kitchen Sign In */
        post: operations["kitchen_sign_in_api_v1_auth_kitchen_sign_in_post"];
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
    "/api/v1/auth/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Me */
        get: operations["me_api_v1_auth_me_get"];
        put?: never;
        post?: never;
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
    "/api/v1/billing-profiles": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Search Profiles */
        get: operations["search_profiles_api_v1_billing_profiles_get"];
        put?: never;
        /** Create Profile */
        post: operations["create_profile_api_v1_billing_profiles_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/charge-categories": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Charge Categories */
        get: operations["charge_categories_api_v1_charge_categories_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/currencies": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Currencies
         * @description Currencies a hotel or a plan may use (public: the signup form needs it).
         */
        get: operations["currencies_api_v1_currencies_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/deliveries": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Deliveries
         * @description `all` (everything ready or on its way) is the dispatcher's view and needs deliveries.manage.
         */
        get: operations["list_deliveries_api_v1_deliveries_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/deliveries/{order_id}/assign": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Assign */
        post: operations["assign_api_v1_deliveries__order_id__assign_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/deliveries/{order_id}/claim": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Claim */
        post: operations["claim_api_v1_deliveries__order_id__claim_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/deliveries/{order_id}/delivered": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Delivered */
        post: operations["delivered_api_v1_deliveries__order_id__delivered_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/deliveries/{order_id}/leave-on-room": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Leave On Room */
        post: operations["leave_on_room_api_v1_deliveries__order_id__leave_on_room_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/deliveries/{order_id}/picked-up": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Picked Up */
        post: operations["picked_up_api_v1_deliveries__order_id__picked_up_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/deliveries/{order_id}/release": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Release */
        post: operations["release_api_v1_deliveries__order_id__release_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/devices": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Devices */
        get: operations["list_devices_api_v1_devices_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/devices/heartbeat": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Heartbeat */
        post: operations["heartbeat_api_v1_devices_heartbeat_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/devices/pair": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Pair Device
         * @description Redeems a pairing code. The credential is in this response only; a replay of the same
         *     request returns `device_credential: null` (DECISIONS D23).
         */
        post: operations["pair_device_api_v1_devices_pair_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/devices/pairings": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Pairing */
        post: operations["create_pairing_api_v1_devices_pairings_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/devices/token": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Device Token
         * @description Exchanges the device credential for a 1-hour device token (security spec, Credentials).
         */
        post: operations["device_token_api_v1_devices_token_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/devices/{device_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Device */
        get: operations["get_device_api_v1_devices__device_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/devices/{device_id}/disable": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Disable Device */
        post: operations["disable_device_api_v1_devices__device_id__disable_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/devices/{device_id}/lock": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Lock Device */
        post: operations["lock_device_api_v1_devices__device_id__lock_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/devices/{device_id}/pairing": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Unpair Device */
        delete: operations["unpair_device_api_v1_devices__device_id__pairing_delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/devices/{device_id}/reassign": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reassign Device */
        post: operations["reassign_device_api_v1_devices__device_id__reassign_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/devices/{device_id}/reset": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reset Device */
        post: operations["reset_device_api_v1_devices__device_id__reset_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/devices/{device_id}/unlock": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Unlock Device
         * @description Returns a locked or disabled device to active.
         */
        post: operations["unlock_device_api_v1_devices__device_id__unlock_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/folios/{stay_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Folio */
        get: operations["get_folio_api_v1_folios__stay_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/folios/{stay_id}/charges": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Add Charge */
        post: operations["add_charge_api_v1_folios__stay_id__charges_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/folios/{stay_id}/discounts": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Add Discount */
        post: operations["add_discount_api_v1_folios__stay_id__discounts_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/guest/folio": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** My Folio */
        get: operations["my_folio_api_v1_guest_folio_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/guest/info": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Info */
        get: operations["info_api_v1_guest_info_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/guest/menu": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Menu */
        get: operations["menu_api_v1_guest_menu_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/guest/orders": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** My Orders */
        get: operations["my_orders_api_v1_guest_orders_get"];
        put?: never;
        /** Place Order */
        post: operations["place_order_api_v1_guest_orders_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/guest/orders/quote": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Quote */
        post: operations["quote_api_v1_guest_orders_quote_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/guest/orders/{order_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** My Order */
        get: operations["my_order_api_v1_guest_orders__order_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/guest/session": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Session
         * @description Works while locked, so the tablet can show its paused screen.
         */
        get: operations["session_api_v1_guest_session_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/guests": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Search Guests */
        get: operations["search_guests_api_v1_guests_get"];
        put?: never;
        /** Create Guest */
        post: operations["create_guest_api_v1_guests_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/guests/{guest_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Get Guest
         * @description Profile and stay history.
         */
        get: operations["get_guest_api_v1_guests__guest_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Patch Guest */
        patch: operations["patch_guest_api_v1_guests__guest_id__patch"];
        trace?: never;
    };
    "/api/v1/guests/{guest_id}/anonymise": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Anonymise Guest */
        post: operations["anonymise_guest_api_v1_guests__guest_id__anonymise_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/guests/{guest_id}/export": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Export Guest
         * @description POPIA access request: everything held about this guest.
         */
        get: operations["export_guest_api_v1_guests__guest_id__export_get"];
        put?: never;
        post?: never;
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
    "/api/v1/hotel/logo": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Start Logo Upload
         * @description Returns a signed URL; PUT the file there with the given headers within its lifetime.
         */
        post: operations["start_logo_upload_api_v1_hotel_logo_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/hotel/onboarding": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Onboarding */
        get: operations["get_onboarding_api_v1_hotel_onboarding_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
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
    "/api/v1/invoices/{invoice_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Invoice */
        get: operations["get_invoice_api_v1_invoices__invoice_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/invoices/{invoice_id}/credit-note": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Credit Note */
        post: operations["credit_note_api_v1_invoices__invoice_id__credit_note_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/invoices/{invoice_id}/email": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Email Invoice */
        post: operations["email_invoice_api_v1_invoices__invoice_id__email_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/invoices/{invoice_id}/pdf": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Invoice Pdf */
        get: operations["invoice_pdf_api_v1_invoices__invoice_id__pdf_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/kitchen-stations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Stations */
        get: operations["list_stations_api_v1_kitchen_stations_get"];
        put?: never;
        /** Create Station */
        post: operations["create_station_api_v1_kitchen_stations_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/kitchen-stations/{station_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Station */
        delete: operations["delete_station_api_v1_kitchen_stations__station_id__delete"];
        options?: never;
        head?: never;
        /** Patch Station */
        patch: operations["patch_station_api_v1_kitchen_stations__station_id__patch"];
        trace?: never;
    };
    "/api/v1/kitchen/order-items/{item_id}/ready": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Item Ready */
        post: operations["item_ready_api_v1_kitchen_order_items__item_id__ready_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/kitchen/order-items/{item_id}/unready": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Item Unready */
        post: operations["item_unready_api_v1_kitchen_order_items__item_id__unready_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/kitchen/orders": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Kitchen Orders */
        get: operations["kitchen_orders_api_v1_kitchen_orders_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/kitchen/orders/{order_id}/accept": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Accept */
        post: operations["accept_api_v1_kitchen_orders__order_id__accept_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/kitchen/orders/{order_id}/start": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Start */
        post: operations["start_api_v1_kitchen_orders__order_id__start_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/kitchen/staff": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Sign In List */
        get: operations["sign_in_list_api_v1_kitchen_staff_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/menu/categories": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Categories */
        get: operations["list_categories_api_v1_menu_categories_get"];
        put?: never;
        /** Create Category */
        post: operations["create_category_api_v1_menu_categories_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/menu/categories/{category_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /**
         * Delete Category
         * @description `?with_items=true` removes the category and all its items, and needs step-up.
         */
        delete: operations["delete_category_api_v1_menu_categories__category_id__delete"];
        options?: never;
        head?: never;
        /** Patch Category */
        patch: operations["patch_category_api_v1_menu_categories__category_id__patch"];
        trace?: never;
    };
    "/api/v1/menu/items": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Items */
        get: operations["list_items_api_v1_menu_items_get"];
        put?: never;
        /** Create Item */
        post: operations["create_item_api_v1_menu_items_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/menu/items/import": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Import Items
         * @description Dry run by default: a per-line report. `?commit=true` imports every row or none.
         */
        post: operations["import_items_api_v1_menu_items_import_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/menu/items/{item_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Item */
        get: operations["get_item_api_v1_menu_items__item_id__get"];
        put?: never;
        post?: never;
        /** Delete Item */
        delete: operations["delete_item_api_v1_menu_items__item_id__delete"];
        options?: never;
        head?: never;
        /** Patch Item */
        patch: operations["patch_item_api_v1_menu_items__item_id__patch"];
        trace?: never;
    };
    "/api/v1/menu/items/{item_id}/availability": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Set Availability */
        post: operations["set_availability_api_v1_menu_items__item_id__availability_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/menu/items/{item_id}/image": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Start Image Upload */
        post: operations["start_image_upload_api_v1_menu_items__item_id__image_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/menu/items/{item_id}/modifier-groups": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Set Item Groups */
        put: operations["set_item_groups_api_v1_menu_items__item_id__modifier_groups_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/menu/modifier-groups": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Groups */
        get: operations["list_groups_api_v1_menu_modifier_groups_get"];
        put?: never;
        /** Create Group */
        post: operations["create_group_api_v1_menu_modifier_groups_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/menu/modifier-groups/{group_id}/options": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Create Option */
        post: operations["create_option_api_v1_menu_modifier_groups__group_id__options_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/menu/schedules": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Schedules */
        get: operations["list_schedules_api_v1_menu_schedules_get"];
        put?: never;
        /** Create Schedule */
        post: operations["create_schedule_api_v1_menu_schedules_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/orders": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Orders */
        get: operations["list_orders_api_v1_orders_get"];
        put?: never;
        /**
         * Staff Order
         * @description A phone or fallback order for a room: same pricing and approval rules as the tablet.
         */
        post: operations["staff_order_api_v1_orders_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/orders/quote": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Staff Quote
         * @description Prices a cart for a room so the phone order can be confirmed with the exact total.
         */
        post: operations["staff_quote_api_v1_orders_quote_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/orders/{order_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Order */
        get: operations["get_order_api_v1_orders__order_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/orders/{order_id}/approve": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Approve */
        post: operations["approve_api_v1_orders__order_id__approve_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/orders/{order_id}/cancel": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Cancel */
        post: operations["cancel_api_v1_orders__order_id__cancel_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/orders/{order_id}/decline": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Decline */
        post: operations["decline_api_v1_orders__order_id__decline_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/payments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Payments */
        get: operations["list_payments_api_v1_payments_get"];
        put?: never;
        /** Record Payment */
        post: operations["record_payment_api_v1_payments_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/payments/preview": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Preview */
        post: operations["preview_api_v1_payments_preview_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
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
    "/api/v1/reports/daily-close": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Daily Close */
        get: operations["daily_close_api_v1_reports_daily_close_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/reports/daily-close/{day}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Put Daily Close */
        put: operations["put_daily_close_api_v1_reports_daily_close__day__put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/reports/items": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Items */
        get: operations["items_api_v1_reports_items_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/reports/kitchen": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Kitchen */
        get: operations["kitchen_api_v1_reports_kitchen_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/reports/occupancy": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Occupancy */
        get: operations["occupancy_api_v1_reports_occupancy_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/reports/open-balances": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Open Balances */
        get: operations["open_balances_api_v1_reports_open_balances_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/reports/orders": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Orders */
        get: operations["orders_api_v1_reports_orders_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/reports/payments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Payments */
        get: operations["payments_api_v1_reports_payments_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/reports/revenue": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Revenue */
        get: operations["revenue_api_v1_reports_revenue_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/reports/room-service": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Room Service */
        get: operations["room_service_api_v1_reports_room_service_get"];
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
        /** Create Role */
        post: operations["create_role_api_v1_roles_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/roles/{role_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Patch Role */
        patch: operations["patch_role_api_v1_roles__role_id__patch"];
        trace?: never;
    };
    "/api/v1/room-types": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Room Types */
        get: operations["list_room_types_api_v1_room_types_get"];
        put?: never;
        /** Create Room Type */
        post: operations["create_room_type_api_v1_room_types_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/room-types/{room_type_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Patch Room Type */
        patch: operations["patch_room_type_api_v1_room_types__room_type_id__patch"];
        trace?: never;
    };
    "/api/v1/rooms": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Rooms */
        get: operations["list_rooms_api_v1_rooms_get"];
        put?: never;
        /** Create Room */
        post: operations["create_room_api_v1_rooms_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/rooms/bulk": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Bulk Create Rooms */
        post: operations["bulk_create_rooms_api_v1_rooms_bulk_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/rooms/import": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Import Rooms
         * @description Dry run by default: returns a per-line report. `?commit=true` writes all rows or none.
         */
        post: operations["import_rooms_api_v1_rooms_import_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/rooms/{room_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Room */
        get: operations["get_room_api_v1_rooms__room_id__get"];
        put?: never;
        post?: never;
        /** Delete Room */
        delete: operations["delete_room_api_v1_rooms__room_id__delete"];
        options?: never;
        head?: never;
        /** Patch Room */
        patch: operations["patch_room_api_v1_rooms__room_id__patch"];
        trace?: never;
    };
    "/api/v1/rooms/{room_id}/status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Set Room Status */
        post: operations["set_room_status_api_v1_rooms__room_id__status_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/rooms/{room_id}/walk-in": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Walk In */
        post: operations["walk_in_api_v1_rooms__room_id__walk_in_post"];
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
    "/api/v1/staff": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Staff */
        get: operations["list_staff_api_v1_staff_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/staff/invitations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Invitations */
        get: operations["list_invitations_api_v1_staff_invitations_get"];
        put?: never;
        /** Invite Staff */
        post: operations["invite_staff_api_v1_staff_invitations_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/staff/invitations/{invitation_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Cancel Invitation */
        delete: operations["cancel_invitation_api_v1_staff_invitations__invitation_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/staff/{user_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Patch Staff */
        patch: operations["patch_staff_api_v1_staff__user_id__patch"];
        trace?: never;
    };
    "/api/v1/staff/{user_id}/deactivate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Deactivate Staff */
        post: operations["deactivate_staff_api_v1_staff__user_id__deactivate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/staff/{user_id}/pin/reset": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reset Staff Pin */
        post: operations["reset_staff_pin_api_v1_staff__user_id__pin_reset_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/staff/{user_id}/roles": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Set Staff Roles */
        put: operations["set_staff_roles_api_v1_staff__user_id__roles_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/stays": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Stays */
        get: operations["list_stays_api_v1_stays_get"];
        put?: never;
        /** Create Stay */
        post: operations["create_stay_api_v1_stays_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/stays/{stay_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Stay */
        get: operations["get_stay_api_v1_stays__stay_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** Change Dates */
        patch: operations["change_dates_api_v1_stays__stay_id__patch"];
        trace?: never;
    };
    "/api/v1/stays/{stay_id}/block-charges": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Block Charges */
        post: operations["block_charges_api_v1_stays__stay_id__block_charges_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/stays/{stay_id}/cancel": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Cancel Stay */
        post: operations["cancel_stay_api_v1_stays__stay_id__cancel_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/stays/{stay_id}/check-in": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Check In */
        post: operations["check_in_api_v1_stays__stay_id__check_in_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/stays/{stay_id}/checkout": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Check Out */
        post: operations["check_out_api_v1_stays__stay_id__checkout_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/stays/{stay_id}/checkout-summary": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Checkout Summary */
        get: operations["checkout_summary_api_v1_stays__stay_id__checkout_summary_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/stays/{stay_id}/invoices": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Stay Invoices */
        get: operations["stay_invoices_api_v1_stays__stay_id__invoices_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/stays/{stay_id}/move": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Move Stay */
        post: operations["move_stay_api_v1_stays__stay_id__move_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/stays/{stay_id}/unblock-charges": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Unblock Charges */
        post: operations["unblock_charges_api_v1_stays__stay_id__unblock_charges_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/subscription": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Subscription */
        get: operations["get_subscription_api_v1_subscription_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/subscription/change-request": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Change Request */
        post: operations["change_request_api_v1_subscription_change_request_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/support-access": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Hotel Grants */
        get: operations["hotel_grants_api_v1_support_access_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/support-access/{grant_id}/revoke": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Revoke Grant */
        post: operations["revoke_grant_api_v1_support_access__grant_id__revoke_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/webhooks": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Webhooks */
        get: operations["list_webhooks_api_v1_webhooks_get"];
        put?: never;
        /** Create Webhook */
        post: operations["create_webhook_api_v1_webhooks_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/webhooks/{webhook_id}/deliveries": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Webhook Deliveries */
        get: operations["webhook_deliveries_api_v1_webhooks__webhook_id__deliveries_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/webhooks/{webhook_id}/status": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Webhook Status */
        post: operations["webhook_status_api_v1_webhooks__webhook_id__status_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/webhooks/{webhook_id}/test": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Test Webhook */
        post: operations["test_webhook_api_v1_webhooks__webhook_id__test_post"];
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
        /** ActivityEvent */
        ActivityEvent: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Hotel Id */
            hotel_id: string | null;
            /** Hotel Name */
            hotel_name: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Payload */
            payload: {
                [key: string]: unknown;
            };
            /** Type */
            type: string;
        };
        /** ActivityList */
        ActivityList: {
            /** Data */
            data: components["schemas"]["ActivityEvent"][];
            /** Next Cursor */
            next_cursor?: string | null;
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
        /** AdjustmentList */
        AdjustmentList: {
            /** Data */
            data: components["schemas"]["AdjustmentListItem"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** AdjustmentListItem */
        AdjustmentListItem: {
            /** Decided At */
            decided_at: string | null;
            /** Decided By */
            decided_by: string | null;
            /** Decision Note */
            decision_note: string | null;
            /**
             * Folio Id
             * Format: uuid
             */
            folio_id: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            new_amount: components["schemas"]["SignedMoney"];
            /** Order Id */
            order_id: string | null;
            original: components["schemas"]["SignedMoney"];
            /** Reason */
            reason: string;
            /**
             * Requested At
             * Format: date-time
             */
            requested_at: string;
            /**
             * Requested By
             * Format: uuid
             */
            requested_by: string;
            /** Requested By Name */
            requested_by_name: string | null;
            /** Room */
            room: string;
            /** Status */
            status: string;
            /**
             * Stay Id
             * Format: uuid
             */
            stay_id: string;
            /** Target Entry Id */
            target_entry_id: string | null;
        };
        /** AdjustmentOut */
        AdjustmentOut: {
            /** Decided At */
            decided_at: string | null;
            /** Decided By */
            decided_by: string | null;
            /** Decision Note */
            decision_note: string | null;
            /**
             * Folio Id
             * Format: uuid
             */
            folio_id: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            new_amount: components["schemas"]["SignedMoney"];
            /** Order Id */
            order_id: string | null;
            original: components["schemas"]["SignedMoney"];
            /** Reason */
            reason: string;
            /**
             * Requested At
             * Format: date-time
             */
            requested_at: string;
            /**
             * Requested By
             * Format: uuid
             */
            requested_by: string;
            /** Status */
            status: string;
            /** Target Entry Id */
            target_entry_id: string | null;
        };
        /** AdjustmentRequest */
        AdjustmentRequest: {
            /** Folio Entry Id */
            folio_entry_id?: string | null;
            new_amount: components["schemas"]["Money"];
            /** Order Id */
            order_id?: string | null;
            /** Reason */
            reason: string;
        };
        /** AdminHotel */
        AdminHotel: {
            counts: components["schemas"]["HotelCounts"];
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Last Activity */
            last_activity: string | null;
            /** Name */
            name: string;
            /** Plan */
            plan: string | null;
            /** Renews On */
            renews_on: string | null;
            /** Slug */
            slug: string;
            /** Status */
            status: string;
            /** Status Reason */
            status_reason: string | null;
            /** Subscription Status */
            subscription_status: string | null;
        };
        /**
         * AdminHotelDetail
         * @description One hotel for the platform team: no guest data, only what running the account needs.
         */
        AdminHotelDetail: {
            /** Country */
            country: string;
            /** Currency */
            currency: string;
            /** Email */
            email: string | null;
            hotel: components["schemas"]["AdminHotel"];
            /** Legal Name */
            legal_name: string | null;
            /** Owners */
            owners: components["schemas"]["HotelOwner"][];
            /** Phone */
            phone: string | null;
            /** Platform Actions */
            platform_actions: components["schemas"]["PlatformAction"][];
            subscription: components["schemas"]["SubscriptionOut"] | null;
            /** Support Grants */
            support_grants: components["schemas"]["SupportGrantOut"][];
            /** Timezone */
            timezone: string;
        };
        /** AdminHotelList */
        AdminHotelList: {
            /** Data */
            data: components["schemas"]["AdminHotel"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** Analytics */
        Analytics: {
            /** Days */
            days: components["schemas"]["AnalyticsDay"][];
        };
        /** AnalyticsDay */
        AnalyticsDay: {
            /** Checkins */
            checkins: number;
            /**
             * Day
             * Format: date
             */
            day: string;
            /** New Hotels */
            new_hotels: number;
            /** Orders */
            orders: number;
        };
        /** AnonymiseOut */
        AnonymiseOut: {
            /** Anonymised */
            anonymised: boolean;
            /**
             * Id
             * Format: uuid
             */
            id: string;
        };
        /** AnonymiseRequest */
        AnonymiseRequest: {
            /** Reason */
            reason: string;
        };
        /** ApiKeyCreate */
        ApiKeyCreate: {
            /**
             * Environment
             * @enum {string}
             */
            environment: "sandbox" | "production";
            /** Name */
            name: string;
            /** Scopes */
            scopes: string[];
        };
        /** ApiKeyCreated */
        ApiKeyCreated: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Created By
             * Format: uuid
             */
            created_by: string;
            /** Environment */
            environment: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Last Used At */
            last_used_at: string | null;
            /** Name */
            name: string;
            /** Prefix */
            prefix: string;
            /** Revoked At */
            revoked_at: string | null;
            /** Scopes */
            scopes: string[];
            /** Secret */
            secret: string;
            /** Status */
            status: string;
            /** Usage Count */
            usage_count: number;
        };
        /** ApiKeyList */
        ApiKeyList: {
            /** Data */
            data: components["schemas"]["ApiKeyOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** ApiKeyOut */
        ApiKeyOut: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Created By
             * Format: uuid
             */
            created_by: string;
            /** Environment */
            environment: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Last Used At */
            last_used_at: string | null;
            /** Name */
            name: string;
            /** Prefix */
            prefix: string;
            /** Revoked At */
            revoked_at: string | null;
            /** Scopes */
            scopes: string[];
            /** Status */
            status: string;
            /** Usage Count */
            usage_count: number;
        };
        /** AssignRequest */
        AssignRequest: {
            /**
             * User Id
             * Format: uuid
             */
            user_id: string;
        };
        /** AuditEntry */
        AuditEntry: {
            /** Action */
            action: string;
            /** Actor Id */
            actor_id: string | null;
            /** Actor Label */
            actor_label: string | null;
            /** Actor Type */
            actor_type: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Device Id */
            device_id: string | null;
            /** Entity Id */
            entity_id: string | null;
            /** Entity Type */
            entity_type: string;
            /** Id */
            id: number;
            /** Ip */
            ip: string | null;
            /** New Value */
            new_value: {
                [key: string]: unknown;
            } | null;
            /** Old Value */
            old_value: {
                [key: string]: unknown;
            } | null;
            /** Reason */
            reason: string | null;
        };
        /** AuditList */
        AuditList: {
            /** Data */
            data: components["schemas"]["AuditEntry"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** AvailabilityChange */
        AvailabilityChange: {
            /** Available */
            available: boolean;
        };
        /** Billing */
        Billing: {
            /** Billing Profile Id */
            billing_profile_id?: string | null;
            /** Purchase Order */
            purchase_order?: string | null;
            /** Traveller Name */
            traveller_name?: string | null;
            /**
             * Type
             * @default personal
             * @enum {string}
             */
            type: "personal" | "company";
        };
        /** BillingProfileCreate */
        BillingProfileCreate: {
            /** Billing Address */
            billing_address?: {
                [key: string]: string;
            };
            /** Billing Email */
            billing_email?: string | null;
            /** Company Name */
            company_name: string;
            /** Registration Number */
            registration_number?: string | null;
            /** Vat Number */
            vat_number?: string | null;
        };
        /** BillingProfileList */
        BillingProfileList: {
            /** Data */
            data: components["schemas"]["BillingProfileOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** BillingProfileOut */
        BillingProfileOut: {
            /** Billing Address */
            billing_address: {
                [key: string]: string;
            };
            /** Billing Email */
            billing_email: string | null;
            /** Company Name */
            company_name: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Registration Number */
            registration_number: string | null;
            /** Vat Number */
            vat_number: string | null;
        };
        /** BulkResult */
        BulkResult: {
            /** Created */
            created: number;
            /** Data */
            data: components["schemas"]["RoomOut"][];
        };
        /** CartLine */
        CartLine: {
            /**
             * Menu Item Id
             * Format: uuid
             */
            menu_item_id: string;
            /** Modifier Option Ids */
            modifier_option_ids?: string[];
            /** Note */
            note?: string | null;
            /** Quantity */
            quantity: number;
        };
        /** CategoryCreate */
        CategoryCreate: {
            /** Name */
            name: string;
            /** Schedule Id */
            schedule_id?: string | null;
            /**
             * Sort Order
             * @default 0
             */
            sort_order: number;
        };
        /** CategoryList */
        CategoryList: {
            /** Data */
            data: components["schemas"]["CategoryOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** CategoryOut */
        CategoryOut: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
            /** Schedule Id */
            schedule_id: string | null;
            /** Sort Order */
            sort_order: number;
        };
        /** CategoryPatch */
        CategoryPatch: {
            /** Name */
            name?: string | null;
            /** Schedule Id */
            schedule_id?: string | null;
            /** Sort Order */
            sort_order?: number | null;
        };
        /** ChangeRequest */
        ChangeRequest: {
            /** Note */
            note?: string | null;
            /** Plan Code */
            plan_code: string;
        };
        /** ChangeRequestOut */
        ChangeRequestOut: {
            /** Requested Plan */
            requested_plan: string;
            /**
             * Status
             * @constant
             */
            status: "received";
        };
        /** ChargeCategoryList */
        ChargeCategoryList: {
            /** Data */
            data: components["schemas"]["ChargeCategoryOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** ChargeCategoryOut */
        ChargeCategoryOut: {
            /** Code */
            code: string;
            /** Group */
            group: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
            /** Vat Rate Bp */
            vat_rate_bp: number | null;
        };
        /** ChargeRequest */
        ChargeRequest: {
            amount: components["schemas"]["Money"];
            /**
             * Charge Category Id
             * Format: uuid
             */
            charge_category_id: string;
            /** Description */
            description: string;
            /**
             * Quantity
             * @default 1
             */
            quantity: number;
        };
        /** CheckoutOut */
        CheckoutOut: {
            /** Emailed To */
            emailed_to: string[];
            invoice: components["schemas"]["InvoiceOut"];
            /** Override Reason */
            override_reason: string | null;
            /** Status */
            status: string;
            /**
             * Stay Id
             * Format: uuid
             */
            stay_id: string;
        };
        /** CheckoutRequest */
        CheckoutRequest: {
            /** Bill Delivery */
            bill_delivery?: ("pdf" | "email")[];
            /**
             * Confirm Long Stay Vat
             * @default false
             */
            confirm_long_stay_vat: boolean;
            /** Email To */
            email_to?: string[];
            /**
             * Override
             * @default false
             */
            override: boolean;
            /** Override Reason */
            override_reason?: string | null;
            recipient_address?: components["schemas"]["Address"] | null;
        };
        /** CheckoutSummary */
        CheckoutSummary: {
            /** By Category */
            by_category: {
                [key: string]: components["schemas"]["SignedMoney"];
            };
            /** Can Check Out */
            can_check_out: boolean;
            /** Flags */
            flags: string[];
            /** Folio Status */
            folio_status: string;
            /** Invoice Kind */
            invoice_kind: string;
            /** Open Orders */
            open_orders: components["schemas"]["OpenOrder"][];
            /** Override Allowed */
            override_allowed: boolean;
            /**
             * Stay Id
             * Format: uuid
             */
            stay_id: string;
            /** Stay Status */
            stay_status: string;
            totals: components["schemas"]["FolioTotals"];
        };
        /** CloseAdjustment */
        CloseAdjustment: {
            /** Decided By */
            decided_by: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            new_amount: components["schemas"]["SignedMoney"];
            original: components["schemas"]["SignedMoney"];
            /** Reason */
            reason: string;
            /** Requested By */
            requested_by: string | null;
            /** Status */
            status: string;
        };
        /** CloseCard */
        CloseCard: {
            recorded: components["schemas"]["SignedMoney"];
            terminal_batch_total: components["schemas"]["SignedMoney"] | null;
        };
        /** CloseCash */
        CloseCash: {
            counted: components["schemas"]["SignedMoney"] | null;
            recorded: components["schemas"]["SignedMoney"];
        };
        /** CloseDiscount */
        CloseDiscount: {
            amount: components["schemas"]["SignedMoney"] | null;
            /** Applies To */
            applies_to: string;
            /** Given By */
            given_by: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Kind */
            kind: string;
            /** Percent Bp */
            percent_bp: number | null;
            /** Reason */
            reason: string | null;
        };
        /** CloseLateEntry */
        CloseLateEntry: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Kind
             * @enum {string}
             */
            kind: "payment" | "order";
            /**
             * Occurred At
             * Format: date-time
             */
            occurred_at: string;
            /** Reason */
            reason: string;
        };
        /** CloseOverride */
        CloseOverride: {
            /** Reason */
            reason: string;
            /** Room */
            room: string;
            /**
             * Stay Id
             * Format: uuid
             */
            stay_id: string;
        };
        /** ClosePayments */
        ClosePayments: {
            /** By Method */
            by_method: components["schemas"]["PaymentByMethod"][];
            /** By Staff */
            by_staff: components["schemas"]["PaymentByStaff"][];
            total: components["schemas"]["PaymentLine"];
        };
        /** CloseTips */
        CloseTips: {
            /** Name */
            name: string;
            /** Staff Id */
            staff_id: string | null;
            tips: components["schemas"]["SignedMoney"];
        };
        /** CreditNoteRequest */
        CreditNoteRequest: {
            /** Reason */
            reason: string;
        };
        /** CurrencyList */
        CurrencyList: {
            /** Data */
            data: components["schemas"]["CurrencyOut"][];
        };
        /** CurrencyOut */
        CurrencyOut: {
            /** Code */
            code: string;
            /** Name */
            name: string;
            /** Symbol */
            symbol: string;
        };
        /** DailyClosePut */
        DailyClosePut: {
            cash_counted?: components["schemas"]["Money"] | null;
            /**
             * Mark Reviewed
             * @default false
             */
            mark_reviewed: boolean;
            /** Notes */
            notes?: string | null;
            terminal_batch_total?: components["schemas"]["Money"] | null;
        };
        /** DailyCloseReport */
        DailyCloseReport: {
            /** Adjustments */
            adjustments: components["schemas"]["CloseAdjustment"][];
            card: components["schemas"]["CloseCard"];
            cash: components["schemas"]["CloseCash"];
            /**
             * Date
             * Format: date
             */
            date: string;
            /** Discounts */
            discounts: components["schemas"]["CloseDiscount"][];
            /** Flags */
            flags: string[];
            /** Late Entries */
            late_entries: components["schemas"]["CloseLateEntry"][];
            /** Notes */
            notes: string | null;
            /** Overrides */
            overrides: components["schemas"]["CloseOverride"][];
            payments: components["schemas"]["ClosePayments"];
            revenue: components["schemas"]["RevenueRow"];
            /** Reviewed At */
            reviewed_at: string | null;
            /** Reviewed By */
            reviewed_by: string | null;
            /** Tips By Staff */
            tips_by_staff: components["schemas"]["CloseTips"][];
        };
        /** DeviceInfo */
        DeviceInfo: {
            /** App Version */
            app_version?: string | null;
            /** Model */
            model?: string | null;
            /** Os */
            os?: string | null;
        };
        /** DeviceList */
        DeviceList: {
            /** Data */
            data: components["schemas"]["DeviceOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** DeviceOut */
        DeviceOut: {
            /** App Version */
            app_version: string | null;
            /**
             * Connection
             * @enum {string}
             */
            connection: "online" | "offline" | "needs_pairing";
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Kind
             * @enum {string}
             */
            kind: "guest" | "kitchen";
            /** Label */
            label: string;
            /** Last Seen At */
            last_seen_at: string | null;
            /** Os */
            os: string | null;
            /** Paired At */
            paired_at: string | null;
            room: components["schemas"]["RoomRef"] | null;
            /** Stations */
            stations: components["schemas"]["Ref"][];
            /**
             * Status
             * @enum {string}
             */
            status: "active" | "locked" | "disabled" | "reset_required" | "revoked";
        };
        /** DeviceTokenRequest */
        DeviceTokenRequest: {
            /** Device Credential */
            device_credential: string;
        };
        /** DeviceTokenResponse */
        DeviceTokenResponse: {
            /** Access Token */
            access_token: string;
            /**
             * Device Id
             * Format: uuid
             */
            device_id: string;
            /** Expires In */
            expires_in: number;
            /**
             * Token Type
             * @default Bearer
             * @constant
             */
            token_type: "Bearer";
        };
        /** DiscountRequest */
        DiscountRequest: {
            amount?: components["schemas"]["Money"] | null;
            /**
             * Applies To
             * @enum {string}
             */
            applies_to: "accommodation" | "fnb" | "other" | "all";
            /**
             * Kind
             * @enum {string}
             */
            kind: "percent" | "fixed";
            /** Percent Bp */
            percent_bp?: number | null;
            /** Reason */
            reason: string;
        };
        /** FlagChange */
        FlagChange: {
            /** Enabled */
            enabled: boolean;
            /** Hotel Id */
            hotel_id?: string | null;
            /** Key */
            key: string;
        };
        /** FlagList */
        FlagList: {
            /** Data */
            data: components["schemas"]["FlagOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** FlagOut */
        FlagOut: {
            /** Enabled */
            enabled: boolean;
            /** Hotel Id */
            hotel_id: string | null;
            /** Key */
            key: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** Updated By */
            updated_by: string | null;
        };
        /** FlagPatch */
        FlagPatch: {
            /** Changes */
            changes: components["schemas"]["FlagChange"][];
        };
        /** FolioEntryOut */
        FolioEntryOut: {
            amount: components["schemas"]["SignedMoney"];
            /**
             * Business Date
             * Format: date
             */
            business_date: string;
            /** Category */
            category: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Description */
            description: string;
            /** Group */
            group: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Order Id */
            order_id: string | null;
            /** Payment Id */
            payment_id: string | null;
            /** Quantity */
            quantity: number;
            /** Reverses Entry Id */
            reverses_entry_id: string | null;
            /** Type */
            type: string;
            unit_amount: components["schemas"]["SignedMoney"];
            vat: components["schemas"]["SignedMoney"];
        };
        /** FolioLineOut */
        FolioLineOut: {
            amount: components["schemas"]["SignedMoney"];
            /**
             * Date
             * Format: date
             */
            date: string;
            /** Description */
            description: string;
        };
        /** FolioOut */
        FolioOut: {
            /** By Category */
            by_category: {
                [key: string]: components["schemas"]["SignedMoney"];
            };
            /** Entries */
            entries: components["schemas"]["FolioEntryOut"][];
            /**
             * Folio Id
             * Format: uuid
             */
            folio_id: string;
            /** Status */
            status: string;
            /**
             * Stay Id
             * Format: uuid
             */
            stay_id: string;
            totals: components["schemas"]["FolioTotals"];
        };
        /** FolioSummary */
        FolioSummary: {
            accommodation: components["schemas"]["SignedMoney"];
            balance: components["schemas"]["SignedMoney"];
            fnb: components["schemas"]["SignedMoney"];
            /**
             * Folio Id
             * Format: uuid
             */
            folio_id: string;
            other: components["schemas"]["SignedMoney"];
            paid: components["schemas"]["SignedMoney"];
            /** Status */
            status: string;
            tips: components["schemas"]["SignedMoney"];
        };
        /** FolioTotals */
        FolioTotals: {
            accommodation: components["schemas"]["SignedMoney"];
            balance: components["schemas"]["SignedMoney"];
            fnb: components["schemas"]["SignedMoney"];
            other: components["schemas"]["SignedMoney"];
            paid: components["schemas"]["SignedMoney"];
            tips: components["schemas"]["SignedMoney"];
            vat_included: components["schemas"]["SignedMoney"];
        };
        /** ForgotPasswordRequest */
        ForgotPasswordRequest: {
            /** Email */
            email: string;
        };
        /** GuestCreate */
        GuestCreate: {
            /** Email */
            email?: string | null;
            /** Name */
            name: string;
            /** Nationality */
            nationality?: string | null;
            /** Phone */
            phone?: string | null;
        };
        /** GuestFolio */
        GuestFolio: {
            /** Accommodation */
            accommodation: components["schemas"]["FolioLineOut"][];
            /** Food And Beverage */
            food_and_beverage: components["schemas"]["FolioLineOut"][];
            /** Other */
            other: components["schemas"]["FolioLineOut"][];
            /** Payments */
            payments: components["schemas"]["FolioLineOut"][];
            /** Tips */
            tips: components["schemas"]["FolioLineOut"][];
            /** Totals */
            totals: {
                [key: string]: components["schemas"]["SignedMoney"];
            };
        };
        /** GuestInfo */
        GuestInfo: {
            /**
             * Checkout Time
             * Format: time
             */
            checkout_time: string;
            /** Email */
            email: string | null;
            /** Hotel Name */
            hotel_name: string;
            /** Pages */
            pages: components["schemas"]["InfoPage"][];
            /** Phone */
            phone: string | null;
            /** Wifi Name */
            wifi_name: string | null;
        };
        /** GuestList */
        GuestList: {
            /** Data */
            data: components["schemas"]["GuestOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** GuestMenu */
        GuestMenu: {
            /** Categories */
            categories: components["schemas"]["GuestMenuCategory"][];
        };
        /** GuestMenuCategory */
        GuestMenuCategory: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Items */
            items: components["schemas"]["GuestMenuItem"][];
            /** Name */
            name: string;
        };
        /** GuestMenuItem */
        GuestMenuItem: {
            /** Allergens */
            allergens: string[];
            /** Available Now */
            available_now: boolean;
            /** Description */
            description: string | null;
            /** Dietary Tags */
            dietary_tags: string[];
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Image Url */
            image_url: string | null;
            /** Modifier Groups */
            modifier_groups: {
                [key: string]: unknown;
            }[];
            /** Name */
            name: string;
            /** Next Available At */
            next_available_at: string | null;
            price: components["schemas"]["Money"];
        };
        /** GuestOut */
        GuestOut: {
            /** Anonymised */
            anonymised: boolean;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Email */
            email: string | null;
            /** Has Id Number */
            has_id_number: boolean;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
            /** Nationality */
            nationality: string | null;
            /** Phone */
            phone: string | null;
        };
        /** GuestPatch */
        GuestPatch: {
            /** Email */
            email?: string | null;
            /** Id Number */
            id_number?: string | null;
            /** Name */
            name?: string | null;
            /** Nationality */
            nationality?: string | null;
            /** Phone */
            phone?: string | null;
        };
        /**
         * GuestRecordCreate
         * @description `POST /guests`: a guest record may also carry an ID number.
         */
        GuestRecordCreate: {
            /** Email */
            email?: string | null;
            /** Id Number */
            id_number?: string | null;
            /** Name */
            name: string;
            /** Nationality */
            nationality?: string | null;
            /** Phone */
            phone?: string | null;
        };
        /** GuestRef */
        GuestRef: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
        };
        /** GuestSession */
        GuestSession: {
            /** Hotel */
            hotel: {
                [key: string]: unknown;
            };
            /** Ordering Enabled */
            ordering_enabled: boolean;
            /** Room */
            room: {
                [key: string]: unknown;
            };
            /**
             * State
             * @enum {string}
             */
            state: "active" | "idle" | "locked" | "suspended";
            /** Stay */
            stay: {
                [key: string]: unknown;
            } | null;
        };
        /** HTTPValidationError */
        HTTPValidationError: {
            /** Detail */
            detail?: components["schemas"]["ValidationError"][];
        };
        /** Health */
        Health: {
            /**
             * Checked At
             * Format: date-time
             */
            checked_at: string;
            /** Checks */
            checks: {
                [key: string]: components["schemas"]["HealthCheck"];
            };
            /** Status */
            status: string;
        };
        /** HealthCheck */
        HealthCheck: {
            /** Status */
            status: string;
        } & {
            [key: string]: unknown;
        };
        /** HeartbeatRequest */
        HeartbeatRequest: {
            /** App Version */
            app_version?: string | null;
            /** Battery */
            battery?: number | null;
            /** Completed Commands */
            completed_commands?: ("RESET" | "LOCK")[];
            /** Network */
            network?: string | null;
        };
        /** HeartbeatResponse */
        HeartbeatResponse: {
            /** Commands */
            commands: ("RESET" | "LOCK")[];
            /**
             * Server Time
             * Format: date-time
             */
            server_time: string;
            /**
             * Status
             * @enum {string}
             */
            status: "active" | "locked" | "disabled" | "reset_required" | "revoked";
        };
        /** HistoryOut */
        HistoryOut: {
            /**
             * At
             * Format: date-time
             */
            at: string;
            /** From Status */
            from_status: string | null;
            /** To Status */
            to_status: string;
        };
        /** HotelCounts */
        HotelCounts: {
            /** Active Stays */
            active_stays: number;
            /** Connected Devices */
            connected_devices: number;
            /** Devices */
            devices: number;
            /** Rooms */
            rooms: number;
            /** Staff */
            staff: number;
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
            plan: components["schemas"]["app__schemas__hotel__PlanOut"] | null;
            /** Slug */
            slug: string;
            /** Status */
            status: string;
            /** Version */
            version: number;
        };
        /** HotelOwner */
        HotelOwner: {
            /** Email */
            email: string;
            /** Name */
            name: string;
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
        /** HotelStatusOut */
        HotelStatusOut: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
            /** Status */
            status: string;
            /** Status Reason */
            status_reason: string | null;
        };
        /** HotelSubscription */
        HotelSubscription: {
            /** Limits */
            limits: {
                [key: string]: unknown;
            };
            /** Plan */
            plan: {
                [key: string]: unknown;
            } | null;
            /** Renews On */
            renews_on: string | null;
            /** Starts On */
            starts_on: string | null;
            /** Status */
            status: string | null;
            /** Usage */
            usage: {
                [key: string]: components["schemas"]["Usage"];
            };
        };
        /** HourCount */
        HourCount: {
            /** Hour */
            hour: number;
            /** Orders */
            orders: number;
        };
        /** ImageUploadOut */
        ImageUploadOut: {
            /**
             * Expires At
             * Format: date-time
             */
            expires_at: string;
            /** Headers */
            headers: {
                [key: string]: string;
            };
            /** Max Bytes */
            max_bytes: number;
            /** Method */
            method: string;
            /** Upload Url */
            upload_url: string;
        };
        /** ImageUploadRequest */
        ImageUploadRequest: {
            /**
             * Content Type
             * @enum {string}
             */
            content_type: "image/jpeg" | "image/webp";
            /** Size Bytes */
            size_bytes: number;
        };
        /** ImportProblem */
        ImportProblem: {
            /** Field */
            field: string;
            /** Line */
            line: number;
            /** Problem */
            problem: string;
        };
        /** ImportReport */
        ImportReport: {
            /** Committed */
            committed: boolean;
            /** Created */
            created: number;
            /** Errors */
            errors: components["schemas"]["ImportProblem"][];
            /** Rows */
            rows: number;
            /** Valid */
            valid: boolean;
        };
        /**
         * InfoPage
         * @description A page of hotel information on the guest tablet, such as breakfast times or the spa.
         */
        InfoPage: {
            /** Body */
            body: string;
            /** Title */
            title: string;
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
        /** InvitationCreate */
        InvitationCreate: {
            /** Department */
            department?: string | null;
            /**
             * Email
             * Format: email
             */
            email: string;
            /** Name */
            name: string;
            /** Role Ids */
            role_ids: string[];
        };
        /** InvitationList */
        InvitationList: {
            /** Data */
            data: components["schemas"]["InvitationOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** InvitationOut */
        InvitationOut: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Department */
            department: string | null;
            /** Email */
            email: string;
            /**
             * Expires At
             * Format: date-time
             */
            expires_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Invited By */
            invited_by: string | null;
            /** Name */
            name: string;
            /** Roles */
            roles: components["schemas"]["RoleRef"][];
        };
        /** InvoiceEmailOut */
        InvoiceEmailOut: {
            /**
             * Invoice Id
             * Format: uuid
             */
            invoice_id: string;
            /** Queued To */
            queued_to: string[];
        };
        /** InvoiceEmailRequest */
        InvoiceEmailRequest: {
            /** To */
            to: string[];
        };
        /** InvoiceItemOut */
        InvoiceItemOut: {
            amount: components["schemas"]["SignedMoney"];
            /** Category */
            category: string;
            /** Description */
            description: string;
            /** Line No */
            line_no: number;
            /** Quantity */
            quantity: number;
            vat: components["schemas"]["SignedMoney"];
            /** Vat Rate Bp */
            vat_rate_bp: number;
        };
        /** InvoiceList */
        InvoiceList: {
            /** Data */
            data: components["schemas"]["InvoiceOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** InvoiceOut */
        InvoiceOut: {
            /** By Category */
            by_category: {
                [key: string]: components["schemas"]["SignedMoney"];
            };
            /** Credits Invoice Id */
            credits_invoice_id: string | null;
            /** Flags */
            flags: string[];
            /**
             * Folio Id
             * Format: uuid
             */
            folio_id: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Issued At
             * Format: date-time
             */
            issued_at: string;
            /** Items */
            items: components["schemas"]["InvoiceItemOut"][];
            /** Kind */
            kind: string;
            /** Number */
            number: string;
            /** Reason */
            reason: string | null;
            /** Recipient */
            recipient: {
                [key: string]: unknown;
            };
            /** Sha256 */
            sha256: string | null;
            /**
             * Stay Id
             * Format: uuid
             */
            stay_id: string;
            /** Supplier */
            supplier: {
                [key: string]: unknown;
            };
            /** Title */
            title: string;
            totals: components["schemas"]["InvoiceTotals"];
        };
        /** InvoiceTotals */
        InvoiceTotals: {
            accommodation: components["schemas"]["SignedMoney"];
            balance: components["schemas"]["SignedMoney"];
            charges: components["schemas"]["SignedMoney"];
            fnb: components["schemas"]["SignedMoney"];
            other: components["schemas"]["SignedMoney"];
            paid: components["schemas"]["SignedMoney"];
            tips: components["schemas"]["SignedMoney"];
            vat_included: components["schemas"]["SignedMoney"];
        };
        /** ItemCreate */
        ItemCreate: {
            /** Allergens */
            allergens?: ("gluten" | "crustaceans" | "egg" | "fish" | "peanuts" | "soy" | "dairy" | "tree_nuts" | "celery" | "mustard" | "sesame" | "sulphites" | "lupin" | "molluscs")[];
            /**
             * Category Id
             * Format: uuid
             */
            category_id: string;
            /**
             * Charge Category
             * @default food
             * @enum {string}
             */
            charge_category: "food" | "beverage";
            /** Description */
            description?: string | null;
            /** Dietary Tags */
            dietary_tags?: ("vegetarian" | "vegan" | "halaal" | "kosher" | "gluten_free")[];
            /** Ingredients */
            ingredients?: string[];
            /** Name */
            name: string;
            price: components["schemas"]["Money"];
            /** Schedule Id */
            schedule_id?: string | null;
            /**
             * Sort Order
             * @default 0
             */
            sort_order: number;
            /**
             * Station Id
             * Format: uuid
             */
            station_id: string;
            /** Vat Rate Bp */
            vat_rate_bp?: number | null;
        };
        /** ItemLine */
        ItemLine: {
            /** Menu Item Id */
            menu_item_id: string | null;
            /** Name */
            name: string;
            /** Quantity */
            quantity: number;
            revenue: components["schemas"]["SignedMoney"];
        };
        /** ItemList */
        ItemList: {
            /** Data */
            data: components["schemas"]["ItemOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** ItemModifierGroups */
        ItemModifierGroups: {
            /** Group Ids */
            group_ids: string[];
        };
        /** ItemOut */
        ItemOut: {
            /** Allergens */
            allergens: string[];
            /** Available Now */
            available_now: boolean;
            /**
             * Category Id
             * Format: uuid
             */
            category_id: string;
            /**
             * Charge Category
             * @enum {string}
             */
            charge_category: "food" | "beverage";
            /** Description */
            description: string | null;
            /** Dietary Tags */
            dietary_tags: string[];
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Image Url */
            image_url: string | null;
            /** Ingredients */
            ingredients: string[];
            /** Is Available */
            is_available: boolean;
            /** Modifier Groups */
            modifier_groups: components["schemas"]["ModifierGroupOut"][];
            /** Name */
            name: string;
            /** Next Available At */
            next_available_at?: string | null;
            price: components["schemas"]["Money"];
            /** Schedule Id */
            schedule_id: string | null;
            /** Sort Order */
            sort_order: number;
            /**
             * Station Id
             * Format: uuid
             */
            station_id: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** Vat Rate Bp */
            vat_rate_bp: number | null;
            /** Version */
            version: number;
        };
        /** ItemPatch */
        ItemPatch: {
            /** Allergens */
            allergens?: ("gluten" | "crustaceans" | "egg" | "fish" | "peanuts" | "soy" | "dairy" | "tree_nuts" | "celery" | "mustard" | "sesame" | "sulphites" | "lupin" | "molluscs")[] | null;
            /** Category Id */
            category_id?: string | null;
            /** Charge Category */
            charge_category?: ("food" | "beverage") | null;
            /** Description */
            description?: string | null;
            /** Dietary Tags */
            dietary_tags?: ("vegetarian" | "vegan" | "halaal" | "kosher" | "gluten_free")[] | null;
            /** Ingredients */
            ingredients?: string[] | null;
            /** Name */
            name?: string | null;
            price?: components["schemas"]["Money"] | null;
            /** Schedule Id */
            schedule_id?: string | null;
            /** Sort Order */
            sort_order?: number | null;
            /** Station Id */
            station_id?: string | null;
            /** Vat Rate Bp */
            vat_rate_bp?: number | null;
        };
        /** ItemsReport */
        ItemsReport: {
            /**
             * From
             * Format: date
             */
            from: string;
            /** Items */
            items: components["schemas"]["ItemLine"][];
            /**
             * To
             * Format: date
             */
            to: string;
        };
        /** KitchenBoard */
        KitchenBoard: {
            /** Data */
            data: components["schemas"]["KitchenOrder"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** KitchenItem */
        KitchenItem: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Mine */
            mine: boolean;
            /** Modifiers */
            modifiers: {
                [key: string]: string;
            }[];
            /** Name */
            name: string;
            /** Note */
            note: string | null;
            /** Prep Status */
            prep_status: string;
            /** Quantity */
            quantity: number;
            /** Ready At */
            ready_at: string | null;
            /** Station */
            station: {
                [key: string]: unknown;
            };
        };
        /** KitchenOrder */
        KitchenOrder: {
            /** Accepted At */
            accepted_at: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Items */
            items: components["schemas"]["KitchenItem"][];
            /** Number */
            number: number;
            /** Ready At */
            ready_at: string | null;
            /** Room */
            room: string;
            /** Special Instructions */
            special_instructions: string | null;
            /** Status */
            status: string;
        };
        /** KitchenReport */
        KitchenReport: {
            /**
             * From
             * Format: date
             */
            from: string;
            /** Stations */
            stations: components["schemas"]["StationTimes"][];
            /**
             * To
             * Format: date
             */
            to: string;
        };
        /** KitchenSession */
        KitchenSession: {
            /** Access Token */
            access_token: string;
            /** Expires In */
            expires_in: number;
            /** Token Type */
            token_type: string;
            user: components["schemas"]["KitchenUser"];
        };
        /** KitchenSignIn */
        KitchenSignIn: {
            /** Pin */
            pin: string;
            /**
             * User Id
             * Format: uuid
             */
            user_id: string;
        };
        /** KitchenStaff */
        KitchenStaff: {
            /** Name */
            name: string;
            /**
             * User Id
             * Format: uuid
             */
            user_id: string;
        };
        /** KitchenStaffList */
        KitchenStaffList: {
            /** Data */
            data: components["schemas"]["KitchenStaff"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** KitchenUser */
        KitchenUser: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
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
        /** LogoUploadOut */
        LogoUploadOut: {
            /**
             * Expires At
             * Format: date-time
             */
            expires_at: string;
            /** Headers */
            headers: {
                [key: string]: string;
            };
            /** Max Bytes */
            max_bytes: number;
            /** Method */
            method: string;
            /** Upload Url */
            upload_url: string;
        };
        /** LogoUploadRequest */
        LogoUploadRequest: {
            /**
             * Content Type
             * @enum {string}
             */
            content_type: "image/png" | "image/jpeg" | "image/svg+xml";
            /** Size Bytes */
            size_bytes: number;
        };
        /** MeHotel */
        MeHotel: {
            /** Currency */
            currency: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
            /** Status */
            status: string;
        };
        /**
         * MeOut
         * @description Who is signed in and what they may do, so apps show only usable actions. The server
         *     still checks every permission on every request.
         */
        MeOut: {
            hotel: components["schemas"]["MeHotel"] | null;
            /** Kind */
            kind: string;
            /** Mfa */
            mfa: boolean;
            /** Mfa Pending */
            mfa_pending: boolean;
            /** Permissions */
            permissions: string[];
            /** Roles */
            roles: string[];
            user: components["schemas"]["UserOut"] | null;
        };
        /** MenuImportProblem */
        MenuImportProblem: {
            /** Field */
            field: string;
            /** Line */
            line: number;
            /** Problem */
            problem: string;
        };
        /** MenuImportReport */
        MenuImportReport: {
            /** Committed */
            committed: boolean;
            /** Created */
            created: number;
            /** Errors */
            errors: components["schemas"]["MenuImportProblem"][];
            /** New Categories */
            new_categories: string[];
            /** Rows */
            rows: number;
            /** Valid */
            valid: boolean;
        };
        /** Metrics */
        Metrics: {
            /** Active Hotels */
            active_hotels: number;
            /** Active Stays */
            active_stays: number;
            /** Active Subscriptions */
            active_subscriptions: number;
            /**
             * As Of
             * Format: date-time
             */
            as_of: string;
            /** Cancelled This Month */
            cancelled_this_month: number;
            /** Churn Bp */
            churn_bp: number;
            /** Connected Devices */
            connected_devices: number;
            /** Hotels */
            hotels: number;
            /** Mrr */
            mrr: components["schemas"]["SignedMoney"][];
            /** Orders This Month */
            orders_this_month: number;
            /** Orders Today */
            orders_today: number;
            /** Pending Hotels */
            pending_hotels: number;
            /** Rooms */
            rooms: number;
            /** Suspended Hotels */
            suspended_hotels: number;
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
        /** ModifierGroupCreate */
        ModifierGroupCreate: {
            /**
             * Max Select
             * @default 1
             */
            max_select: number;
            /**
             * Min Select
             * @default 0
             */
            min_select: number;
            /** Name */
            name: string;
        };
        /** ModifierGroupList */
        ModifierGroupList: {
            /** Data */
            data: components["schemas"]["ModifierGroupOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** ModifierGroupOut */
        ModifierGroupOut: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Max Select */
            max_select: number;
            /** Min Select */
            min_select: number;
            /** Name */
            name: string;
            /** Options */
            options: components["schemas"]["ModifierOptionOut"][];
        };
        /** ModifierOptionCreate */
        ModifierOptionCreate: {
            /** Name */
            name: string;
            price_delta: components["schemas"]["Money"];
            /**
             * Sort Order
             * @default 0
             */
            sort_order: number;
        };
        /** ModifierOptionOut */
        ModifierOptionOut: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Is Available */
            is_available: boolean;
            /** Name */
            name: string;
            price_delta: components["schemas"]["Money"];
            /** Sort Order */
            sort_order: number;
        };
        /** Money */
        Money: {
            /** Amount Minor */
            amount_minor: number;
            /** Currency */
            currency: string;
        };
        /** OccupancyNight */
        OccupancyNight: {
            /** Available */
            available: number;
            /**
             * Date
             * Format: date
             */
            date: string;
            /** Occupancy Bp */
            occupancy_bp: number;
            /** Occupied */
            occupied: number;
            /** Out Of Service */
            out_of_service: number;
            /** Rooms */
            rooms: number;
        };
        /** OccupancyReport */
        OccupancyReport: {
            /**
             * From
             * Format: date
             */
            from: string;
            /** Nights */
            nights: components["schemas"]["OccupancyNight"][];
            /**
             * To
             * Format: date
             */
            to: string;
            total: components["schemas"]["OccupancyTotal"];
        };
        /** OccupancyTotal */
        OccupancyTotal: {
            /** Available */
            available: number;
            /** Occupancy Bp */
            occupancy_bp: number;
            /** Occupied */
            occupied: number;
            /** Out Of Service */
            out_of_service: number;
            /** Rooms */
            rooms: number;
        };
        /** OnboardingOut */
        OnboardingOut: {
            /** Completed */
            completed: number;
            /** Next Step */
            next_step: string | null;
            /** Steps */
            steps: components["schemas"]["OnboardingStep"][];
            /** Total */
            total: number;
        };
        /** OnboardingStep */
        OnboardingStep: {
            /** Done */
            done: boolean;
            /** Key */
            key: string;
            /** Title */
            title: string;
        };
        /** OpenBalance */
        OpenBalance: {
            balance: components["schemas"]["SignedMoney"];
            /** Bill To */
            bill_to: string;
            /** Billing Type */
            billing_type: string;
            /** Checked Out At */
            checked_out_at: string | null;
            /** Override Reason */
            override_reason: string | null;
            /** Room */
            room: string;
            /**
             * Stay Id
             * Format: uuid
             */
            stay_id: string;
        };
        /** OpenBalances */
        OpenBalances: {
            /** Data */
            data: components["schemas"]["OpenBalance"][];
            total: components["schemas"]["SignedMoney"];
        };
        /** OpenOrder */
        OpenOrder: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Number */
            number: number;
            /** Status */
            status: string;
        };
        /** OrderItemOut */
        OrderItemOut: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            line_total: components["schemas"]["Money"];
            /** Modifiers */
            modifiers: {
                [key: string]: unknown;
            }[];
            /** Name */
            name: string;
            /** Note */
            note: string | null;
            /** Prep Status */
            prep_status: string;
            /** Quantity */
            quantity: number;
            /**
             * Station Id
             * Format: uuid
             */
            station_id: string;
            unit_price: components["schemas"]["Money"];
        };
        /** OrderList */
        OrderList: {
            /** Data */
            data: components["schemas"]["OrderOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** OrderOut */
        OrderOut: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Decline Reason */
            decline_reason: string | null;
            fee: components["schemas"]["Money"];
            /** History */
            history: components["schemas"]["HistoryOut"][];
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Items */
            items: components["schemas"]["OrderItemOut"][];
            /** Needs Approval */
            needs_approval: boolean;
            /** Number */
            number: number;
            /**
             * Payment Method
             * @enum {string}
             */
            payment_method: "room_charge" | "card_terminal" | "cash";
            /**
             * Placed By
             * @enum {string}
             */
            placed_by: "guest" | "staff";
            /** Room */
            room: string;
            /**
             * Room Id
             * Format: uuid
             */
            room_id: string;
            /** Special Instructions */
            special_instructions: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "PENDING_APPROVAL" | "NEW" | "ACCEPTED" | "PREPARING" | "READY" | "ASSIGNED" | "PICKED_UP" | "DELIVERED" | "CLOSED" | "DECLINED" | "CANCELLED";
            /**
             * Stay Id
             * Format: uuid
             */
            stay_id: string;
            subtotal: components["schemas"]["Money"];
            total: components["schemas"]["Money"];
            vat_included: components["schemas"]["Money"];
        };
        /** OrderPlaced */
        OrderPlaced: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            fee: components["schemas"]["Money"];
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Number */
            number: number;
            /** Room */
            room: string;
            /**
             * Status
             * @enum {string}
             */
            status: "PENDING_APPROVAL" | "NEW" | "ACCEPTED" | "PREPARING" | "READY" | "ASSIGNED" | "PICKED_UP" | "DELIVERED" | "CLOSED" | "DECLINED" | "CANCELLED";
            subtotal: components["schemas"]["Money"];
            total: components["schemas"]["Money"];
            vat_included: components["schemas"]["Money"];
        };
        /** OrdersReport */
        OrdersReport: {
            average_order_value: components["schemas"]["SignedMoney"];
            /** By Hour */
            by_hour: components["schemas"]["HourCount"][];
            /** Cancelled */
            cancelled: number;
            /** Completed Or Open */
            completed_or_open: number;
            /** Declined */
            declined: number;
            /**
             * From
             * Format: date
             */
            from: string;
            /** Orders */
            orders: number;
            /**
             * To
             * Format: date
             */
            to: string;
            value: components["schemas"]["SignedMoney"];
        };
        /** PairRequest */
        PairRequest: {
            /** Code */
            code: string;
            device_info?: components["schemas"]["DeviceInfo"];
        };
        /** PairResponse */
        PairResponse: {
            /**
             * Device Credential
             * @description Shown once. A replay of this request returns null; pair again with a new code.
             */
            device_credential: string | null;
            /**
             * Device Id
             * Format: uuid
             */
            device_id: string;
            hotel: components["schemas"]["Ref"];
            /**
             * Kind
             * @enum {string}
             */
            kind: "guest" | "kitchen";
            /** Label */
            label: string;
            room: components["schemas"]["RoomRef"] | null;
            /** Stations */
            stations: components["schemas"]["Ref"][];
        };
        /** PairingCreate */
        PairingCreate: {
            /** Room Id */
            room_id?: string | null;
            /** Station Id */
            station_id?: string | null;
            /** Station Ids */
            station_ids?: string[] | null;
            /**
             * Type
             * @enum {string}
             */
            type: "guest" | "kitchen";
        };
        /** PairingOut */
        PairingOut: {
            /** Code */
            code: string;
            /**
             * Expires At
             * Format: date-time
             */
            expires_at: string;
            /** Qr Payload */
            qr_payload: string;
        };
        /** PaymentByMethod */
        PaymentByMethod: {
            amount: components["schemas"]["SignedMoney"];
            /** Count */
            count: number;
            /** Method */
            method: string;
            received: components["schemas"]["SignedMoney"];
            tips: components["schemas"]["SignedMoney"];
        };
        /** PaymentByStaff */
        PaymentByStaff: {
            amount: components["schemas"]["SignedMoney"];
            /** Count */
            count: number;
            /** Late */
            late: number;
            /** Name */
            name: string;
            received: components["schemas"]["SignedMoney"];
            /** Staff Id */
            staff_id: string | null;
            tips: components["schemas"]["SignedMoney"];
        };
        /** PaymentLine */
        PaymentLine: {
            amount: components["schemas"]["SignedMoney"];
            /** Count */
            count: number;
            received: components["schemas"]["SignedMoney"];
            tips: components["schemas"]["SignedMoney"];
        };
        /** PaymentList */
        PaymentList: {
            /** Data */
            data: components["schemas"]["PaymentOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** PaymentOut */
        PaymentOut: {
            amount_due: components["schemas"]["Money"];
            amount_received: components["schemas"]["Money"];
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Late Reason */
            late_reason: string | null;
            /** Method */
            method: string;
            /**
             * Occurred At
             * Format: date-time
             */
            occurred_at: string;
            /** Order Id */
            order_id: string | null;
            /** Recorded By */
            recorded_by: {
                [key: string]: unknown;
            } | null;
            /** Status */
            status: string;
            /**
             * Stay Id
             * Format: uuid
             */
            stay_id: string;
            /** Terminal Reference */
            terminal_reference: string | null;
            tip: components["schemas"]["Money"];
        };
        /** PaymentPreview */
        PaymentPreview: {
            amount_due: components["schemas"]["Money"];
            amount_received: components["schemas"]["Money"];
            difference: components["schemas"]["Money"];
            shortfall: components["schemas"]["Money"];
            /**
             * Status
             * @enum {string}
             */
            status: "paid" | "partial";
            tip: components["schemas"]["Money"];
        };
        /** PaymentPreviewRequest */
        PaymentPreviewRequest: {
            amount_received: components["schemas"]["Money"];
            /** Order Id */
            order_id?: string | null;
            /** Stay Id */
            stay_id?: string | null;
        };
        /** PaymentRequest */
        PaymentRequest: {
            amount_received: components["schemas"]["Money"];
            /**
             * Confirm Tip
             * @default false
             */
            confirm_tip: boolean;
            /** Late Reason */
            late_reason?: string | null;
            /**
             * Method
             * @enum {string}
             */
            method: "card_terminal" | "cash" | "eft";
            /** Occurred At */
            occurred_at?: string | null;
            /** Order Id */
            order_id?: string | null;
            /** Stay Id */
            stay_id?: string | null;
            /** Terminal Reference */
            terminal_reference?: string | null;
        };
        /** PaymentsReport */
        PaymentsReport: {
            /** By Method */
            by_method: components["schemas"]["PaymentByMethod"][];
            /** By Staff */
            by_staff: components["schemas"]["PaymentByStaff"][];
            /**
             * From
             * Format: date
             */
            from: string;
            /**
             * To
             * Format: date
             */
            to: string;
            total: components["schemas"]["PaymentLine"];
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
        /** PlaceOrder */
        PlaceOrder: {
            /** Lines */
            lines: components["schemas"]["CartLine"][];
            /**
             * Payment Method
             * @default room_charge
             * @constant
             */
            payment_method: "room_charge";
            quoted_total: components["schemas"]["Money"];
            /** Special Instructions */
            special_instructions?: string | null;
        };
        /** PlanCreate */
        PlanCreate: {
            /** Code */
            code: string;
            /** Features */
            features?: {
                [key: string]: boolean;
            };
            /** Limits */
            limits?: {
                [key: string]: number;
            };
            monthly_price: components["schemas"]["Money"];
            /** Name */
            name: string;
        };
        /** PlanList */
        PlanList: {
            /** Data */
            data: components["schemas"]["app__schemas__admin__PlanOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** PlanPatch */
        PlanPatch: {
            /** Features */
            features?: {
                [key: string]: boolean;
            } | null;
            /** Is Active */
            is_active?: boolean | null;
            /** Limits */
            limits?: {
                [key: string]: number;
            } | null;
            monthly_price?: components["schemas"]["Money"] | null;
            /** Name */
            name?: string | null;
        };
        /** PlatformAction */
        PlatformAction: {
            /** Action */
            action: string;
            /** Actor */
            actor: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Entity Type */
            entity_type: string;
            /** Id */
            id: number;
            /** Reason */
            reason: string | null;
        };
        /** Quote */
        Quote: {
            fee: components["schemas"]["Money"];
            /** Lines */
            lines: components["schemas"]["QuoteLine"][];
            /** Needs Approval */
            needs_approval: boolean;
            subtotal: components["schemas"]["Money"];
            total: components["schemas"]["Money"];
            vat_included: components["schemas"]["Money"];
        };
        /** QuoteLine */
        QuoteLine: {
            line_total: components["schemas"]["Money"];
            /**
             * Menu Item Id
             * Format: uuid
             */
            menu_item_id: string;
            /** Modifiers */
            modifiers: components["schemas"]["QuoteModifier"][];
            /** Name */
            name: string;
            /** Note */
            note: string | null;
            /** Quantity */
            quantity: number;
            unit_price: components["schemas"]["Money"];
        };
        /** QuoteModifier */
        QuoteModifier: {
            /** Group */
            group: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
            price_delta: components["schemas"]["Money"];
        };
        /** QuoteRequest */
        QuoteRequest: {
            /** Lines */
            lines: components["schemas"]["CartLine"][];
        };
        /** ReasonBody */
        ReasonBody: {
            /** Reason */
            reason: string;
        };
        /** ReassignRequest */
        ReassignRequest: {
            /**
             * Room Id
             * Format: uuid
             */
            room_id: string;
        };
        /** Ref */
        Ref: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
        };
        /** RefreshRequest */
        RefreshRequest: {
            /** Hotel Id */
            hotel_id?: string | null;
            /** Refresh Token */
            refresh_token?: string | null;
        };
        /** RejectRequest */
        RejectRequest: {
            /** Reason */
            reason: string;
        };
        /** ResetPasswordRequest */
        ResetPasswordRequest: {
            /** New Password */
            new_password: string;
            /** Token */
            token: string;
        };
        /** RevenueReport */
        RevenueReport: {
            /** Days */
            days: components["schemas"]["RevenueRow"][];
            /**
             * From
             * Format: date
             */
            from: string;
            /**
             * To
             * Format: date
             */
            to: string;
            total: components["schemas"]["RevenueRow"];
        };
        /** RevenueRow */
        RevenueRow: {
            accommodation: components["schemas"]["SignedMoney"];
            adjustments: components["schemas"]["SignedMoney"];
            /** Date */
            date?: string | null;
            discounts: components["schemas"]["SignedMoney"];
            fnb: components["schemas"]["SignedMoney"];
            other: components["schemas"]["SignedMoney"];
            payments: components["schemas"]["SignedMoney"];
            revenue: components["schemas"]["SignedMoney"];
            revenue_excluding_vat: components["schemas"]["SignedMoney"];
            reversals: components["schemas"]["SignedMoney"];
            tips: components["schemas"]["SignedMoney"];
            vat_included: components["schemas"]["SignedMoney"];
        };
        /** RoleCreate */
        RoleCreate: {
            /** Name */
            name: string;
            /** Permissions */
            permissions: string[];
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
        /** RolePatch */
        RolePatch: {
            /** Name */
            name?: string | null;
            /** Permissions */
            permissions?: string[] | null;
        };
        /** RoleRef */
        RoleRef: {
            /** Code */
            code: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
        };
        /** RoomBulkCreate */
        RoomBulkCreate: {
            /** Ranges */
            ranges: components["schemas"]["RoomRange"][];
        };
        /** RoomCreate */
        RoomCreate: {
            /** Amenities */
            amenities?: string[];
            /** Capacity */
            capacity?: number | null;
            /** Floor */
            floor?: string | null;
            /** Number */
            number: string;
            rate?: components["schemas"]["Money"] | null;
            /**
             * Room Type Id
             * Format: uuid
             */
            room_type_id: string;
        };
        /** RoomList */
        RoomList: {
            /** Data */
            data: components["schemas"]["RoomOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** RoomOut */
        RoomOut: {
            /** Amenities */
            amenities: string[];
            /** Capacity */
            capacity: number;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            effective_rate: components["schemas"]["Money"];
            /** Floor */
            floor: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Number */
            number: string;
            rate: components["schemas"]["Money"] | null;
            room_type: components["schemas"]["RoomTypeRef"];
            /**
             * Status
             * @enum {string}
             */
            status: "available" | "occupied" | "reserved" | "cleaning" | "maintenance" | "out_of_service";
            /**
             * Status Changed At
             * Format: date-time
             */
            status_changed_at: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** Version */
            version: number;
        };
        /** RoomPatch */
        RoomPatch: {
            /** Amenities */
            amenities?: string[] | null;
            /** Capacity */
            capacity?: number | null;
            /** Floor */
            floor?: string | null;
            /** Number */
            number?: string | null;
            rate?: components["schemas"]["Money"] | null;
            /** Room Type Id */
            room_type_id?: string | null;
        };
        /** RoomRange */
        RoomRange: {
            /** Floor */
            floor?: number | string | null;
            /** From */
            from: number;
            /**
             * Prefix
             * @default
             */
            prefix: string;
            /**
             * Room Type Id
             * Format: uuid
             */
            room_type_id: string;
            /** To */
            to: number;
        };
        /** RoomRef */
        RoomRef: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Number */
            number: string;
        };
        /** RoomServiceReport */
        RoomServiceReport: {
            /**
             * From
             * Format: date
             */
            from: string;
            /** Staff */
            staff: components["schemas"]["StaffTimes"][];
            /**
             * To
             * Format: date
             */
            to: string;
        };
        /** RoomStatusChange */
        RoomStatusChange: {
            /**
             * Status
             * @enum {string}
             */
            status: "available" | "reserved" | "cleaning" | "maintenance" | "out_of_service";
        };
        /** RoomTypeCreate */
        RoomTypeCreate: {
            /** Amenities */
            amenities?: string[];
            base_rate: components["schemas"]["Money"];
            /**
             * Capacity
             * @default 2
             */
            capacity: number;
            /** Name */
            name: string;
        };
        /** RoomTypeList */
        RoomTypeList: {
            /** Data */
            data: components["schemas"]["RoomTypeOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** RoomTypeOut */
        RoomTypeOut: {
            /** Amenities */
            amenities: string[];
            base_rate: components["schemas"]["Money"];
            /** Capacity */
            capacity: number;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
            /** Room Count */
            room_count: number;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** Version */
            version: number;
        };
        /** RoomTypePatch */
        RoomTypePatch: {
            /** Amenities */
            amenities?: string[] | null;
            base_rate?: components["schemas"]["Money"] | null;
            /** Capacity */
            capacity?: number | null;
            /** Name */
            name?: string | null;
        };
        /** RoomTypeRef */
        RoomTypeRef: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
        };
        /** ScheduleCreate */
        ScheduleCreate: {
            /** Name */
            name: string;
            /** Windows */
            windows: components["schemas"]["Window"][];
        };
        /** ScheduleList */
        ScheduleList: {
            /** Data */
            data: components["schemas"]["ScheduleOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** ScheduleOut */
        ScheduleOut: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
            /** Windows */
            windows: components["schemas"]["Window"][];
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
            /** Guest Id Number Enabled */
            guest_id_number_enabled: boolean;
            /** Info Pages */
            info_pages: components["schemas"]["InfoPage"][];
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
            /** Guest Id Number Enabled */
            guest_id_number_enabled?: boolean | null;
            /** Info Pages */
            info_pages?: components["schemas"]["InfoPage"][] | null;
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
        /**
         * SignedMoney
         * @description Output only: ledger amounts and balances, which may be negative (reversals, credit).
         */
        SignedMoney: {
            /** Amount Minor */
            amount_minor: number;
            /** Currency */
            currency: string;
        };
        /** SignedUrl */
        SignedUrl: {
            /** Expires In */
            expires_in: number;
            /** Url */
            url: string;
        };
        /** SignupHotel */
        SignupHotel: {
            address?: components["schemas"]["Address"] | null;
            /** Currency */
            currency: string;
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
        /** StaffList */
        StaffList: {
            /** Data */
            data: components["schemas"]["StaffMember"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** StaffMember */
        StaffMember: {
            /** Department */
            department: string | null;
            /** Email */
            email: string;
            /** Has Pin */
            has_pin: boolean;
            /**
             * Joined At
             * Format: date-time
             */
            joined_at: string;
            /** Last Sign In At */
            last_sign_in_at: string | null;
            /** Mfa Enabled */
            mfa_enabled: boolean;
            /** Name */
            name: string;
            /** Roles */
            roles: components["schemas"]["RoleRef"][];
            /**
             * Status
             * @enum {string}
             */
            status: "active" | "deactivated";
            /**
             * User Id
             * Format: uuid
             */
            user_id: string;
        };
        /** StaffOrder */
        StaffOrder: {
            /** Late Reason */
            late_reason?: string | null;
            /** Lines */
            lines: components["schemas"]["CartLine"][];
            /**
             * Payment Method
             * @default room_charge
             * @enum {string}
             */
            payment_method: "room_charge" | "card_terminal" | "cash";
            quoted_total: components["schemas"]["Money"];
            /**
             * Room Id
             * Format: uuid
             */
            room_id: string;
            /** Special Instructions */
            special_instructions?: string | null;
        };
        /** StaffPatch */
        StaffPatch: {
            /** Department */
            department?: string | null;
            /** Name */
            name?: string | null;
        };
        /**
         * StaffQuote
         * @description Price a cart for a room before a staff phone order (same server pricing as the tablet).
         */
        StaffQuote: {
            /** Lines */
            lines: components["schemas"]["CartLine"][];
            /**
             * Room Id
             * Format: uuid
             */
            room_id: string;
        };
        /** StaffRoles */
        StaffRoles: {
            /** Role Ids */
            role_ids: string[];
        };
        /** StaffTimes */
        StaffTimes: {
            /** Deliveries */
            deliveries: number;
            /** Median Seconds */
            median_seconds: number;
            /** Name */
            name: string | null;
            /** Staff Id */
            staff_id: string | null;
        };
        /** StationCreate */
        StationCreate: {
            /** Name */
            name: string;
            /**
             * Sort Order
             * @default 0
             */
            sort_order: number;
        };
        /** StationList */
        StationList: {
            /** Data */
            data: components["schemas"]["StationOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** StationOut */
        StationOut: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Is Active */
            is_active: boolean;
            /** Name */
            name: string;
            /** Sort Order */
            sort_order: number;
        };
        /** StationPatch */
        StationPatch: {
            /** Is Active */
            is_active?: boolean | null;
            /** Name */
            name?: string | null;
            /** Sort Order */
            sort_order?: number | null;
        };
        /** StationTimes */
        StationTimes: {
            /** Items */
            items: number;
            /** Median Seconds */
            median_seconds: number;
            /** Name */
            name: string;
            /** P90 Seconds */
            p90_seconds: number;
            /**
             * Station Id
             * Format: uuid
             */
            station_id: string;
        };
        /** StayCreate */
        StayCreate: {
            /**
             * Arrival Date
             * Format: date
             */
            arrival_date: string;
            billing?: components["schemas"]["Billing"];
            /**
             * Departure Date
             * Format: date
             */
            departure_date: string;
            guest?: components["schemas"]["GuestCreate"] | null;
            /** Guest Id */
            guest_id?: string | null;
            rate_override?: components["schemas"]["Money"] | null;
            /** Rate Override Reason */
            rate_override_reason?: string | null;
            /**
             * Room Id
             * Format: uuid
             */
            room_id: string;
            /**
             * Training
             * @default false
             */
            training: boolean;
        };
        /** StayDatesPatch */
        StayDatesPatch: {
            /** Arrival Date */
            arrival_date?: string | null;
            /** Departure Date */
            departure_date?: string | null;
        };
        /** StayList */
        StayList: {
            /** Data */
            data: components["schemas"]["StayOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** StayMove */
        StayMove: {
            /** Reason */
            reason?: string | null;
            /**
             * Room Id
             * Format: uuid
             */
            room_id: string;
        };
        /** StayOut */
        StayOut: {
            /**
             * Arrival Date
             * Format: date
             */
            arrival_date: string;
            /** Billing Profile Id */
            billing_profile_id: string | null;
            /** Billing Type */
            billing_type: string;
            /** Charges Blocked */
            charges_blocked: boolean;
            /** Checked In At */
            checked_in_at: string | null;
            /** Checked Out At */
            checked_out_at: string | null;
            /**
             * Departure Date
             * Format: date
             */
            departure_date: string;
            folio: components["schemas"]["FolioSummary"] | null;
            guest: components["schemas"]["GuestRef"];
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Is Training */
            is_training: boolean;
            nightly_rate: components["schemas"]["Money"];
            /** Nights */
            nights: number;
            /** Purchase Order */
            purchase_order: string | null;
            room: components["schemas"]["RoomRef"];
            /**
             * Status
             * @enum {string}
             */
            status: "reserved" | "checked_in" | "active" | "checkout_pending" | "checked_out" | "cancelled";
            /** Traveller Name */
            traveller_name: string | null;
            /** Version */
            version: number;
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
        /** SubscriptionOut */
        SubscriptionOut: {
            /** Cancelled At */
            cancelled_at: string | null;
            /**
             * Hotel Id
             * Format: uuid
             */
            hotel_id: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Limit Overrides */
            limit_overrides: {
                [key: string]: unknown;
            };
            /** Limits */
            limits: {
                [key: string]: unknown;
            };
            plan: components["schemas"]["app__schemas__admin__PlanOut"];
            /** Renews On */
            renews_on: string | null;
            /**
             * Starts On
             * Format: date
             */
            starts_on: string;
            /** Status */
            status: string;
        };
        /** SubscriptionPut */
        SubscriptionPut: {
            /** Limit Overrides */
            limit_overrides?: {
                [key: string]: number;
            } | null;
            /**
             * Plan Id
             * Format: uuid
             */
            plan_id: string;
            /** Renews On */
            renews_on?: string | null;
            /**
             * Starts On
             * Format: date
             */
            starts_on: string;
            /**
             * Status
             * @enum {string}
             */
            status: "trialing" | "active" | "past_due" | "cancelled";
        };
        /** SupportAccessOut */
        SupportAccessOut: {
            /** Access Token */
            access_token: string;
            grant: components["schemas"]["SupportGrantOut"];
            /** Token Type */
            token_type: string;
        };
        /** SupportGrantList */
        SupportGrantList: {
            /** Data */
            data: components["schemas"]["SupportGrantOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** SupportGrantOut */
        SupportGrantOut: {
            /** Active */
            active: boolean;
            /**
             * Expires At
             * Format: date-time
             */
            expires_at: string;
            /**
             * Hotel Id
             * Format: uuid
             */
            hotel_id: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Platform User Id
             * Format: uuid
             */
            platform_user_id: string;
            /** Reason */
            reason: string | null;
            /** Revoked At */
            revoked_at: string | null;
            /**
             * Starts At
             * Format: date-time
             */
            starts_at: string;
            /** Ticket Reference */
            ticket_reference: string;
        };
        /** SupportRequest */
        SupportRequest: {
            /**
             * Minutes
             * @default 30
             */
            minutes: number;
            /** Reason */
            reason?: string | null;
            /** Ticket Reference */
            ticket_reference: string;
        };
        /** SuspendRequest */
        SuspendRequest: {
            /** Reason */
            reason: string;
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
        /** Usage */
        Usage: {
            /** Limit */
            limit: number | null;
            /** Used */
            used: number;
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
        /** WalkIn */
        WalkIn: {
            billing?: components["schemas"]["Billing"];
            guest?: components["schemas"]["GuestCreate"] | null;
            /** Guest Id */
            guest_id?: string | null;
            /** Nights */
            nights: number;
            rate_override?: components["schemas"]["Money"] | null;
            /** Rate Override Reason */
            rate_override_reason?: string | null;
            /**
             * Training
             * @default false
             */
            training: boolean;
        };
        /** WebhookCreate */
        WebhookCreate: {
            /** Events */
            events: string[];
            /** Url */
            url: string;
        };
        /** WebhookCreated */
        WebhookCreated: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Events */
            events: string[];
            /** Failure Count */
            failure_count: number;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Signing Secret */
            signing_secret: string;
            /** Status */
            status: string;
            /** Url */
            url: string;
        };
        /** WebhookList */
        WebhookList: {
            /** Data */
            data: components["schemas"]["WebhookOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** WebhookOut */
        WebhookOut: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Events */
            events: string[];
            /** Failure Count */
            failure_count: number;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Status */
            status: string;
            /** Url */
            url: string;
        };
        /** WebhookStatusChange */
        WebhookStatusChange: {
            /**
             * Status
             * @enum {string}
             */
            status: "active" | "disabled";
        };
        /** WebhookTestOut */
        WebhookTestOut: {
            /** Queued */
            queued: boolean;
            /** Seq */
            seq: number;
            /**
             * Webhook Id
             * Format: uuid
             */
            webhook_id: string;
        };
        /** Window */
        Window: {
            /** Days */
            days: number[];
            /** From */
            from: string;
            /** To */
            to: string;
        };
        /** PlanOut */
        app__schemas__admin__PlanOut: {
            /** Code */
            code: string;
            /** Features */
            features: {
                [key: string]: unknown;
            };
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Is Active */
            is_active: boolean;
            /** Limits */
            limits: {
                [key: string]: unknown;
            };
            monthly_price: components["schemas"]["SignedMoney"];
            /** Name */
            name: string;
        };
        /** PlanOut */
        app__schemas__hotel__PlanOut: {
            /** Code */
            code: string;
            /** Name */
            name: string;
            /** Subscription Status */
            subscription_status: string;
        };
        /** DeliveryList */
        app__schemas__reports__DeliveryList: {
            /** Data */
            data: components["schemas"]["app__schemas__reports__DeliveryOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** DeliveryOut */
        app__schemas__reports__DeliveryOut: {
            /** Attempt */
            attempt: number;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Error */
            error: string | null;
            /**
             * Event Id
             * Format: uuid
             */
            event_id: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Next Attempt At */
            next_attempt_at: string | null;
            /** State */
            state: string;
            /** Status Code */
            status_code: number | null;
        };
        /** DeliveryList */
        app__schemas__room_service__DeliveryList: {
            /** Data */
            data: components["schemas"]["app__schemas__room_service__DeliveryOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** DeliveryOut */
        app__schemas__room_service__DeliveryOut: {
            amount_due: components["schemas"]["Money"];
            /** Assigned At */
            assigned_at: string | null;
            /** Assigned To */
            assigned_to: {
                [key: string]: unknown;
            } | null;
            /** Delivered At */
            delivered_at: string | null;
            /** Items */
            items: {
                [key: string]: unknown;
            }[];
            /** Number */
            number: number;
            /**
             * Order Id
             * Format: uuid
             */
            order_id: string;
            /** Paid */
            paid: boolean;
            /** Picked Up At */
            picked_up_at: string | null;
            /** Ready At */
            ready_at: string | null;
            /** Room */
            room: string;
            /** Special Instructions */
            special_instructions: string | null;
            /** Status */
            status: string;
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
    list_adjustments_api_v1_adjustments_get: {
        parameters: {
            query?: {
                status?: ("pending" | "approved" | "rejected") | null;
            };
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
                    "application/json": components["schemas"]["AdjustmentList"];
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
    request_adjustment_api_v1_adjustments_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AdjustmentRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AdjustmentOut"];
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
    approve_adjustment_api_v1_adjustments__adjustment_id__approve_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                adjustment_id: string;
            };
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
                    "application/json": components["schemas"]["AdjustmentOut"];
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
    reject_adjustment_api_v1_adjustments__adjustment_id__reject_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                adjustment_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RejectRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AdjustmentOut"];
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
    activity_api_v1_admin_activity_get: {
        parameters: {
            query?: {
                hours?: number;
            };
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
                    "application/json": components["schemas"]["ActivityList"];
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
    analytics_api_v1_admin_analytics_get: {
        parameters: {
            query?: {
                days?: number;
            };
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
                    "application/json": components["schemas"]["Analytics"];
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
    flags_api_v1_admin_feature_flags_get: {
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
                    "application/json": components["schemas"]["FlagList"];
                };
            };
        };
    };
    set_flags_api_v1_admin_feature_flags_patch: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["FlagPatch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["FlagList"];
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
    health_api_v1_admin_health_get: {
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
                    "application/json": components["schemas"]["Health"];
                };
            };
        };
    };
    hotels_api_v1_admin_hotels_get: {
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
                    "application/json": components["schemas"]["AdminHotelList"];
                };
            };
        };
    };
    hotel_detail_api_v1_admin_hotels__hotel_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                hotel_id: string;
            };
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
                    "application/json": components["schemas"]["AdminHotelDetail"];
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
    approve_api_v1_admin_hotels__hotel_id__approve_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                hotel_id: string;
            };
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
                    "application/json": components["schemas"]["HotelStatusOut"];
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
    reactivate_api_v1_admin_hotels__hotel_id__reactivate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                hotel_id: string;
            };
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
                    "application/json": components["schemas"]["HotelStatusOut"];
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
    put_subscription_api_v1_admin_hotels__hotel_id__subscription_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                hotel_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SubscriptionPut"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SubscriptionOut"];
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
    support_access_api_v1_admin_hotels__hotel_id__support_access_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                hotel_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SupportRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SupportAccessOut"];
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
    suspend_api_v1_admin_hotels__hotel_id__suspend_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                hotel_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SuspendRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HotelStatusOut"];
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
    metrics_api_v1_admin_metrics_get: {
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
                    "application/json": components["schemas"]["Metrics"];
                };
            };
        };
    };
    plans_api_v1_admin_plans_get: {
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
                    "application/json": components["schemas"]["PlanList"];
                };
            };
        };
    };
    create_plan_api_v1_admin_plans_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PlanCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["app__schemas__admin__PlanOut"];
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
    update_plan_api_v1_admin_plans__plan_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                plan_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PlanPatch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["app__schemas__admin__PlanOut"];
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
    list_keys_api_v1_api_keys_get: {
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
                    "application/json": components["schemas"]["ApiKeyList"];
                };
            };
        };
    };
    create_key_api_v1_api_keys_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ApiKeyCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ApiKeyCreated"];
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
    revoke_key_api_v1_api_keys__key_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                key_id: string;
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
    audit_logs_api_v1_audit_logs_get: {
        parameters: {
            query?: {
                actor_id?: string | null;
                action?: string | null;
                entity_type?: string | null;
                from?: string | null;
                to?: string | null;
                limit?: number;
                cursor?: string | null;
            };
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
                    "application/json": components["schemas"]["AuditList"];
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
    kitchen_sign_in_api_v1_auth_kitchen_sign_in_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["KitchenSignIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["KitchenSession"];
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
    me_api_v1_auth_me_get: {
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
                    "application/json": components["schemas"]["MeOut"];
                };
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
    search_profiles_api_v1_billing_profiles_get: {
        parameters: {
            query?: {
                q?: string | null;
                limit?: number;
            };
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
                    "application/json": components["schemas"]["BillingProfileList"];
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
    create_profile_api_v1_billing_profiles_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BillingProfileCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BillingProfileOut"];
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
    charge_categories_api_v1_charge_categories_get: {
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
                    "application/json": components["schemas"]["ChargeCategoryList"];
                };
            };
        };
    };
    currencies_api_v1_currencies_get: {
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
                    "application/json": components["schemas"]["CurrencyList"];
                };
            };
        };
    };
    list_deliveries_api_v1_deliveries_get: {
        parameters: {
            query?: {
                scope?: "ready" | "mine" | "all";
            };
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
                    "application/json": components["schemas"]["app__schemas__room_service__DeliveryList"];
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
    assign_api_v1_deliveries__order_id__assign_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                order_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AssignRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["app__schemas__room_service__DeliveryOut"];
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
    claim_api_v1_deliveries__order_id__claim_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                order_id: string;
            };
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
                    "application/json": components["schemas"]["app__schemas__room_service__DeliveryOut"];
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
    delivered_api_v1_deliveries__order_id__delivered_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                order_id: string;
            };
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
                    "application/json": components["schemas"]["app__schemas__room_service__DeliveryOut"];
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
    leave_on_room_api_v1_deliveries__order_id__leave_on_room_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                order_id: string;
            };
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
                    "application/json": components["schemas"]["app__schemas__room_service__DeliveryOut"];
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
    picked_up_api_v1_deliveries__order_id__picked_up_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                order_id: string;
            };
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
                    "application/json": components["schemas"]["app__schemas__room_service__DeliveryOut"];
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
    release_api_v1_deliveries__order_id__release_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                order_id: string;
            };
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
                    "application/json": components["schemas"]["app__schemas__room_service__DeliveryOut"];
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
    list_devices_api_v1_devices_get: {
        parameters: {
            query?: {
                type?: ("guest" | "kitchen") | null;
                status?: ("active" | "locked" | "disabled" | "reset_required" | "revoked") | null;
                room_id?: string | null;
                limit?: number;
                cursor?: string | null;
            };
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
                    "application/json": components["schemas"]["DeviceList"];
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
    heartbeat_api_v1_devices_heartbeat_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["HeartbeatRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["HeartbeatResponse"];
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
    pair_device_api_v1_devices_pair_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PairRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PairResponse"];
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
    create_pairing_api_v1_devices_pairings_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PairingCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PairingOut"];
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
    device_token_api_v1_devices_token_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DeviceTokenRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DeviceTokenResponse"];
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
    get_device_api_v1_devices__device_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                device_id: string;
            };
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
                    "application/json": components["schemas"]["DeviceOut"];
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
    disable_device_api_v1_devices__device_id__disable_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                device_id: string;
            };
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
                    "application/json": components["schemas"]["DeviceOut"];
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
    lock_device_api_v1_devices__device_id__lock_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                device_id: string;
            };
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
                    "application/json": components["schemas"]["DeviceOut"];
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
    unpair_device_api_v1_devices__device_id__pairing_delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                device_id: string;
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
    reassign_device_api_v1_devices__device_id__reassign_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                device_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ReassignRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DeviceOut"];
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
    reset_device_api_v1_devices__device_id__reset_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                device_id: string;
            };
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
                    "application/json": components["schemas"]["DeviceOut"];
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
    unlock_device_api_v1_devices__device_id__unlock_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                device_id: string;
            };
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
                    "application/json": components["schemas"]["DeviceOut"];
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
    get_folio_api_v1_folios__stay_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                stay_id: string;
            };
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
                    "application/json": components["schemas"]["FolioOut"];
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
    add_charge_api_v1_folios__stay_id__charges_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                stay_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ChargeRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["FolioOut"];
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
    add_discount_api_v1_folios__stay_id__discounts_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                stay_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DiscountRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["FolioOut"];
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
    my_folio_api_v1_guest_folio_get: {
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
                    "application/json": components["schemas"]["GuestFolio"];
                };
            };
        };
    };
    info_api_v1_guest_info_get: {
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
                    "application/json": components["schemas"]["GuestInfo"];
                };
            };
        };
    };
    menu_api_v1_guest_menu_get: {
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
                    "application/json": components["schemas"]["GuestMenu"];
                };
            };
        };
    };
    my_orders_api_v1_guest_orders_get: {
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
                    "application/json": components["schemas"]["OrderList"];
                };
            };
        };
    };
    place_order_api_v1_guest_orders_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PlaceOrder"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["OrderPlaced"];
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
    quote_api_v1_guest_orders_quote_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["QuoteRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Quote"];
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
    my_order_api_v1_guest_orders__order_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                order_id: string;
            };
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
                    "application/json": components["schemas"]["OrderOut"];
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
    session_api_v1_guest_session_get: {
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
                    "application/json": components["schemas"]["GuestSession"];
                };
            };
        };
    };
    search_guests_api_v1_guests_get: {
        parameters: {
            query?: {
                q?: string | null;
                limit?: number;
            };
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
                    "application/json": components["schemas"]["GuestList"];
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
    create_guest_api_v1_guests_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["GuestRecordCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GuestOut"];
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
    get_guest_api_v1_guests__guest_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                guest_id: string;
            };
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
                    "application/json": {
                        [key: string]: unknown;
                    };
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
    patch_guest_api_v1_guests__guest_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                guest_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["GuestPatch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GuestOut"];
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
    anonymise_guest_api_v1_guests__guest_id__anonymise_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                guest_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AnonymiseRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AnonymiseOut"];
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
    export_guest_api_v1_guests__guest_id__export_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                guest_id: string;
            };
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
                    "application/json": {
                        [key: string]: unknown;
                    };
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
    start_logo_upload_api_v1_hotel_logo_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LogoUploadRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LogoUploadOut"];
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
    get_onboarding_api_v1_hotel_onboarding_get: {
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
                    "application/json": components["schemas"]["OnboardingOut"];
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
    get_invoice_api_v1_invoices__invoice_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                invoice_id: string;
            };
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
                    "application/json": components["schemas"]["InvoiceOut"];
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
    credit_note_api_v1_invoices__invoice_id__credit_note_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                invoice_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreditNoteRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InvoiceOut"];
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
    email_invoice_api_v1_invoices__invoice_id__email_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                invoice_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["InvoiceEmailRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InvoiceEmailOut"];
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
    invoice_pdf_api_v1_invoices__invoice_id__pdf_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                invoice_id: string;
            };
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
                    "application/json": components["schemas"]["SignedUrl"];
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
    list_stations_api_v1_kitchen_stations_get: {
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
                    "application/json": components["schemas"]["StationList"];
                };
            };
        };
    };
    create_station_api_v1_kitchen_stations_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["StationCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StationOut"];
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
    delete_station_api_v1_kitchen_stations__station_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                station_id: string;
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
    patch_station_api_v1_kitchen_stations__station_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                station_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["StationPatch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StationOut"];
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
    item_ready_api_v1_kitchen_order_items__item_id__ready_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                item_id: string;
            };
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
                    "application/json": components["schemas"]["KitchenOrder"];
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
    item_unready_api_v1_kitchen_order_items__item_id__unready_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                item_id: string;
            };
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
                    "application/json": components["schemas"]["KitchenOrder"];
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
    kitchen_orders_api_v1_kitchen_orders_get: {
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
                    "application/json": components["schemas"]["KitchenBoard"];
                };
            };
        };
    };
    accept_api_v1_kitchen_orders__order_id__accept_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                order_id: string;
            };
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
                    "application/json": components["schemas"]["KitchenOrder"];
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
    start_api_v1_kitchen_orders__order_id__start_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                order_id: string;
            };
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
                    "application/json": components["schemas"]["KitchenOrder"];
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
    sign_in_list_api_v1_kitchen_staff_get: {
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
                    "application/json": components["schemas"]["KitchenStaffList"];
                };
            };
        };
    };
    list_categories_api_v1_menu_categories_get: {
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
                    "application/json": components["schemas"]["CategoryList"];
                };
            };
        };
    };
    create_category_api_v1_menu_categories_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CategoryCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CategoryOut"];
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
    delete_category_api_v1_menu_categories__category_id__delete: {
        parameters: {
            query?: {
                with_items?: boolean;
            };
            header?: never;
            path: {
                category_id: string;
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
    patch_category_api_v1_menu_categories__category_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                category_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CategoryPatch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CategoryOut"];
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
    list_items_api_v1_menu_items_get: {
        parameters: {
            query?: {
                category_id?: string | null;
                station_id?: string | null;
                available?: boolean | null;
            };
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
                    "application/json": components["schemas"]["ItemList"];
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
    create_item_api_v1_menu_items_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ItemCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ItemOut"];
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
    import_items_api_v1_menu_items_import_post: {
        parameters: {
            query?: {
                commit?: boolean;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "text/csv": string;
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MenuImportReport"];
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
    get_item_api_v1_menu_items__item_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                item_id: string;
            };
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
                    "application/json": components["schemas"]["ItemOut"];
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
    delete_item_api_v1_menu_items__item_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                item_id: string;
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
    patch_item_api_v1_menu_items__item_id__patch: {
        parameters: {
            query?: never;
            header?: {
                "If-Match"?: string | null;
            };
            path: {
                item_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ItemPatch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ItemOut"];
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
    set_availability_api_v1_menu_items__item_id__availability_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                item_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AvailabilityChange"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ItemOut"];
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
    start_image_upload_api_v1_menu_items__item_id__image_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                item_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ImageUploadRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ImageUploadOut"];
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
    set_item_groups_api_v1_menu_items__item_id__modifier_groups_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                item_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ItemModifierGroups"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ItemOut"];
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
    list_groups_api_v1_menu_modifier_groups_get: {
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
                    "application/json": components["schemas"]["ModifierGroupList"];
                };
            };
        };
    };
    create_group_api_v1_menu_modifier_groups_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ModifierGroupCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ModifierGroupOut"];
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
    create_option_api_v1_menu_modifier_groups__group_id__options_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                group_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ModifierOptionCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ModifierGroupOut"];
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
    list_schedules_api_v1_menu_schedules_get: {
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
                    "application/json": components["schemas"]["ScheduleList"];
                };
            };
        };
    };
    create_schedule_api_v1_menu_schedules_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ScheduleCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ScheduleOut"];
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
    list_orders_api_v1_orders_get: {
        parameters: {
            query?: {
                status?: ("PENDING_APPROVAL" | "NEW" | "ACCEPTED" | "PREPARING" | "READY" | "ASSIGNED" | "PICKED_UP" | "DELIVERED" | "CLOSED" | "DECLINED" | "CANCELLED") | null;
                room_id?: string | null;
                stay_id?: string | null;
                from?: string | null;
                to?: string | null;
                limit?: number;
                cursor?: string | null;
            };
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
                    "application/json": components["schemas"]["OrderList"];
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
    staff_order_api_v1_orders_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["StaffOrder"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["OrderPlaced"];
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
    staff_quote_api_v1_orders_quote_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["StaffQuote"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Quote"];
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
    get_order_api_v1_orders__order_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                order_id: string;
            };
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
                    "application/json": components["schemas"]["OrderOut"];
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
    approve_api_v1_orders__order_id__approve_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                order_id: string;
            };
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
                    "application/json": components["schemas"]["OrderOut"];
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
    cancel_api_v1_orders__order_id__cancel_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                order_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ReasonBody"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["OrderOut"];
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
    decline_api_v1_orders__order_id__decline_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                order_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ReasonBody"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["OrderOut"];
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
    list_payments_api_v1_payments_get: {
        parameters: {
            query?: {
                method?: ("card_terminal" | "cash" | "eft") | null;
                from?: string | null;
                to?: string | null;
                staff_id?: string | null;
                limit?: number;
                cursor?: string | null;
            };
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
                    "application/json": components["schemas"]["PaymentList"];
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
    record_payment_api_v1_payments_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PaymentRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PaymentOut"];
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
    preview_api_v1_payments_preview_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PaymentPreviewRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PaymentPreview"];
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
    daily_close_api_v1_reports_daily_close_get: {
        parameters: {
            query?: {
                date?: string | null;
            };
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
                    "application/json": components["schemas"]["DailyCloseReport"];
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
    put_daily_close_api_v1_reports_daily_close__day__put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                day: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["DailyClosePut"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["DailyCloseReport"];
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
    items_api_v1_reports_items_get: {
        parameters: {
            query: {
                from: string;
                to: string;
            };
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
                    "application/json": components["schemas"]["ItemsReport"];
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
    kitchen_api_v1_reports_kitchen_get: {
        parameters: {
            query: {
                from: string;
                to: string;
            };
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
                    "application/json": components["schemas"]["KitchenReport"];
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
    occupancy_api_v1_reports_occupancy_get: {
        parameters: {
            query: {
                from: string;
                to: string;
            };
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
                    "application/json": components["schemas"]["OccupancyReport"];
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
    open_balances_api_v1_reports_open_balances_get: {
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
                    "application/json": components["schemas"]["OpenBalances"];
                };
            };
        };
    };
    orders_api_v1_reports_orders_get: {
        parameters: {
            query: {
                from: string;
                to: string;
            };
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
                    "application/json": components["schemas"]["OrdersReport"];
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
    payments_api_v1_reports_payments_get: {
        parameters: {
            query: {
                from: string;
                to: string;
            };
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
                    "application/json": components["schemas"]["PaymentsReport"];
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
    revenue_api_v1_reports_revenue_get: {
        parameters: {
            query: {
                from: string;
                to: string;
            };
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
                    "application/json": components["schemas"]["RevenueReport"];
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
    room_service_api_v1_reports_room_service_get: {
        parameters: {
            query: {
                from: string;
                to: string;
            };
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
                    "application/json": components["schemas"]["RoomServiceReport"];
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
    create_role_api_v1_roles_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RoleCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RoleOut"];
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
    patch_role_api_v1_roles__role_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                role_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RolePatch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RoleOut"];
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
    list_room_types_api_v1_room_types_get: {
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
                    "application/json": components["schemas"]["RoomTypeList"];
                };
            };
        };
    };
    create_room_type_api_v1_room_types_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RoomTypeCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RoomTypeOut"];
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
    patch_room_type_api_v1_room_types__room_type_id__patch: {
        parameters: {
            query?: never;
            header?: {
                "If-Match"?: string | null;
            };
            path: {
                room_type_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RoomTypePatch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RoomTypeOut"];
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
    list_rooms_api_v1_rooms_get: {
        parameters: {
            query?: {
                status?: ("available" | "occupied" | "reserved" | "cleaning" | "maintenance" | "out_of_service") | null;
                floor?: string | null;
                room_type_id?: string | null;
                limit?: number;
                cursor?: string | null;
            };
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
                    "application/json": components["schemas"]["RoomList"];
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
    create_room_api_v1_rooms_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RoomCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RoomOut"];
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
    bulk_create_rooms_api_v1_rooms_bulk_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RoomBulkCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BulkResult"];
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
    import_rooms_api_v1_rooms_import_post: {
        parameters: {
            query?: {
                commit?: boolean;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "text/csv": string;
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ImportReport"];
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
    get_room_api_v1_rooms__room_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                room_id: string;
            };
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
                    "application/json": components["schemas"]["RoomOut"];
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
    delete_room_api_v1_rooms__room_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                room_id: string;
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
    patch_room_api_v1_rooms__room_id__patch: {
        parameters: {
            query?: never;
            header?: {
                "If-Match"?: string | null;
            };
            path: {
                room_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RoomPatch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RoomOut"];
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
    set_room_status_api_v1_rooms__room_id__status_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                room_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RoomStatusChange"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RoomOut"];
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
    walk_in_api_v1_rooms__room_id__walk_in_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                room_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["WalkIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StayOut"];
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
    list_staff_api_v1_staff_get: {
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
                    "application/json": components["schemas"]["StaffList"];
                };
            };
        };
    };
    list_invitations_api_v1_staff_invitations_get: {
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
                    "application/json": components["schemas"]["InvitationList"];
                };
            };
        };
    };
    invite_staff_api_v1_staff_invitations_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["InvitationCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["InvitationOut"];
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
    cancel_invitation_api_v1_staff_invitations__invitation_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                invitation_id: string;
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
    patch_staff_api_v1_staff__user_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["StaffPatch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StaffMember"];
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
    deactivate_staff_api_v1_staff__user_id__deactivate_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: string;
            };
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
                    "application/json": components["schemas"]["StaffMember"];
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
    reset_staff_pin_api_v1_staff__user_id__pin_reset_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: string;
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
    set_staff_roles_api_v1_staff__user_id__roles_put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                user_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["StaffRoles"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StaffMember"];
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
    list_stays_api_v1_stays_get: {
        parameters: {
            query?: {
                status?: ("reserved" | "checked_in" | "active" | "checkout_pending" | "checked_out" | "cancelled") | null;
                room_id?: string | null;
                from?: string | null;
                to?: string | null;
                limit?: number;
                cursor?: string | null;
            };
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
                    "application/json": components["schemas"]["StayList"];
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
    create_stay_api_v1_stays_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["StayCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StayOut"];
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
    get_stay_api_v1_stays__stay_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                stay_id: string;
            };
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
                    "application/json": components["schemas"]["StayOut"];
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
    change_dates_api_v1_stays__stay_id__patch: {
        parameters: {
            query?: never;
            header?: {
                "If-Match"?: string | null;
            };
            path: {
                stay_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["StayDatesPatch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StayOut"];
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
    block_charges_api_v1_stays__stay_id__block_charges_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                stay_id: string;
            };
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
                    "application/json": components["schemas"]["StayOut"];
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
    cancel_stay_api_v1_stays__stay_id__cancel_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                stay_id: string;
            };
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
                    "application/json": components["schemas"]["StayOut"];
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
    check_in_api_v1_stays__stay_id__check_in_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                stay_id: string;
            };
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
                    "application/json": components["schemas"]["StayOut"];
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
    check_out_api_v1_stays__stay_id__checkout_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                stay_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CheckoutRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CheckoutOut"];
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
    checkout_summary_api_v1_stays__stay_id__checkout_summary_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                stay_id: string;
            };
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
                    "application/json": components["schemas"]["CheckoutSummary"];
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
    stay_invoices_api_v1_stays__stay_id__invoices_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                stay_id: string;
            };
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
                    "application/json": components["schemas"]["InvoiceList"];
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
    move_stay_api_v1_stays__stay_id__move_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                stay_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["StayMove"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StayOut"];
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
    unblock_charges_api_v1_stays__stay_id__unblock_charges_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                stay_id: string;
            };
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
                    "application/json": components["schemas"]["StayOut"];
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
    get_subscription_api_v1_subscription_get: {
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
                    "application/json": components["schemas"]["HotelSubscription"];
                };
            };
        };
    };
    change_request_api_v1_subscription_change_request_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ChangeRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ChangeRequestOut"];
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
    hotel_grants_api_v1_support_access_get: {
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
                    "application/json": components["schemas"]["SupportGrantList"];
                };
            };
        };
    };
    revoke_grant_api_v1_support_access__grant_id__revoke_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                grant_id: string;
            };
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
                    "application/json": components["schemas"]["SupportGrantOut"];
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
    list_webhooks_api_v1_webhooks_get: {
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
                    "application/json": components["schemas"]["WebhookList"];
                };
            };
        };
    };
    create_webhook_api_v1_webhooks_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["WebhookCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WebhookCreated"];
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
    webhook_deliveries_api_v1_webhooks__webhook_id__deliveries_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                webhook_id: string;
            };
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
                    "application/json": components["schemas"]["app__schemas__reports__DeliveryList"];
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
    webhook_status_api_v1_webhooks__webhook_id__status_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                webhook_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["WebhookStatusChange"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WebhookOut"];
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
    test_webhook_api_v1_webhooks__webhook_id__test_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                webhook_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["WebhookTestOut"];
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
