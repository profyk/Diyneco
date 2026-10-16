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
    "/api/v1/admin/billing-settings": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Billing Settings */
        get: operations["get_billing_settings_api_v1_admin_billing_settings_get"];
        /** Put Billing Settings */
        put: operations["put_billing_settings_api_v1_admin_billing_settings_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/billing/invoices": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Billing Invoices
         * @description Invoices and credit notes across hotels; `format=csv` exports up to 5,000 rows.
         */
        get: operations["billing_invoices_api_v1_admin_billing_invoices_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/billing/payments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Billing Payments
         * @description Payments across hotels for reconciliation; `format=csv` exports up to 5,000 rows.
         */
        get: operations["billing_payments_api_v1_admin_billing_payments_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/billing/provider": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Billing Provider
         * @description Which payment provider is selected and whether it is ready here; never a secret.
         */
        get: operations["billing_provider_api_v1_admin_billing_provider_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/billing/summary": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Billing Summary */
        get: operations["billing_summary_api_v1_admin_billing_summary_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/billing/webhooks": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Billing Webhooks */
        get: operations["billing_webhooks_api_v1_admin_billing_webhooks_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/company": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Company */
        get: operations["get_company_api_v1_admin_company_get"];
        /**
         * Put Company
         * @description Replaces the editable settings. `version` must match (else 412); `reason` is audited.
         */
        put: operations["put_company_api_v1_admin_company_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/company/logo": {
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
         * @description Returns a signed URL; PUT the PNG or JPEG there within its lifetime.
         */
        post: operations["start_logo_upload_api_v1_admin_company_logo_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/countries": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Countries
         * @description Every country Diyneco knows, whether it takes signups, and how many hotels it has.
         */
        get: operations["list_countries_api_v1_admin_countries_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/countries/{code}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /**
         * Put Country
         * @description Switches signups on or off for a country. Existing hotels are never affected.
         */
        put: operations["put_country_api_v1_admin_countries__code__put"];
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
    "/api/v1/admin/hotels/{hotel_id}/invoices": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Admin List */
        get: operations["admin_list_api_v1_admin_hotels__hotel_id__invoices_get"];
        put?: never;
        /**
         * Draft
         * @description A manual invoice for an approved charge, as a draft; the server works out tax and totals.
         */
        post: operations["draft_api_v1_admin_hotels__hotel_id__invoices_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/hotels/{hotel_id}/invoices/{invoice_id}/credit": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Credit
         * @description Issues a credit note for all or part of an issued invoice.
         */
        post: operations["credit_api_v1_admin_hotels__hotel_id__invoices__invoice_id__credit_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/hotels/{hotel_id}/invoices/{invoice_id}/issue": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Issue
         * @description Numbers, freezes, renders and emails the invoice.
         */
        post: operations["issue_api_v1_admin_hotels__hotel_id__invoices__invoice_id__issue_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/hotels/{hotel_id}/invoices/{invoice_id}/pdf": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Admin Pdf */
        get: operations["admin_pdf_api_v1_admin_hotels__hotel_id__invoices__invoice_id__pdf_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/hotels/{hotel_id}/invoices/{invoice_id}/send": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Resend */
        post: operations["resend_api_v1_admin_hotels__hotel_id__invoices__invoice_id__send_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/hotels/{hotel_id}/invoices/{invoice_id}/void": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Void */
        post: operations["void_api_v1_admin_hotels__hotel_id__invoices__invoice_id__void_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/hotels/{hotel_id}/payments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Hotel Payments */
        get: operations["hotel_payments_api_v1_admin_hotels__hotel_id__payments_get"];
        put?: never;
        /**
         * Record Payment
         * @description Records a verified offline payment (EFT) with its bank reference.
         */
        post: operations["record_payment_api_v1_admin_hotels__hotel_id__payments_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/hotels/{hotel_id}/payments/{payment_id}/reconcile": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reconcile Payment */
        post: operations["reconcile_payment_api_v1_admin_hotels__hotel_id__payments__payment_id__reconcile_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/hotels/{hotel_id}/payments/{payment_id}/refund": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Refund Payment
         * @description Refunds part or all of a payment, with a credit note for the same amount.
         */
        post: operations["refund_payment_api_v1_admin_hotels__hotel_id__payments__payment_id__refund_post"];
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
    "/api/v1/admin/hotels/{hotel_id}/trial": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Grant Trial
         * @description Grants a free trial to a hotel without a subscription (an owner's further property,
         *     D86), or sets when a running trial ends. Audited with the reason.
         */
        post: operations["grant_trial_api_v1_admin_hotels__hotel_id__trial_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/insights": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Insights
         * @description Adoption, activation funnel, trial conversion, churn, cohorts, breakdowns by country,
         *     region and property type, and staff activity (D87). Default period: the last 30 days.
         */
        get: operations["insights_api_v1_admin_insights_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/legal-documents": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Admin List */
        get: operations["admin_list_api_v1_admin_legal_documents_get"];
        put?: never;
        /** Create Draft */
        post: operations["create_draft_api_v1_admin_legal_documents_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/legal-documents/{document_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Draft */
        delete: operations["delete_draft_api_v1_admin_legal_documents__document_id__delete"];
        options?: never;
        head?: never;
        /** Update Draft */
        patch: operations["update_draft_api_v1_admin_legal_documents__document_id__patch"];
        trace?: never;
    };
    "/api/v1/admin/legal-documents/{document_id}/publish": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Publish */
        post: operations["publish_api_v1_admin_legal_documents__document_id__publish_post"];
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
    "/api/v1/admin/owners": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Owners
         * @description Every Hotel Owner with their properties, rooms, MRR and money processed (D87).
         */
        get: operations["owners_api_v1_admin_owners_get"];
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
        /**
         * Create Plan
         * @description A new plan starts as a draft; price it, preview it, then publish it.
         */
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
        /**
         * Update Plan
         * @description Details, limits and features. `version` must match (else 412); a published plan needs a
         *     `reason`. Prices change through /prices.
         */
        patch: operations["update_plan_api_v1_admin_plans__plan_id__patch"];
        trace?: never;
    };
    "/api/v1/admin/plans/{plan_id}/archive": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Archive Plan
         * @description Takes the plan off sale; hotels already on it keep it.
         */
        post: operations["archive_plan_api_v1_admin_plans__plan_id__archive_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/plans/{plan_id}/preview": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Preview Plan */
        get: operations["preview_plan_api_v1_admin_plans__plan_id__preview_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/plans/{plan_id}/prices": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Add Price */
        post: operations["add_price_api_v1_admin_plans__plan_id__prices_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/plans/{plan_id}/prices/{price_id}": {
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
         * Withdraw Price
         * @description Withdraws a scheduled price that is not yet in force.
         */
        delete: operations["withdraw_price_api_v1_admin_plans__plan_id__prices__price_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/plans/{plan_id}/publish": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Publish Plan
         * @description Puts the plan on sale. Needs a price in force; confirmed with step-up.
         */
        post: operations["publish_plan_api_v1_admin_plans__plan_id__publish_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/plans/{plan_id}/restore": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Restore Plan
         * @description Brings an archived plan back as a draft.
         */
        post: operations["restore_plan_api_v1_admin_plans__plan_id__restore_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/site/analytics": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Analytics */
        get: operations["analytics_api_v1_admin_site_analytics_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/site/entries": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Entries */
        get: operations["list_entries_api_v1_admin_site_entries_get"];
        put?: never;
        /** Create Entry */
        post: operations["create_entry_api_v1_admin_site_entries_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/site/entries/{entry_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Entry */
        get: operations["get_entry_api_v1_admin_site_entries__entry_id__get"];
        put?: never;
        post?: never;
        /** Delete Entry */
        delete: operations["delete_entry_api_v1_admin_site_entries__entry_id__delete"];
        options?: never;
        head?: never;
        /** Update Entry */
        patch: operations["update_entry_api_v1_admin_site_entries__entry_id__patch"];
        trace?: never;
    };
    "/api/v1/admin/site/entries/{entry_id}/preview": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Preview Link */
        post: operations["preview_link_api_v1_admin_site_entries__entry_id__preview_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/site/entries/{entry_id}/publish": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Publish Entry */
        post: operations["publish_entry_api_v1_admin_site_entries__entry_id__publish_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/site/entries/{entry_id}/unpublish": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Unpublish Entry */
        post: operations["unpublish_entry_api_v1_admin_site_entries__entry_id__unpublish_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/site/entries/{entry_id}/versions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Versions */
        get: operations["versions_api_v1_admin_site_entries__entry_id__versions_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/site/entries/{entry_id}/versions/{version}/restore": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Restore Version
         * @description Copies a published version back into the draft; publish to make it live again.
         */
        post: operations["restore_version_api_v1_admin_site_entries__entry_id__versions__version__restore_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/site/leads": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Leads */
        get: operations["list_leads_api_v1_admin_site_leads_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/site/leads/{lead_id}": {
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
         * Erase Lead
         * @description Erases a lead on the person's request (POPIA); the audit keeps only that it happened.
         */
        delete: operations["erase_lead_api_v1_admin_site_leads__lead_id__delete"];
        options?: never;
        head?: never;
        /** Update Lead */
        patch: operations["update_lead_api_v1_admin_site_leads__lead_id__patch"];
        trace?: never;
    };
    "/api/v1/admin/site/media": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Media */
        get: operations["list_media_api_v1_admin_site_media_get"];
        put?: never;
        /**
         * Upload Media
         * @description JPEG, PNG or WebP up to 6 MB; re-encoded as WebP in several widths, metadata dropped.
         */
        post: operations["upload_media_api_v1_admin_site_media_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/site/media/{media_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Media */
        delete: operations["delete_media_api_v1_admin_site_media__media_id__delete"];
        options?: never;
        head?: never;
        /** Update Media */
        patch: operations["update_media_api_v1_admin_site_media__media_id__patch"];
        trace?: never;
    };
    "/api/v1/admin/site/redirects": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Redirects */
        get: operations["list_redirects_api_v1_admin_site_redirects_get"];
        put?: never;
        /** Create Redirect */
        post: operations["create_redirect_api_v1_admin_site_redirects_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/site/redirects/{redirect_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Redirect */
        delete: operations["delete_redirect_api_v1_admin_site_redirects__redirect_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/site/settings": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Settings */
        get: operations["get_settings_api_v1_admin_site_settings_get"];
        /** Put Settings */
        put: operations["put_settings_api_v1_admin_site_settings_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/staff": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Staff */
        get: operations["list_staff_api_v1_admin_staff_get"];
        put?: never;
        /** Invite */
        post: operations["invite_api_v1_admin_staff_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/staff/roles": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Roles */
        get: operations["list_roles_api_v1_admin_staff_roles_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/staff/{user_id}/deactivate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Deactivate */
        post: operations["deactivate_api_v1_admin_staff__user_id__deactivate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/staff/{user_id}/reactivate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Reactivate */
        post: operations["reactivate_api_v1_admin_staff__user_id__reactivate_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/staff/{user_id}/resend-invitation": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Resend Invitation */
        post: operations["resend_invitation_api_v1_admin_staff__user_id__resend_invitation_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/staff/{user_id}/roles": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        /** Change Roles */
        put: operations["change_roles_api_v1_admin_staff__user_id__roles_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/tax-rates": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** List Tax Rates */
        get: operations["list_tax_rates_api_v1_admin_tax_rates_get"];
        put?: never;
        /** Schedule Tax Rate */
        post: operations["schedule_tax_rate_api_v1_admin_tax_rates_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/admin/tax-rates/{rate_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Withdraw Tax Rate */
        delete: operations["withdraw_tax_rate_api_v1_admin_tax_rates__rate_id__delete"];
        options?: never;
        head?: never;
        patch?: never;
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
    "/api/v1/auth/email/resend": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Resend Email Code
         * @description Sends a new code to an unconfirmed address (at most once a minute); same answer for any address.
         */
        post: operations["resend_email_code_api_v1_auth_email_resend_post"];
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
    "/api/v1/auth/email/verify-code": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Verify Email Code
         * @description Confirms the address with the 6-digit code from the sign-up email (D84).
         */
        post: operations["verify_email_code_api_v1_auth_email_verify_code_post"];
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
    "/api/v1/auth/platform-invitations/accept": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Accept Invitation */
        post: operations["accept_invitation_api_v1_auth_platform_invitations_accept_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/auth/platform/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Platform Login
         * @description Sign-in for the Diyneco admin panel: Diyneco staff accounts only (D75). Hotel accounts
         *     sign in through /auth/login, which in turn refuses Diyneco staff accounts.
         */
        post: operations["platform_login_api_v1_auth_platform_login_post"];
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
    "/api/v1/auth/staff-code/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Staff Code Login
         * @description Room-service sign-in with the Hotel ID, an 8-digit staff code and the member's PIN
         *     (D82). Accounts that must use two-step sign-in are sent to /auth/login.
         */
        post: operations["staff_code_login_api_v1_auth_staff_code_login_post"];
        delete?: never;
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
    "/api/v1/billing/webhooks/stitch": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Stitch Webhook
         * @description Stitch payment events, signed with Svix. A repeated event is acknowledged and not
         *     processed again; the payment's status is always fetched from Stitch.
         */
        post: operations["stitch_webhook_api_v1_billing_webhooks_stitch_post"];
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
    "/api/v1/countries": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Countries
         * @description Countries where new hotels can sign up, with the defaults each suggests (public: the
         *     signup form needs it). The platform chooses them (operational countries, D84).
         */
        get: operations["countries_api_v1_countries_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/countries/{code}/regions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Country Regions
         * @description A country's provinces, states or other first-level regions (ISO 3166-2, D85). Public:
         *     the signup form and hotel settings use it. An empty list means the region is free text.
         */
        get: operations["country_regions_api_v1_countries__code__regions_get"];
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
         * @description Redeems a setup code with the Hotel ID and the issuing manager's PIN (D82). The
         *     credential is in this response only; a replay of the same request returns
         *     `device_credential: null` (DECISIONS D23).
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
    "/api/v1/guest/feedback": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * My Feedback
         * @description What this stay has rated already (D98), so the tablet only asks once.
         */
        get: operations["my_feedback_api_v1_guest_feedback_get"];
        put?: never;
        /** Give Feedback */
        post: operations["give_feedback_api_v1_guest_feedback_post"];
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
    "/api/v1/guest/legal": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Guest Documents
         * @description Guest terms and privacy notice for the tablet's hotel country.
         */
        get: operations["guest_documents_api_v1_guest_legal_get"];
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
    "/api/v1/guest/requests": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * My Requests
         * @description This stay's service requests (D93); empty before check-in.
         */
        get: operations["my_requests_api_v1_guest_requests_get"];
        put?: never;
        /** Ask */
        post: operations["ask_api_v1_guest_requests_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/guest/requests/{request_id}/cancel": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Cancel Request */
        post: operations["cancel_request_api_v1_guest_requests__request_id__cancel_post"];
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
    "/api/v1/hotels": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Add Property
         * @description A Hotel Owner adds another property with the signup form's hotel details. It starts
         *     with no subscription (the free trial is once per owner); switch to it with
         *     POST /auth/refresh {hotel_id}.
         */
        post: operations["add_property_api_v1_hotels_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
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
    "/api/v1/kitchen/menu": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Kitchen Menu
         * @description Dishes of this display's stations, so a cook can mark one sold out (D67).
         */
        get: operations["kitchen_menu_api_v1_kitchen_menu_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/kitchen/menu-items/{item_id}/availability": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Kitchen Sold Out
         * @description Sold out or back in stock; tablets stop offering the dish at once.
         */
        post: operations["kitchen_sold_out_api_v1_kitchen_menu_items__item_id__availability_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
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
    "/api/v1/legal/accept": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Accept */
        post: operations["accept_api_v1_legal_accept_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/legal/documents": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Documents
         * @description Current published version of each document for a country (public: signup shows them).
         */
        get: operations["documents_api_v1_legal_documents_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/legal/documents/{document_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Document */
        get: operations["document_api_v1_legal_documents__document_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/legal/pending": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Pending
         * @description Current merchant documents the caller has not accepted yet for this hotel.
         */
        get: operations["pending_api_v1_legal_pending_get"];
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
    "/api/v1/menu/categories/{category_id}/station": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Route Category
         * @description Prepares the category's dishes, current and new, at one kitchen station.
         */
        post: operations["route_category_api_v1_menu_categories__category_id__station_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
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
    "/api/v1/menu/modifier-groups/{group_id}": {
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
         * Delete Group
         * @description Removes the group and takes it off every item; past orders keep their choices.
         */
        delete: operations["delete_group_api_v1_menu_modifier_groups__group_id__delete"];
        options?: never;
        head?: never;
        /** Patch Group */
        patch: operations["patch_group_api_v1_menu_modifier_groups__group_id__patch"];
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
    "/api/v1/menu/modifier-options/{option_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        /** Delete Option */
        delete: operations["delete_option_api_v1_menu_modifier_options__option_id__delete"];
        options?: never;
        head?: never;
        /**
         * Patch Option
         * @description Rename, reprice (menu.price.update) or mark a choice sold out; returns its whole group.
         */
        patch: operations["patch_option_api_v1_menu_modifier_options__option_id__patch"];
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
    "/api/v1/menu/standard-layout": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Standard Layout
         * @description Adds the usual sections, categories and kitchen stations that are missing (D68).
         */
        post: operations["standard_layout_api_v1_menu_standard_layout_post"];
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
    "/api/v1/orders/{order_id}/items/{item_id}/void": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Void Item
         * @description Cancels one line of an order with a reason; its bill charge is reversed (D67).
         */
        post: operations["void_item_api_v1_orders__order_id__items__item_id__void_post"];
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
    "/api/v1/plans": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Public Plans
         * @description Published plans with their prices in force (public: the pricing page and signup).
         */
        get: operations["public_plans_api_v1_plans_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/portfolio": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Portfolio
         * @description Every property the caller owns side by side: occupancy, stays, open orders and revenue
         *     today and this month, with totals per currency.
         */
        get: operations["portfolio_api_v1_portfolio_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/portfolio/billing": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Group Statement
         * @description Every open invoice across the caller's properties and what is due per currency (D89).
         */
        get: operations["group_statement_api_v1_portfolio_billing_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/portfolio/invitations": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Invite To Properties
         * @description Invites one person to several of the caller's properties at once, with a role at each
         *     (D90). Each property gets its own invitation, checked and audited as usual.
         */
        post: operations["invite_to_properties_api_v1_portfolio_invitations_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/portfolio/payments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Pay All
         * @description One checkout for the balance of every open invoice in a currency across the caller's
         *     properties. Each property keeps its own invoice and receives its own share.
         */
        post: operations["pay_all_api_v1_portfolio_payments_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/portfolio/payments/{group_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Check Group Payment
         * @description The group payment as the provider reports it now (asked on the server).
         */
        get: operations["check_group_payment_api_v1_portfolio_payments__group_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/portfolio/payments/{group_id}/sandbox": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Group Sandbox
         * @description Test mode only (never in production): finishes a sandbox group checkout; no money moves.
         */
        post: operations["group_sandbox_api_v1_portfolio_payments__group_id__sandbox_post"];
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
    "/api/v1/reports/feedback": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Guest Feedback
         * @description Guest ratings (D98): average, stars, by subject and the latest comments.
         */
        get: operations["guest_feedback_api_v1_reports_feedback_get"];
        put?: never;
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
    "/api/v1/reports/requests": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Service Requests
         * @description Guest service requests (D93): by kind and by the person who finished them.
         */
        get: operations["service_requests_api_v1_reports_requests_get"];
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
    "/api/v1/requests": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * List Requests
         * @description `open`: waiting or under way, oldest first. `mine`: those assigned to me. `recent`: the
         *     last 7 days, newest first.
         */
        get: operations["list_requests_api_v1_requests_get"];
        put?: never;
        /**
         * Log Request
         * @description A request taken by phone or at the desk, for any room (with or without a guest).
         */
        post: operations["log_request_api_v1_requests_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/requests/{request_id}/acknowledge": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Acknowledge */
        post: operations["acknowledge_api_v1_requests__request_id__acknowledge_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/requests/{request_id}/assign": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Assign */
        post: operations["assign_api_v1_requests__request_id__assign_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/requests/{request_id}/cancel": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Cancel */
        post: operations["cancel_api_v1_requests__request_id__cancel_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/requests/{request_id}/done": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Done */
        post: operations["done_api_v1_requests__request_id__done_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/requests/{request_id}/start": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Start */
        post: operations["start_api_v1_requests__request_id__start_post"];
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
    "/api/v1/site/entry": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Public Entry
         * @description A published page or post; the home page is the page with an empty slug.
         */
        get: operations["public_entry_api_v1_site_entry_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/site/leads": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Create Lead
         * @description A demo request or contact message. Spam is accepted silently and dropped.
         */
        post: operations["create_lead_api_v1_site_leads_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/site/media/{media_id}/{width}.webp": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Media */
        get: operations["media_api_v1_site_media__media_id___width__webp_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/site/posts": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Public Posts */
        get: operations["public_posts_api_v1_site_posts_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/site/preview": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Preview Entry
         * @description The draft behind a 15-minute preview link made in the admin panel.
         */
        get: operations["preview_entry_api_v1_site_preview_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/site/redirects": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Public Redirects
         * @description Old addresses and where they now live, for the website to answer with 301 or 302.
         */
        get: operations["public_redirects_api_v1_site_redirects_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/site/settings": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Public Settings */
        get: operations["public_settings_api_v1_site_settings_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/site/sitemap": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Sitemap */
        get: operations["sitemap_api_v1_site_sitemap_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/site/views": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Record View
         * @description A cookieless page view; nothing that identifies the visitor is stored.
         */
        post: operations["record_view_api_v1_site_views_post"];
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
    "/api/v1/staff/{user_id}/staff-code": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Issue Staff Code
         * @description A new 8-digit staff code for room-service sign-in (D82), shown once. Replaces any
         *     earlier code.
         */
        post: operations["issue_staff_code_api_v1_staff__user_id__staff_code_post"];
        /** Remove Staff Code */
        delete: operations["remove_staff_code_api_v1_staff__user_id__staff_code_delete"];
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
    "/api/v1/subscription/billing-contact": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Get Billing Contact */
        get: operations["get_billing_contact_api_v1_subscription_billing_contact_get"];
        /**
         * Put Billing Contact
         * @description Who Diyneco bills; `version` must match (0 the first time).
         */
        put: operations["put_billing_contact_api_v1_subscription_billing_contact_put"];
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/subscription/cancel": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Cancel Subscription
         * @description A trial ends at once; a paid subscription ends at the end of its current period.
         */
        post: operations["cancel_subscription_api_v1_subscription_cancel_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/subscription/change": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Change Plan
         * @description Upgrades apply at once with a prorated invoice when proration is on; other changes
         *     wait for the next renewal. Choosing the current plan withdraws a scheduled change.
         */
        post: operations["change_plan_api_v1_subscription_change_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/subscription/invoices": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** My Invoices */
        get: operations["my_invoices_api_v1_subscription_invoices_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/subscription/invoices/{invoice_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** My Invoice */
        get: operations["my_invoice_api_v1_subscription_invoices__invoice_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/subscription/invoices/{invoice_id}/pay": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Pay Invoice
         * @description Opens a checkout for the invoice's balance with the configured provider; send the
         *     browser to `checkout_url`. Nothing is paid until the provider confirms it.
         */
        post: operations["pay_invoice_api_v1_subscription_invoices__invoice_id__pay_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/subscription/invoices/{invoice_id}/pdf": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * My Invoice Pdf
         * @description A signed address valid for 5 minutes; invoices are never at a public address.
         */
        get: operations["my_invoice_pdf_api_v1_subscription_invoices__invoice_id__pdf_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/subscription/payment-attempts": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** My Attempts */
        get: operations["my_attempts_api_v1_subscription_payment_attempts_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/subscription/payment-attempts/{attempt_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /**
         * Check Attempt
         * @description The attempt's status as the provider reports it now (asked on the server).
         */
        get: operations["check_attempt_api_v1_subscription_payment_attempts__attempt_id__get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/subscription/payment-attempts/{attempt_id}/sandbox": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Sandbox Outcome
         * @description Test mode only (never in production): finishes a sandbox checkout. No money moves and
         *     the payment is recorded as a test payment.
         */
        post: operations["sandbox_outcome_api_v1_subscription_payment_attempts__attempt_id__sandbox_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/subscription/payment-options": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** Payment Options */
        get: operations["payment_options_api_v1_subscription_payment_options_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/subscription/payments": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** My Payments */
        get: operations["my_payments_api_v1_subscription_payments_get"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/subscription/quote": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Subscription Quote
         * @description What the hotel would pay for a published plan today, computed on the server (D76).
         */
        post: operations["subscription_quote_api_v1_subscription_quote_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/subscription/resume": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** Resume Subscription */
        post: operations["resume_subscription_api_v1_subscription_resume_post"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/api/v1/subscription/subscribe": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /**
         * Subscribe
         * @description Subscribes to a published plan at the price the server computes, and issues the first
         *     invoice; the subscription is pending payment until that invoice is paid.
         */
        post: operations["subscribe_api_v1_subscription_subscribe_post"];
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
        /** AddPropertyOut */
        AddPropertyOut: {
            /** Code */
            code: string;
            /**
             * Hotel Id
             * Format: uuid
             */
            hotel_id: string;
            /** Name */
            name: string;
            /** Status */
            status: string;
            /** Subscription Status */
            subscription_status: string | null;
        };
        /** AddPropertyRequest */
        AddPropertyRequest: {
            /** Accepted Documents */
            accepted_documents?: string[];
            hotel: components["schemas"]["SignupHotel"];
        };
        /** Address */
        "Address-Output": {
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
        /** AdminCountryList */
        AdminCountryList: {
            /** Data */
            data: components["schemas"]["AdminCountryOut"][];
        };
        /** AdminCountryOut */
        AdminCountryOut: {
            /** Active Hotels */
            active_hotels: number;
            /** Code */
            code: string;
            /** Currency */
            currency: string;
            /** Dial */
            dial: string;
            /** Enabled At */
            enabled_at: string | null;
            /** Hotels */
            hotels: number;
            /** Locale */
            locale: string;
            /** Name */
            name: string;
            /** Operational */
            operational: boolean;
            /** Region */
            region: string;
            /** Tax Id Label */
            tax_id_label: string;
            /** Tax Id Pattern */
            tax_id_pattern: string | null;
            /** Tax Label */
            tax_label: string;
            /** Tax Rate Bp */
            tax_rate_bp: number | null;
            /** Timezone */
            timezone: string;
            /** Timezones */
            timezones: string[];
        };
        /** AdminHotel */
        AdminHotel: {
            /**
             * Activated
             * @default false
             */
            activated: boolean;
            /** City */
            city?: string | null;
            /** Code */
            code: string;
            /** Country */
            country?: string | null;
            counts: components["schemas"]["HotelCounts"];
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            gmv_30d?: components["schemas"]["SignedMoney"] | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Last Activity */
            last_activity: string | null;
            mrr?: components["schemas"]["SignedMoney"] | null;
            /** Name */
            name: string;
            /**
             * Orders 30D
             * @default 0
             */
            orders_30d: number;
            /** Plan */
            plan: string | null;
            /** Plan Name */
            plan_name?: string | null;
            /** Property Type */
            property_type?: string | null;
            /** Province */
            province?: string | null;
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
        /** AdminInvoiceList */
        AdminInvoiceList: {
            /** Data */
            data: components["schemas"]["AdminInvoiceRow"][];
            /** Total */
            total: number;
        };
        /** AdminInvoiceRow */
        AdminInvoiceRow: {
            balance: components["schemas"]["SignedMoney"];
            credited: components["schemas"]["SignedMoney"];
            /** Currency */
            currency: string;
            /** Due On */
            due_on: string | null;
            /**
             * Hotel Id
             * Format: uuid
             */
            hotel_id: string;
            /** Hotel Name */
            hotel_name: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Is Tax Invoice */
            is_tax_invoice: boolean;
            /** Issued At */
            issued_at: string | null;
            /** Kind */
            kind: string;
            /** Number */
            number: string | null;
            paid: components["schemas"]["SignedMoney"];
            /** Period End */
            period_end: string | null;
            /** Period Start */
            period_start: string | null;
            /** Plan Code */
            plan_code: string | null;
            /** Purpose */
            purpose: string;
            /** Status */
            status: string;
            tax: components["schemas"]["SignedMoney"];
            total: components["schemas"]["SignedMoney"];
        };
        /** AdminPaymentList */
        AdminPaymentList: {
            /** Data */
            data: components["schemas"]["AdminPaymentRow"][];
            /** Total */
            total: number;
        };
        /** AdminPaymentRow */
        AdminPaymentRow: {
            amount: components["schemas"]["SignedMoney"];
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Hotel Id
             * Format: uuid
             */
            hotel_id: string;
            /** Hotel Name */
            hotel_name: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Invoice Id
             * Format: uuid
             */
            invoice_id: string;
            /** Invoice Number */
            invoice_number: string | null;
            /** Method */
            method: string;
            /** Provider */
            provider: string;
            /** Provider Payment Id */
            provider_payment_id: string | null;
            /**
             * Received On
             * Format: date
             */
            received_on: string;
            /** Reconciled At */
            reconciled_at: string | null;
            /** Reconciliation Note */
            reconciliation_note: string | null;
            /** Reconciliation Status */
            reconciliation_status: string;
            /** Reference */
            reference: string | null;
            refunded: components["schemas"]["SignedMoney"];
            /** Test Mode */
            test_mode: boolean;
        };
        /** Alternate */
        Alternate: {
            /** Locale */
            locale: string;
            /** Path */
            path: string;
        };
        /**
         * Analytics
         * @description `builtin`: Diyneco's own cookieless counts. `plausible`: a Plausible-compatible script
         *     (also cookieless). `none`: nothing is counted.
         */
        "Analytics-Input": {
            /** Plausible Domain */
            plausible_domain?: string | null;
            /** Plausible Script */
            plausible_script?: string | null;
            /**
             * Provider
             * @default builtin
             * @enum {string}
             */
            provider: "builtin" | "plausible" | "none";
        };
        /** Analytics */
        "Analytics-Output": {
            /** Days */
            days: components["schemas"]["app__schemas__reports__AnalyticsDay"][];
        };
        /** AnalyticsOut */
        AnalyticsOut: {
            /** Days */
            days: components["schemas"]["app__schemas__site__AnalyticsDay"][];
            /** Leads */
            leads: number;
            /** Locales */
            locales: components["schemas"]["AnalyticsRow"][];
            /** Pages */
            pages: components["schemas"]["AnalyticsRow"][];
            /** Referrers */
            referrers: components["schemas"]["AnalyticsRow"][];
            /**
             * Since
             * Format: date
             */
            since: string;
            /**
             * Until
             * Format: date
             */
            until: string;
            /** Views */
            views: number;
            /** Visitors */
            visitors: number;
        };
        /** AnalyticsRow */
        AnalyticsRow: {
            /** Key */
            key: string;
            /** Views */
            views: number;
            /** Visitors */
            visitors: number;
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
        /** AssignRequestTo */
        AssignRequestTo: {
            /**
             * User Id
             * Format: uuid
             */
            user_id: string;
        };
        /** AttemptList */
        AttemptList: {
            /** Data */
            data: components["schemas"]["AttemptOut"][];
        };
        /** AttemptOut */
        AttemptOut: {
            amount: components["schemas"]["SignedMoney"];
            /** Completed At */
            completed_at: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Failure Reason */
            failure_reason: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Invoice Id
             * Format: uuid
             */
            invoice_id: string;
            /** Provider */
            provider: string;
            /** Provider Label */
            provider_label: string;
            /**
             * Status
             * @enum {string}
             */
            status: "pending" | "succeeded" | "failed" | "cancelled" | "expired";
            /** Test Mode */
            test_mode: boolean;
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
        /** BankDetails */
        BankDetails: {
            /** Account Holder */
            account_holder?: string | null;
            /** Account Number */
            account_number?: string | null;
            /** Account Type */
            account_type?: ("cheque" | "current" | "savings" | "business") | null;
            /** Bank Name */
            bank_name?: string | null;
            /** Branch Code */
            branch_code?: string | null;
            /** Swift Code */
            swift_code?: string | null;
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
        /** BillingContactOut */
        BillingContactOut: {
            /** Address */
            address: {
                [key: string]: unknown;
            };
            /** Billing Email */
            billing_email: string | null;
            /** Contact Name */
            contact_name: string | null;
            /** Legal Name */
            legal_name: string | null;
            /** Phone */
            phone: string | null;
            /** Vat Number */
            vat_number: string | null;
            /** Version */
            version: number;
        };
        /** BillingContactPut */
        BillingContactPut: {
            address?: components["schemas"]["ContactAddress"];
            /** Billing Email */
            billing_email?: string | null;
            /** Contact Name */
            contact_name?: string | null;
            /** Legal Name */
            legal_name?: string | null;
            /** Phone */
            phone?: string | null;
            /** Vat Number */
            vat_number?: string | null;
            /** Version */
            version: number;
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
        /** BillingSettingsOut */
        BillingSettingsOut: {
            /**
             * Card Provider
             * @enum {string}
             */
            card_provider: "none" | "sandbox" | "stitch";
            /** Eft Enabled */
            eft_enabled: boolean;
            /** Grace Days */
            grace_days: number;
            /** Group Discount Bp */
            group_discount_bp: number;
            /** Group Discount Min Properties */
            group_discount_min_properties: number;
            /** Price Change Notice Days */
            price_change_notice_days: number;
            /** Proration Enabled */
            proration_enabled: boolean;
            /** Read Only When Suspended */
            read_only_when_suspended: boolean;
            /** Reminder Offsets */
            reminder_offsets: number[];
            /** Renewal Lead Days */
            renewal_lead_days: number;
            /** Suspend After Grace */
            suspend_after_grace: boolean;
            /** Trial Days */
            trial_days: number;
            /** Trial Limits */
            trial_limits: {
                [key: string]: number;
            };
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** Version */
            version: number;
        };
        /** BillingSettingsPut */
        BillingSettingsPut: {
            /** Card Provider */
            card_provider?: ("none" | "sandbox" | "stitch") | null;
            /** Eft Enabled */
            eft_enabled?: boolean | null;
            /** Grace Days */
            grace_days?: number | null;
            /** Group Discount Bp */
            group_discount_bp?: number | null;
            /** Group Discount Min Properties */
            group_discount_min_properties?: number | null;
            /** Price Change Notice Days */
            price_change_notice_days: number;
            /** Proration Enabled */
            proration_enabled?: boolean | null;
            /** Read Only When Suspended */
            read_only_when_suspended?: boolean | null;
            /** Reason */
            reason: string;
            /** Reminder Offsets */
            reminder_offsets?: number[] | null;
            /** Renewal Lead Days */
            renewal_lead_days?: number | null;
            /** Suspend After Grace */
            suspend_after_grace?: boolean | null;
            /** Trial Days */
            trial_days: number;
            /** Trial Limits */
            trial_limits: {
                [key: string]: number;
            };
            /** Version */
            version: number;
        };
        /** BillingSummary */
        BillingSummary: {
            /** Active Subscriptions */
            active_subscriptions: number;
            /** By Plan */
            by_plan: components["schemas"]["PlanRevenue"][];
            /** Cancelled Subscriptions */
            cancelled_subscriptions: number;
            /** Currencies */
            currencies: components["schemas"]["SummaryCurrency"][];
            /** Failed Payments */
            failed_payments: number;
            /**
             * From
             * Format: date
             */
            from: string;
            /** New Subscriptions */
            new_subscriptions: number;
            /** Past Due */
            past_due: number;
            /** Suspended */
            suspended: number;
            /**
             * To
             * Format: date
             */
            to: string;
            /** Trials */
            trials: number;
        };
        /** Breakdown */
        Breakdown: {
            /** Activated */
            activated: number;
            /** Active */
            active: number;
            /** Gmv 30D */
            gmv_30d: components["schemas"]["SignedMoney"][];
            /** Hotels */
            hotels: number;
            /** Key */
            key: string;
            /** Label */
            label: string;
            /** Mrr */
            mrr: components["schemas"]["SignedMoney"][];
            /** Orders 30D */
            orders_30d: number;
            /** Paying */
            paying: number;
            /** Rooms */
            rooms: number;
            /** Trials */
            trials: number;
        };
        /** BulkResult */
        BulkResult: {
            /** Created */
            created: number;
            /** Data */
            data: components["schemas"]["RoomOut"][];
        };
        /** CallToAction */
        CallToAction: {
            /** Body */
            body?: string | null;
            /** Heading */
            heading: string;
            primary: components["schemas"]["Cta"];
            secondary?: components["schemas"]["Cta"] | null;
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "cta";
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
            /** Default Station Id */
            default_station_id?: string | null;
            /** Name */
            name: string;
            /** Schedule Id */
            schedule_id?: string | null;
            /**
             * Section
             * @default food
             * @enum {string}
             */
            section: "food" | "drinks";
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
            /** Default Station Id */
            default_station_id: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
            /** Schedule Id */
            schedule_id: string | null;
            /**
             * Section
             * @enum {string}
             */
            section: "food" | "drinks";
            /** Sort Order */
            sort_order: number;
        };
        /** CategoryPatch */
        CategoryPatch: {
            /** Default Station Id */
            default_station_id?: string | null;
            /** Name */
            name?: string | null;
            /** Schedule Id */
            schedule_id?: string | null;
            /** Section */
            section?: ("food" | "drinks") | null;
            /** Sort Order */
            sort_order?: number | null;
        };
        /** CategoryRoute */
        CategoryRoute: {
            /**
             * Station Id
             * Format: uuid
             */
            station_id: string;
        };
        /** CategoryRouted */
        CategoryRouted: {
            /** Default Station Id */
            default_station_id: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Moved Items */
            moved_items: number;
            /** Name */
            name: string;
            /** Schedule Id */
            schedule_id: string | null;
            /**
             * Section
             * @enum {string}
             */
            section: "food" | "drinks";
            /** Sort Order */
            sort_order: number;
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
            recipient_address?: components["schemas"]["app__schemas__hotel__Address"] | null;
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
        /** Cohort */
        Cohort: {
            /** Activated */
            activated: number;
            /** Closed */
            closed: number;
            /** In Use 30D */
            in_use_30d: number;
            /** Month */
            month: string;
            /** Paying */
            paying: number;
            /** Signups */
            signups: number;
        };
        /** CompanyLogoUpload */
        CompanyLogoUpload: {
            /**
             * Content Type
             * @enum {string}
             */
            content_type: "image/png" | "image/jpeg";
            /** Size Bytes */
            size_bytes: number;
        };
        /** CompanySettingsOut */
        CompanySettingsOut: {
            bank_details: components["schemas"]["BankDetails"];
            /** Billing Email */
            billing_email: string | null;
            /** Billing Phone */
            billing_phone: string | null;
            business_address: components["schemas"]["Address-Output"];
            /** Country */
            country: string;
            /** Credit Note Prefix */
            credit_note_prefix: string;
            /** Currency */
            currency: string;
            /** Invoice Example */
            invoice_example: string;
            /** Invoice Prefix */
            invoice_prefix: string;
            /** Legal Name */
            legal_name: string;
            /** Logo Url */
            logo_url: string | null;
            /** Missing */
            missing: string[];
            /** Number Padding */
            number_padding: number;
            /**
             * Number Reset
             * @enum {string}
             */
            number_reset: "never" | "yearly";
            /** Payment Instructions */
            payment_instructions: string | null;
            /** Payment Terms Days */
            payment_terms_days: number;
            registered_address: components["schemas"]["Address-Output"];
            /** Registration Number */
            registration_number: string | null;
            tax_today: components["schemas"]["TaxToday"];
            /** Timezone */
            timezone: string;
            /** Trading Name */
            trading_name: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** Vat Effective Date */
            vat_effective_date: string | null;
            /** Vat Number */
            vat_number: string | null;
            /** Vat Registered */
            vat_registered: boolean;
            /** Version */
            version: number;
        };
        /** CompanySettingsPut */
        CompanySettingsPut: {
            bank_details?: components["schemas"]["BankDetails"];
            /** Billing Email */
            billing_email?: string | null;
            /** Billing Phone */
            billing_phone?: string | null;
            business_address?: components["schemas"]["app__schemas__company__Address"];
            /**
             * Credit Note Prefix
             * @default CN
             */
            credit_note_prefix: string;
            /**
             * Invoice Prefix
             * @default INV
             */
            invoice_prefix: string;
            /** Legal Name */
            legal_name: string;
            /**
             * Number Padding
             * @default 6
             */
            number_padding: number;
            /**
             * Number Reset
             * @default never
             * @enum {string}
             */
            number_reset: "never" | "yearly";
            /** Payment Instructions */
            payment_instructions?: string | null;
            /**
             * Payment Terms Days
             * @default 7
             */
            payment_terms_days: number;
            /** Reason */
            reason: string;
            registered_address?: components["schemas"]["app__schemas__company__Address"];
            /** Registration Number */
            registration_number?: string | null;
            /** Trading Name */
            trading_name: string;
            /** Vat Effective Date */
            vat_effective_date?: string | null;
            /** Vat Number */
            vat_number?: string | null;
            /**
             * Vat Registered
             * @default false
             */
            vat_registered: boolean;
            /** Version */
            version: number;
        };
        /** Contact */
        Contact: {
            /** Address */
            address?: string | null;
            /** Email */
            email?: string | null;
            /** Phone */
            phone?: string | null;
        };
        /** ContactAddress */
        ContactAddress: {
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
        /** CountryList */
        CountryList: {
            /** Data */
            data: components["schemas"]["CountryOut"][];
        };
        /** CountryOut */
        CountryOut: {
            /** Code */
            code: string;
            /** Currency */
            currency: string;
            /** Dial */
            dial: string;
            /** Locale */
            locale: string;
            /** Name */
            name: string;
            /** Region */
            region: string;
            /** Tax Id Label */
            tax_id_label: string;
            /** Tax Id Pattern */
            tax_id_pattern: string | null;
            /** Tax Label */
            tax_label: string;
            /** Tax Rate Bp */
            tax_rate_bp: number | null;
            /** Timezone */
            timezone: string;
            /** Timezones */
            timezones: string[];
        };
        /** CountryPut */
        CountryPut: {
            /** Operational */
            operational: boolean;
            /** Reason */
            reason: string;
        };
        /** CreditNoteRequest */
        CreditNoteRequest: {
            /** Reason */
            reason: string;
        };
        /** CreditRequest */
        CreditRequest: {
            /** Amount Minor */
            amount_minor?: number | null;
            /** Reason */
            reason: string;
        };
        /** Cta */
        Cta: {
            /** Href */
            href: string;
            /** Label */
            label: string;
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
            /** Decimals */
            decimals: number;
            /** Name */
            name: string;
            /** Symbol */
            symbol: string;
        };
        /** CurrencyTotals */
        CurrencyTotals: {
            /** Currency */
            currency: string;
            month: components["schemas"]["SignedMoney"];
            payments_month: components["schemas"]["SignedMoney"];
            today: components["schemas"]["SignedMoney"];
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
        /**
         * DraftCreate
         * @description A manual invoice for an approved charge. Amounts are minor units of `currency`.
         */
        DraftCreate: {
            /** Currency */
            currency: string;
            /** Lines */
            lines: components["schemas"]["DraftLine"][];
            /** Notes */
            notes?: string | null;
            /** Period End */
            period_end?: string | null;
            /** Period Start */
            period_start?: string | null;
            /**
             * Prices Include Tax
             * @default false
             */
            prices_include_tax: boolean;
            /** Reason */
            reason: string;
        };
        /** DraftLine */
        DraftLine: {
            /**
             * Code
             * @default charge
             */
            code: string;
            /** Description */
            description: string;
            /**
             * Discount Minor
             * @default 0
             */
            discount_minor: number;
            /**
             * Quantity
             * @default 1
             */
            quantity: number;
            /** Unit Amount Minor */
            unit_amount_minor: number;
        };
        /**
         * EntryContent
         * @description A page is blocks; a post is a body with an excerpt, a cover and tags.
         */
        EntryContent: {
            /** Author */
            author?: string | null;
            /** Blocks */
            blocks?: (components["schemas"]["Hero"] | components["schemas"]["Features"] | components["schemas"]["Steps"] | components["schemas"]["Split"] | components["schemas"]["Stats"] | components["schemas"]["Testimonials"] | components["schemas"]["Faq"] | components["schemas"]["CallToAction"] | components["schemas"]["Logos"] | components["schemas"]["Pricing"] | components["schemas"]["RichText"] | components["schemas"]["LeadForm"] | components["schemas"]["PostList"] | components["schemas"]["Gallery"])[];
            /** Body */
            body?: string | null;
            /** Cover Id */
            cover_id?: string | null;
            /** Excerpt */
            excerpt?: string | null;
            seo?: components["schemas"]["Seo"];
            /** Tags */
            tags?: string[];
            /** Title */
            title: string;
        };
        /** EntryCreate */
        EntryCreate: {
            content: components["schemas"]["EntryContent"];
            /**
             * Kind
             * @enum {string}
             */
            kind: "page" | "post";
            /** Locale */
            locale: string;
            /** Slug */
            slug: string;
            /** Translation Of */
            translation_of?: string | null;
        };
        /** EntryList */
        EntryList: {
            /** Data */
            data: components["schemas"]["EntrySummary"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** EntryOut */
        EntryOut: {
            /** Draft */
            draft: {
                [key: string]: unknown;
            };
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Kind */
            kind: string;
            /** Locale */
            locale: string;
            /** Published */
            published: {
                [key: string]: unknown;
            } | null;
            /** Published At */
            published_at: string | null;
            /** Slug */
            slug: string;
            /**
             * Status
             * @enum {string}
             */
            status: "draft" | "published" | "changed";
            /** Title */
            title: string;
            /**
             * Translation Key
             * Format: uuid
             */
            translation_key: string;
            /** Translations */
            translations: {
                [key: string]: unknown;
            }[];
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** Version */
            version: number;
        };
        /** EntryPatch */
        EntryPatch: {
            content?: components["schemas"]["EntryContent"] | null;
            /** Slug */
            slug?: string | null;
        };
        /** EntrySummary */
        EntrySummary: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Kind */
            kind: string;
            /** Locale */
            locale: string;
            /** Published At */
            published_at: string | null;
            /** Slug */
            slug: string;
            /**
             * Status
             * @enum {string}
             */
            status: "draft" | "published" | "changed";
            /** Title */
            title: string;
            /**
             * Translation Key
             * Format: uuid
             */
            translation_key: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** Version */
            version: number;
        };
        /** EntryVersion */
        EntryVersion: {
            /** Content */
            content: {
                [key: string]: unknown;
            };
            /**
             * Published At
             * Format: date-time
             */
            published_at: string;
            /** Published By */
            published_by: string | null;
            /** Version */
            version: number;
        };
        /** EntryVersionList */
        EntryVersionList: {
            /** Data */
            data: components["schemas"]["EntryVersion"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** Faq */
        Faq: {
            /** Heading */
            heading?: string | null;
            /** Items */
            items: components["schemas"]["FaqItem"][];
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "faq";
        };
        /** FaqItem */
        FaqItem: {
            /** Answer */
            answer: string;
            /** Question */
            question: string;
        };
        /** FeatureItem */
        FeatureItem: {
            /** Body */
            body: string;
            /** Icon */
            icon?: string | null;
            /** Image Id */
            image_id?: string | null;
            /** Title */
            title: string;
        };
        /** Features */
        Features: {
            /** Heading */
            heading?: string | null;
            /** Intro */
            intro?: string | null;
            /** Items */
            items: components["schemas"]["FeatureItem"][];
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "features";
        };
        /** FeedbackComment */
        FeedbackComment: {
            /** Comment */
            comment: string | null;
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
            /** Rating */
            rating: number;
            /** Room */
            room: string;
            /**
             * Subject
             * @enum {string}
             */
            subject: "order" | "request" | "stay";
        };
        /** FeedbackCreate */
        FeedbackCreate: {
            /** Comment */
            comment?: string | null;
            /** Order Id */
            order_id?: string | null;
            /** Rating */
            rating: number;
            /** Request Id */
            request_id?: string | null;
            /**
             * Subject
             * @enum {string}
             */
            subject: "order" | "request" | "stay";
        };
        /** FeedbackList */
        FeedbackList: {
            /** Data */
            data: components["schemas"]["FeedbackOut"][];
        };
        /** FeedbackOut */
        FeedbackOut: {
            /** Comment */
            comment: string | null;
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
            /** Order Id */
            order_id: string | null;
            /** Rating */
            rating: number;
            /** Request Id */
            request_id: string | null;
            /**
             * Subject
             * @enum {string}
             */
            subject: "order" | "request" | "stay";
        };
        /** FeedbackReport */
        FeedbackReport: {
            /** Average */
            average: number | null;
            /** By Subject */
            by_subject: components["schemas"]["SubjectScore"][];
            /** Distribution */
            distribution: number[];
            /**
             * From
             * Format: date
             */
            from: string;
            /** Ratings */
            ratings: number;
            /** Recent */
            recent: components["schemas"]["FeedbackComment"][];
            /**
             * To
             * Format: date
             */
            to: string;
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
        /** Footer */
        Footer: {
            /** Columns */
            columns?: components["schemas"]["FooterColumn"][];
            /** Note */
            note?: string | null;
        };
        /** FooterColumn */
        FooterColumn: {
            /** Heading */
            heading: string;
            /** Links */
            links: components["schemas"]["NavLink"][];
        };
        /** ForgotPasswordRequest */
        ForgotPasswordRequest: {
            /** Email */
            email: string;
        };
        /** FunnelStep */
        FunnelStep: {
            /** Hotels */
            hotels: number;
            /** Label */
            label: string;
            /** Step */
            step: string;
        };
        /**
         * Gallery
         * @description Photos of hotels using Diyneco (kitchens, reception, rooms, outside...), with filters by
         *     area and a full-screen viewer (D91).
         */
        Gallery: {
            /** Heading */
            heading?: string | null;
            /** Intro */
            intro?: string | null;
            /** Items */
            items: components["schemas"]["GalleryItem"][];
            /**
             * Show Filters
             * @default true
             */
            show_filters: boolean;
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "gallery";
        };
        /** GalleryItem */
        GalleryItem: {
            /** Caption */
            caption?: string | null;
            /**
             * Category
             * @default other
             * @enum {string}
             */
            category: "rooms" | "reception" | "kitchen" | "restaurant" | "outside" | "pool" | "spa" | "conference" | "events" | "other";
            /**
             * Image Id
             * Format: uuid
             */
            image_id: string;
        };
        /** GroupCheckoutOut */
        GroupCheckoutOut: {
            amount: components["schemas"]["SignedMoney"];
            /** Checkout Url */
            checkout_url: string | null;
            /** Completed At */
            completed_at: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Failure Reason */
            failure_reason: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Invoices */
            invoices: number;
            paid: components["schemas"]["SignedMoney"] | null;
            /** Provider */
            provider: string;
            /**
             * Status
             * @enum {string}
             */
            status: "pending" | "succeeded" | "failed" | "cancelled" | "expired";
            /** Test Mode */
            test_mode: boolean;
            unallocated: components["schemas"]["SignedMoney"];
        };
        /** GroupPayRequest */
        GroupPayRequest: {
            /** Currency */
            currency: string;
        };
        /** GroupPaymentOut */
        GroupPaymentOut: {
            amount: components["schemas"]["SignedMoney"];
            /** Checkout Url */
            checkout_url: string | null;
            /** Completed At */
            completed_at: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Failure Reason */
            failure_reason: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            paid: components["schemas"]["SignedMoney"] | null;
            /** Provider */
            provider: string;
            /**
             * Status
             * @enum {string}
             */
            status: "pending" | "succeeded" | "failed" | "cancelled" | "expired";
            /** Test Mode */
            test_mode: boolean;
            unallocated: components["schemas"]["SignedMoney"];
        };
        /**
         * GroupStatement
         * @description Every open invoice of the owner's properties, what is due per currency (D89).
         */
        GroupStatement: {
            /** Due */
            due: components["schemas"]["SignedMoney"][];
            /** Group Discount Bp */
            group_discount_bp: number;
            /** Group Discount Min Properties */
            group_discount_min_properties: number;
            /** Invoices */
            invoices: components["schemas"]["StatementInvoice"][];
            /** Options */
            options: {
                [key: string]: unknown;
            };
            /** Payments */
            payments: components["schemas"]["GroupPaymentOut"][];
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
            /** Section */
            section: string;
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
            /** Ingredients */
            ingredients: string[];
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
        /** GuestRequestCreate */
        GuestRequestCreate: {
            /** Due At */
            due_at?: string | null;
            /**
             * Kind
             * @enum {string}
             */
            kind: "towels" | "toiletries" | "pillows" | "cleaning" | "turndown" | "maintenance" | "wake_up" | "late_checkout" | "luggage" | "other";
            /** Note */
            note?: string | null;
        };
        /** GuestRequestList */
        GuestRequestList: {
            /** Data */
            data: components["schemas"]["GuestRequestOut"][];
        };
        /**
         * GuestRequestOut
         * @description What the room's tablet sees: no staff names, only progress.
         */
        GuestRequestOut: {
            /** Acknowledged At */
            acknowledged_at: string | null;
            /** Cancelled At */
            cancelled_at: string | null;
            /** Completed At */
            completed_at: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Due At */
            due_at: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Kind
             * @enum {string}
             */
            kind: "towels" | "toiletries" | "pillows" | "cleaning" | "turndown" | "maintenance" | "wake_up" | "late_checkout" | "luggage" | "other";
            /** Note */
            note: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "open" | "acknowledged" | "in_progress" | "done" | "cancelled";
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
        /** Hero */
        Hero: {
            /** Eyebrow */
            eyebrow?: string | null;
            /** Heading */
            heading: string;
            /** Image Id */
            image_id?: string | null;
            primary?: components["schemas"]["Cta"] | null;
            secondary?: components["schemas"]["Cta"] | null;
            /** Subheading */
            subheading?: string | null;
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "hero";
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
            /** Code */
            code: string;
            /** Country */
            country: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Data Region */
            data_region: string;
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
            /** Property Type */
            property_type: string | null;
            /** Room Count */
            room_count: number | null;
            /** Slug */
            slug: string;
            /** Status */
            status: string;
            /** Version */
            version: number;
            /** Website */
            website: string | null;
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
            address?: components["schemas"]["app__schemas__hotel__Address"] | null;
            /** Email */
            email?: string | null;
            /** Legal Name */
            legal_name?: string | null;
            /** Name */
            name?: string | null;
            /** Phone */
            phone?: string | null;
            /** Property Type */
            property_type?: ("hotel" | "boutique_hotel" | "resort" | "motel" | "inn" | "lodge" | "guest_house" | "bed_and_breakfast" | "aparthotel" | "serviced_apartments" | "holiday_home" | "country_house" | "hostel" | "camp" | "other") | null;
            /** Room Count */
            room_count?: number | null;
            /** Website */
            website?: string | null;
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
            /** Cancel At Period End */
            cancel_at_period_end: boolean;
            /** Current Period Start */
            current_period_start: string | null;
            /** Interval */
            interval: ("month" | "quarter" | "year") | null;
            /** Limits */
            limits: {
                [key: string]: unknown;
            };
            /** Outstanding */
            outstanding: components["schemas"]["OutstandingInvoice"][];
            /** Past Due Since */
            past_due_since: string | null;
            pending_change: components["schemas"]["PendingChange"] | null;
            /** Plan */
            plan: {
                [key: string]: unknown;
            } | null;
            price: components["schemas"]["SignedMoney"] | null;
            /** Renews On */
            renews_on: string | null;
            /** Starts On */
            starts_on: string | null;
            /** Status */
            status: ("trial" | "pending_payment" | "active" | "past_due" | "suspended" | "cancellation_scheduled") | null;
            /** Suspended At */
            suspended_at: string | null;
            /** Trial Ends On */
            trial_ends_on: string | null;
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
        /** InsightPeriod */
        InsightPeriod: {
            /** Activation Bp */
            activation_bp: number;
            /** Churn Bp */
            churn_bp: number;
            /** Churned */
            churned: number;
            /** Churned Mrr */
            churned_mrr: components["schemas"]["SignedMoney"][];
            /** New Mrr */
            new_mrr: components["schemas"]["SignedMoney"][];
            /** Paying At Start */
            paying_at_start: number;
            /** Signups */
            signups: number;
            /** Trial Conversion Bp */
            trial_conversion_bp: number;
            /** Trials Converted */
            trials_converted: number;
            /** Trials Ended */
            trials_ended: number;
        };
        /** InsightTotals */
        InsightTotals: {
            /** Activated */
            activated: number;
            /** Active */
            active: number;
            /** Gmv 30D */
            gmv_30d: components["schemas"]["SignedMoney"][];
            /** Hotels */
            hotels: number;
            /** In Use 30D */
            in_use_30d: number;
            /** Mrr */
            mrr: components["schemas"]["SignedMoney"][];
            /** Multi Property Owners */
            multi_property_owners: number;
            /** No Plan */
            no_plan: number;
            /** Owners */
            owners: number;
            /** Paying */
            paying: number;
            /** Pending Approval */
            pending_approval: number;
            /** Rooms */
            rooms: number;
            /** Suspended */
            suspended: number;
            /** Trials */
            trials: number;
        };
        /** InsightsOut */
        InsightsOut: {
            /** By Country */
            by_country: components["schemas"]["Breakdown"][];
            /** By Property Type */
            by_property_type: components["schemas"]["Breakdown"][];
            /** By Region */
            by_region: components["schemas"]["Breakdown"][];
            /** Cohorts */
            cohorts: components["schemas"]["Cohort"][];
            /** Days */
            days: components["schemas"]["SignupDay"][];
            /** Funnel */
            funnel: components["schemas"]["FunnelStep"][];
            period: components["schemas"]["InsightPeriod"];
            /**
             * Since
             * Format: date
             */
            since: string;
            totals: components["schemas"]["InsightTotals"];
            /**
             * Until
             * Format: date
             */
            until: string;
            /** Users */
            users: components["schemas"]["RoleActivity"][];
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
        /** InvoiceLineOut */
        InvoiceLineOut: {
            /** Code */
            code: string;
            /** Description */
            description: string;
            /** Discount Minor */
            discount_minor: number;
            /** Position */
            position: number;
            /** Quantity */
            quantity: number;
            /** Tax Minor */
            tax_minor: number;
            /** Total Minor */
            total_minor: number;
            /** Unit Amount Minor */
            unit_amount_minor: number;
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
            /** Station Id */
            station_id?: string | null;
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
            /** Locale */
            locale: string;
            /** Next Cursor */
            next_cursor?: string | null;
            /** Timezone */
            timezone: string;
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
        /** KitchenMenu */
        KitchenMenu: {
            /** Data */
            data: components["schemas"]["KitchenMenuItem"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /**
         * KitchenMenuItem
         * @description A dish as the kitchen sees it: no prices (security spec).
         */
        KitchenMenuItem: {
            /** Category */
            category: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Is Available */
            is_available: boolean;
            /** Name */
            name: string;
            /**
             * Station Id
             * Format: uuid
             */
            station_id: string;
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
        /** LeadForm */
        LeadForm: {
            /** Heading */
            heading?: string | null;
            /** Intro */
            intro?: string | null;
            /**
             * Kind
             * @enum {string}
             */
            kind: "demo" | "contact";
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "lead_form";
        };
        /** LeadIn */
        LeadIn: {
            /** Company */
            company?: string | null;
            /**
             * Consent
             * @constant
             */
            consent: true;
            /** Consent Text */
            consent_text: string;
            /** Country */
            country?: string | null;
            /** Elapsed Ms */
            elapsed_ms: number;
            /** Email */
            email: string;
            /**
             * Kind
             * @enum {string}
             */
            kind: "demo" | "contact";
            /** Locale */
            locale: string;
            /** Message */
            message?: string | null;
            /** Name */
            name: string;
            /** Phone */
            phone?: string | null;
            /** Rooms */
            rooms?: number | null;
            /** Source Path */
            source_path?: string | null;
            /**
             * Website
             * @default
             */
            website: string;
        };
        /** LeadList */
        LeadList: {
            /** Data */
            data: components["schemas"]["LeadOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** LeadOut */
        LeadOut: {
            /** Company */
            company: string | null;
            /** Consent Text */
            consent_text: string;
            /** Country */
            country: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Email */
            email: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Kind */
            kind: string;
            /** Locale */
            locale: string;
            /** Message */
            message: string | null;
            /** Name */
            name: string;
            /** Notes */
            notes: string | null;
            /** Phone */
            phone: string | null;
            /** Rooms */
            rooms: number | null;
            /** Source Path */
            source_path: string | null;
            /** Status */
            status: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** LeadPatch */
        LeadPatch: {
            /** Notes */
            notes?: string | null;
            /** Status */
            status?: ("new" | "contacted" | "qualified" | "closed" | "spam") | null;
        };
        /** LegalAccept */
        LegalAccept: {
            /** Document Ids */
            document_ids: string[];
        };
        /** LegalDocumentList */
        LegalDocumentList: {
            /** Data */
            data: components["schemas"]["LegalDocumentOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** LegalDocumentOut */
        LegalDocumentOut: {
            /** Body */
            body?: string | null;
            /** Country */
            country: string | null;
            /** Effective At */
            effective_at: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Kind
             * @enum {string}
             */
            kind: "terms" | "privacy" | "dpa" | "acceptable_use" | "guest_terms" | "guest_privacy";
            /** Published At */
            published_at: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "draft" | "published";
            /** Summary */
            summary: string | null;
            /** Title */
            title: string;
            /** Version */
            version: number;
        };
        /** LegalDraftCreate */
        LegalDraftCreate: {
            /** Body */
            body: string;
            /** Country */
            country?: string | null;
            /** Effective At */
            effective_at?: string | null;
            /**
             * Kind
             * @enum {string}
             */
            kind: "terms" | "privacy" | "dpa" | "acceptable_use" | "guest_terms" | "guest_privacy";
            /** Summary */
            summary?: string | null;
            /** Title */
            title: string;
        };
        /** LegalDraftPatch */
        LegalDraftPatch: {
            /** Body */
            body?: string | null;
            /** Effective At */
            effective_at?: string | null;
            /** Summary */
            summary?: string | null;
            /** Title */
            title?: string | null;
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
        /** LogoItem */
        LogoItem: {
            /** Href */
            href?: string | null;
            /**
             * Image Id
             * Format: uuid
             */
            image_id: string;
            /** Name */
            name: string;
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
        /** Logos */
        Logos: {
            /** Heading */
            heading?: string | null;
            /** Items */
            items: components["schemas"]["LogoItem"][];
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "logos";
        };
        /**
         * ManualPayment
         * @description A payment seen on Diyneco's bank statement, recorded after checking it.
         */
        ManualPayment: {
            /** Amount Minor */
            amount_minor: number;
            /**
             * Invoice Id
             * Format: uuid
             */
            invoice_id: string;
            /**
             * Method
             * @default eft
             * @enum {string}
             */
            method: "eft" | "other";
            /** Notes */
            notes?: string | null;
            /**
             * Received On
             * Format: date
             */
            received_on: string;
            /** Reference */
            reference: string;
        };
        /** MeHotel */
        MeHotel: {
            /** Code */
            code: string;
            /** Currency */
            currency: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Locale */
            locale: string;
            /** Name */
            name: string;
            /** Status */
            status: string;
            /** Tax Label */
            tax_label: string;
            /** Timezone */
            timezone: string;
        };
        /**
         * MeOut
         * @description Who is signed in and what they may do, so apps show only usable actions. The server
         *     still checks every permission on every request.
         */
        MeOut: {
            /**
             * Has Pin
             * @default false
             */
            has_pin: boolean;
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
        /** MediaList */
        MediaList: {
            /** Data */
            data: components["schemas"]["MediaOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** MediaOut */
        MediaOut: {
            /** Alt */
            alt: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Filename */
            filename: string;
            /** Height */
            height: number;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Url */
            url: string;
            /** Width */
            width: number;
            /** Widths */
            widths: number[];
        };
        /** MediaPatch */
        MediaPatch: {
            /** Alt */
            alt: string;
        };
        /** MediaUpload */
        MediaUpload: {
            /**
             * Alt
             * @default
             */
            alt: string;
            /** Data Base64 */
            data_base64: string;
            /** Filename */
            filename: string;
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
        /** ModifierGroupPatch */
        ModifierGroupPatch: {
            /** Max Select */
            max_select?: number | null;
            /** Min Select */
            min_select?: number | null;
            /** Name */
            name?: string | null;
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
        /** ModifierOptionPatch */
        ModifierOptionPatch: {
            /** Is Available */
            is_available?: boolean | null;
            /** Name */
            name?: string | null;
            price_delta?: components["schemas"]["Money"] | null;
            /** Sort Order */
            sort_order?: number | null;
        };
        /** Money */
        Money: {
            /** Amount Minor */
            amount_minor: number;
            /** Currency */
            currency: string;
        };
        /**
         * MultiInvite
         * @description One person invited to several of the owner's properties, with a role at each (D90).
         */
        MultiInvite: {
            /** Assignments */
            assignments: components["schemas"]["PropertyAssignment"][];
            /** Department */
            department?: string | null;
            /** Email */
            email: string;
            /** Name */
            name: string;
        };
        /** MultiInviteList */
        MultiInviteList: {
            /** Data */
            data: components["schemas"]["MultiInviteResult"][];
        };
        /** MultiInviteResult */
        MultiInviteResult: {
            /** Email */
            email: string;
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
            /** Hotel Name */
            hotel_name: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Roles */
            roles: {
                [key: string]: unknown;
            }[];
        };
        /** NavLink */
        NavLink: {
            /** Href */
            href: string;
            /** Label */
            label: string;
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
            /**
             * Voided Items
             * @default []
             */
            voided_items: components["schemas"]["VoidedItemOut"][];
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
        /** OutstandingInvoice */
        OutstandingInvoice: {
            balance: components["schemas"]["SignedMoney"];
            /** Due On */
            due_on: string | null;
            /**
             * Invoice Id
             * Format: uuid
             */
            invoice_id: string;
            /** Number */
            number: string | null;
            /** Status */
            status: string;
        };
        /** OwnerHotel */
        OwnerHotel: {
            /** City */
            city: string | null;
            /** Code */
            code: string;
            /** Country */
            country: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
            /** Plan Name */
            plan_name: string | null;
            /** Property Type */
            property_type: string | null;
            /** Province */
            province: string | null;
            /** Rooms */
            rooms: number;
            /** Status */
            status: string;
            /** Subscription Status */
            subscription_status: string | null;
        };
        /** OwnerList */
        OwnerList: {
            /** Data */
            data: components["schemas"]["OwnerOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** OwnerOut */
        OwnerOut: {
            /** Countries */
            countries: string[];
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Email */
            email: string;
            /** Email Verified */
            email_verified: boolean;
            /** Gmv 30D */
            gmv_30d: components["schemas"]["SignedMoney"][];
            /** Hotels */
            hotels: components["schemas"]["OwnerHotel"][];
            /** Last Login At */
            last_login_at: string | null;
            /** Mrr */
            mrr: components["schemas"]["SignedMoney"][];
            /** Name */
            name: string;
            /** Paying */
            paying: number;
            /** Phone */
            phone: string | null;
            /** Rooms */
            rooms: number;
            /**
             * User Id
             * Format: uuid
             */
            user_id: string;
        };
        /** PageViewIn */
        PageViewIn: {
            /** Locale */
            locale: string;
            /** Path */
            path: string;
            /**
             * Referrer
             * @default
             */
            referrer: string;
        };
        /**
         * PairRequest
         * @description Device setup (D82): the Hotel ID, the 8-digit setup code and the PIN of the manager who
         *     created the code.
         */
        PairRequest: {
            /** Code */
            code: string;
            device_info?: components["schemas"]["DeviceInfo"];
            /** Hotel Code */
            hotel_code: string;
            /** Pin */
            pin: string;
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
            /**
             * Hotel Code
             * @description The hotel's Hotel ID, entered on the device with the code.
             */
            hotel_code: string;
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
        /** PaymentOptions */
        PaymentOptions: {
            /** Eft */
            eft: {
                [key: string]: unknown;
            };
            /** Online */
            online: {
                [key: string]: unknown;
            };
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
        /** PdfLink */
        PdfLink: {
            /** Url */
            url: string;
        };
        /** PendingChange */
        PendingChange: {
            /** Effective On */
            effective_on: string | null;
            /** Interval */
            interval: ("month" | "quarter" | "year") | null;
            /** Plan Code */
            plan_code: string;
            /** Plan Name */
            plan_name: string;
            price: components["schemas"]["SignedMoney"];
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
        /** Person */
        Person: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Name */
            name: string;
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
        /** PlanChangeOut */
        PlanChangeOut: {
            /**
             * Effective
             * @enum {string}
             */
            effective: "now" | "renewal" | "withdrawn";
            invoice: components["schemas"]["SubscriptionInvoiceOut"] | null;
            subscription: components["schemas"]["HotelSubscription"];
        };
        /** PlanChangeRequest */
        PlanChangeRequest: {
            /**
             * Interval
             * @enum {string}
             */
            interval: "month" | "quarter" | "year";
            /** Plan Code */
            plan_code: string;
        };
        /** PlanCreate */
        PlanCreate: {
            /** Can Downgrade */
            can_downgrade?: boolean | null;
            /** Can Upgrade */
            can_upgrade?: boolean | null;
            /** Code */
            code: string;
            /** Currency */
            currency: string;
            /** Description */
            description?: string | null;
            /** Display Order */
            display_order?: number | null;
            /** Features */
            features?: {
                [key: string]: boolean;
            } | null;
            /** Highlights */
            highlights?: string[] | null;
            /** Limits */
            limits?: {
                [key: string]: number;
            } | null;
            /** Name */
            name: string;
            /** Overage Policy */
            overage_policy?: string | null;
            /** Promo Discount Bp */
            promo_discount_bp?: number | null;
            /** Promo Ends On */
            promo_ends_on?: string | null;
            /** Recommended */
            recommended?: boolean | null;
            /** Setup Fee Minor */
            setup_fee_minor?: number | null;
            /** Short Description */
            short_description?: string | null;
            /** Support Level */
            support_level?: string | null;
            /** Tax Treatment */
            tax_treatment?: ("exclusive" | "inclusive") | null;
            /** Trial Days */
            trial_days?: number | null;
        };
        /** PlanList */
        PlanList: {
            /** Data */
            data: components["schemas"]["app__schemas__plans__PlanOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** PlanPatch */
        PlanPatch: {
            /** Can Downgrade */
            can_downgrade?: boolean | null;
            /** Can Upgrade */
            can_upgrade?: boolean | null;
            /** Currency */
            currency?: string | null;
            /** Description */
            description?: string | null;
            /** Display Order */
            display_order?: number | null;
            /** Features */
            features?: {
                [key: string]: boolean;
            } | null;
            /** Highlights */
            highlights?: string[] | null;
            /** Limits */
            limits?: {
                [key: string]: number;
            } | null;
            /** Name */
            name?: string | null;
            /** Overage Policy */
            overage_policy?: string | null;
            /** Promo Discount Bp */
            promo_discount_bp?: number | null;
            /** Promo Ends On */
            promo_ends_on?: string | null;
            /** Reason */
            reason?: string | null;
            /** Recommended */
            recommended?: boolean | null;
            /** Setup Fee Minor */
            setup_fee_minor?: number | null;
            /** Short Description */
            short_description?: string | null;
            /** Support Level */
            support_level?: string | null;
            /** Tax Treatment */
            tax_treatment?: ("exclusive" | "inclusive") | null;
            /** Trial Days */
            trial_days?: number | null;
            /** Version */
            version: number;
        };
        /** PlanRevenue */
        PlanRevenue: {
            collected: components["schemas"]["SignedMoney"];
            mrr: components["schemas"]["SignedMoney"];
            /** Plan Code */
            plan_code: string;
            /** Plan Name */
            plan_name: string;
            /** Subscriptions */
            subscriptions: number;
        };
        /** PlanStatusChange */
        PlanStatusChange: {
            /** Reason */
            reason: string;
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
        /** PlatformInviteAccept */
        PlatformInviteAccept: {
            /** Password */
            password: string;
            /** Token */
            token: string;
        };
        /**
         * PlatformLoginRequest
         * @description Admin panel sign-in (D75): a Diyneco staff account has no hotel.
         */
        PlatformLoginRequest: {
            /** Email */
            email: string;
            /** Password */
            password: string;
        };
        /** PlatformRole */
        PlatformRole: {
            /** Code */
            code: string;
            /** Name */
            name: string;
            /** Permissions */
            permissions: string[];
        };
        /** PlatformRoleList */
        PlatformRoleList: {
            /** Data */
            data: components["schemas"]["PlatformRole"][];
        };
        /** PlatformStaffInvite */
        PlatformStaffInvite: {
            /**
             * Email
             * Format: email
             */
            email: string;
            /** Name */
            name: string;
            /** Roles */
            roles: string[];
        };
        /** PlatformStaffList */
        PlatformStaffList: {
            /** Data */
            data: components["schemas"]["PlatformStaffOut"][];
        };
        /** PlatformStaffOut */
        PlatformStaffOut: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Email */
            email: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Last Login At */
            last_login_at: string | null;
            /** Mfa Enrolled */
            mfa_enrolled: boolean;
            /** Name */
            name: string;
            /** Roles */
            roles: string[];
            /**
             * Status
             * @enum {string}
             */
            status: "invited" | "active" | "locked" | "deactivated";
        };
        /** PlatformStaffRoles */
        PlatformStaffRoles: {
            /** Roles */
            roles: string[];
        };
        /** PortfolioHotel */
        PortfolioHotel: {
            /** Arrivals Today */
            arrivals_today: number;
            /**
             * Business Date
             * Format: date
             */
            business_date: string;
            /** City */
            city: string | null;
            /** Code */
            code: string;
            /** Country */
            country: string;
            /** Currency */
            currency: string;
            /**
             * Hotel Id
             * Format: uuid
             */
            hotel_id: string;
            /** In House */
            in_house: number;
            /** Name */
            name: string;
            /** Occupancy Bp */
            occupancy_bp: number;
            /** Occupied */
            occupied: number;
            /** Open Orders */
            open_orders: number;
            payments_month: components["schemas"]["SignedMoney"];
            /** Plan Name */
            plan_name: string | null;
            /** Property Type */
            property_type: string | null;
            /** Province */
            province: string | null;
            revenue_month: components["schemas"]["SignedMoney"];
            revenue_today: components["schemas"]["SignedMoney"];
            /** Rooms */
            rooms: number;
            /** Staff */
            staff: number;
            /** Status */
            status: string;
            /** Subscription Status */
            subscription_status: string | null;
            /** Trial Ends On */
            trial_ends_on: string | null;
        };
        /** PortfolioOut */
        PortfolioOut: {
            /** Data */
            data: components["schemas"]["PortfolioHotel"][];
            totals: components["schemas"]["PortfolioTotals"];
        };
        /** PortfolioTotals */
        PortfolioTotals: {
            /** In House */
            in_house: number;
            /** Occupancy Bp */
            occupancy_bp: number;
            /** Occupied */
            occupied: number;
            /** Open Orders */
            open_orders: number;
            /** Properties */
            properties: number;
            /** Revenue */
            revenue: components["schemas"]["CurrencyTotals"][];
            /** Rooms */
            rooms: number;
        };
        /** PostCard */
        PostCard: {
            /** Author */
            author: string | null;
            /** Cover */
            cover: {
                [key: string]: unknown;
            } | null;
            /** Excerpt */
            excerpt: string | null;
            /** Path */
            path: string;
            /**
             * Published At
             * Format: date-time
             */
            published_at: string;
            /** Slug */
            slug: string;
            /** Tags */
            tags: string[];
            /** Title */
            title: string;
        };
        /** PostCardList */
        PostCardList: {
            /** Data */
            data: components["schemas"]["PostCard"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /**
         * PostList
         * @description The latest blog posts in the page's language.
         */
        PostList: {
            /** Heading */
            heading?: string | null;
            /**
             * Limit
             * @default 3
             */
            limit: number;
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "post_list";
        };
        /** PreviewOut */
        PreviewOut: {
            /** Expires In */
            expires_in: number;
            /** Url */
            url: string;
        };
        /** PriceCreate */
        PriceCreate: {
            amount: components["schemas"]["Money"];
            /** Effective From */
            effective_from?: string | null;
            /**
             * Existing Policy
             * @default new_only
             * @enum {string}
             */
            existing_policy: "new_only" | "next_renewal";
            /**
             * Interval
             * @enum {string}
             */
            interval: "month" | "quarter" | "year";
            intro_amount?: components["schemas"]["Money"] | null;
            /** Intro Periods */
            intro_periods?: number | null;
            /** Reason */
            reason: string;
        };
        /** PriceOut */
        PriceOut: {
            amount: components["schemas"]["SignedMoney"];
            /**
             * Effective From
             * Format: date-time
             */
            effective_from: string;
            /**
             * Existing Policy
             * @enum {string}
             */
            existing_policy: "new_only" | "next_renewal";
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** In Force */
            in_force: boolean;
            /**
             * Interval
             * @enum {string}
             */
            interval: "month" | "quarter" | "year";
            intro_amount: components["schemas"]["SignedMoney"] | null;
            /** Intro Periods */
            intro_periods: number | null;
            /** Notice Days */
            notice_days: number | null;
            per_month: components["schemas"]["SignedMoney"];
            /** Reason */
            reason: string;
        };
        /**
         * Pricing
         * @description The live published plans from GET /plans, so prices on the site always match billing.
         */
        Pricing: {
            /** Heading */
            heading?: string | null;
            /** Intro */
            intro?: string | null;
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "pricing";
        };
        /** PropertyAssignment */
        PropertyAssignment: {
            /**
             * Hotel Id
             * Format: uuid
             */
            hotel_id: string;
            /** Role Codes */
            role_codes: ("hotel_owner" | "hotel_admin" | "general_manager" | "reception_manager" | "receptionist" | "finance_manager" | "kitchen_manager" | "kitchen_staff" | "room_service_manager" | "room_service_staff")[];
        };
        /** ProviderStatusOut */
        ProviderStatusOut: {
            /** Bank Details Set */
            bank_details_set: boolean;
            /** Eft Enabled */
            eft_enabled: boolean;
            /** Environment */
            environment: string;
            /** Sandbox Allowed */
            sandbox_allowed: boolean;
            /**
             * Selected
             * @enum {string}
             */
            selected: "none" | "sandbox" | "stitch";
            /** Stitch */
            stitch: {
                [key: string]: unknown;
            };
        };
        /** PublicEntry */
        PublicEntry: {
            /** Alternates */
            alternates: components["schemas"]["Alternate"][];
            /** Content */
            content: {
                [key: string]: unknown;
            };
            /** Kind */
            kind: string;
            /** Locale */
            locale: string;
            /** Media */
            media: {
                [key: string]: {
                    [key: string]: unknown;
                };
            };
            /** Path */
            path: string;
            /** Posts */
            posts?: {
                [key: string]: unknown;
            }[];
            /**
             * Preview
             * @default false
             */
            preview: boolean;
            /** Published At */
            published_at: string | null;
            /** Slug */
            slug: string;
            /** Updated At */
            updated_at: string | null;
        };
        /** PublicPlan */
        PublicPlan: {
            /** Code */
            code: string;
            /** Currency */
            currency: string;
            /** Description */
            description: string | null;
            /** Highlights */
            highlights: string[];
            /** Limits */
            limits: {
                [key: string]: number;
            };
            /** Name */
            name: string;
            /** Overage Policy */
            overage_policy: string | null;
            /** Prices */
            prices: components["schemas"]["PublicPrice"][];
            /** Promo Discount Bp */
            promo_discount_bp: number;
            /** Promo Ends On */
            promo_ends_on: string | null;
            /** Recommended */
            recommended: boolean;
            setup_fee: components["schemas"]["SignedMoney"];
            /** Short Description */
            short_description: string | null;
            /** Support Level */
            support_level: string | null;
            /**
             * Tax Treatment
             * @enum {string}
             */
            tax_treatment: "exclusive" | "inclusive";
            /** Trial Days */
            trial_days: number;
        };
        /** PublicPlanList */
        PublicPlanList: {
            /** Data */
            data: components["schemas"]["PublicPlan"][];
            /** Tax Charged */
            tax_charged: boolean;
            /** Tax Name */
            tax_name: string | null;
            /** Tax Rate Bp */
            tax_rate_bp: number | null;
        };
        /** PublicPrice */
        PublicPrice: {
            amount: components["schemas"]["SignedMoney"];
            /**
             * Interval
             * @enum {string}
             */
            interval: "month" | "quarter" | "year";
            intro_amount: components["schemas"]["SignedMoney"] | null;
            /** Intro Periods */
            intro_periods: number | null;
            per_month: components["schemas"]["SignedMoney"];
            /** Saving Bp */
            saving_bp: number | null;
        };
        /**
         * PublicSettings
         * @description What the website renders with. The lead address is never public.
         */
        PublicSettings: {
            /** Analytics */
            analytics: {
                [key: string]: unknown;
            };
            /** Base Url */
            base_url: string;
            /** Contact */
            contact: {
                [key: string]: unknown;
            };
            /** Default Locale */
            default_locale: string;
            /** Footer */
            footer: {
                [key: string]: unknown;
            };
            /** Locales */
            locales: string[];
            /** Media */
            media: {
                [key: string]: {
                    [key: string]: unknown;
                };
            };
            /** Navigation */
            navigation: {
                [key: string]: unknown;
            }[];
            /** Seo */
            seo: {
                [key: string]: unknown;
            };
            /** Site Name */
            site_name: string;
            /** Social */
            social: {
                [key: string]: unknown;
            }[];
            /** Verification */
            verification: {
                [key: string]: unknown;
            };
        };
        /** Quote */
        Quote: {
            fee: components["schemas"]["Money"];
            /** Lines */
            lines: components["schemas"]["app__schemas__orders__QuoteLine"][];
            /** Needs Approval */
            needs_approval: boolean;
            subtotal: components["schemas"]["Money"];
            total: components["schemas"]["Money"];
            vat_included: components["schemas"]["Money"];
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
        /** QuoteOut */
        QuoteOut: {
            /** Currency */
            currency: string;
            /**
             * Group Discount Bp
             * @default 0
             */
            group_discount_bp: number;
            /**
             * Interval
             * @enum {string}
             */
            interval: "month" | "quarter" | "year";
            /** Intro Periods */
            intro_periods: number | null;
            /** Lines */
            lines: components["schemas"]["app__schemas__reports__QuoteLine"][];
            /**
             * Period End
             * Format: date
             */
            period_end: string;
            /**
             * Period Start
             * Format: date
             */
            period_start: string;
            /** Plan Code */
            plan_code: string;
            /** Plan Name */
            plan_name: string;
            /** Prices Include Tax */
            prices_include_tax: boolean;
            /** Renews At Minor */
            renews_at_minor: number;
            /** Subtotal Minor */
            subtotal_minor: number;
            /** Tax Charged */
            tax_charged: boolean;
            /** Tax Minor */
            tax_minor: number;
            /** Tax Name */
            tax_name: string | null;
            /** Tax Rate Bp */
            tax_rate_bp: number | null;
            /** Total Minor */
            total_minor: number;
            /** Trial Days */
            trial_days: number;
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
        /** ReconcileRequest */
        ReconcileRequest: {
            /** Note */
            note?: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "unreconciled" | "matched" | "disputed";
        };
        /** RedirectIn */
        RedirectIn: {
            /** From Path */
            from_path: string;
            /**
             * Permanent
             * @default true
             */
            permanent: boolean;
            /** To Path */
            to_path: string;
        };
        /** RedirectList */
        RedirectList: {
            /** Data */
            data: components["schemas"]["RedirectOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** RedirectOut */
        RedirectOut: {
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** From Path */
            from_path: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Permanent */
            permanent: boolean;
            /** To Path */
            to_path: string;
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
        /** RefundOut */
        RefundOut: {
            amount: components["schemas"]["SignedMoney"];
            /**
             * Credit Note Id
             * Format: uuid
             */
            credit_note_id: string;
            /** Credit Note Number */
            credit_note_number: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Method
             * @enum {string}
             */
            method: "provider" | "manual";
            /**
             * Payment Id
             * Format: uuid
             */
            payment_id: string;
            /** Reference */
            reference: string | null;
            /** Test Mode */
            test_mode: boolean;
        };
        /** RefundRequest */
        RefundRequest: {
            /** Amount Minor */
            amount_minor: number;
            /** Reason */
            reason: string;
            /** Reference */
            reference?: string | null;
        };
        /** RegionList */
        RegionList: {
            /** Data */
            data: components["schemas"]["RegionOut"][];
            /** Label */
            label: string;
        };
        /** RegionOut */
        RegionOut: {
            /** Code */
            code: string;
            /** Name */
            name: string;
        };
        /** RejectRequest */
        RejectRequest: {
            /** Reason */
            reason: string;
        };
        /** RequestKindRow */
        RequestKindRow: {
            /** Cancelled */
            cancelled: number;
            /** Done */
            done: number;
            /** From Guests */
            from_guests: number;
            /** Kind */
            kind: string;
            /** Median Minutes To Done */
            median_minutes_to_done: number | null;
            /** Median Minutes To Seen */
            median_minutes_to_seen: number | null;
            /** Requests */
            requests: number;
        };
        /** RequestList */
        RequestList: {
            /** Data */
            data: components["schemas"]["RequestOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
            summary: components["schemas"]["RequestSummary"];
        };
        /** RequestOut */
        RequestOut: {
            /** Acknowledged At */
            acknowledged_at: string | null;
            assigned_to: components["schemas"]["Person"] | null;
            /** Cancel Reason */
            cancel_reason: string | null;
            /** Cancelled At */
            cancelled_at: string | null;
            /** Cancelled By */
            cancelled_by: ("guest" | "staff") | null;
            /** Completed At */
            completed_at: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            created_by: components["schemas"]["Person"] | null;
            /** Due At */
            due_at: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Kind
             * @enum {string}
             */
            kind: "towels" | "toiletries" | "pillows" | "cleaning" | "turndown" | "maintenance" | "wake_up" | "late_checkout" | "luggage" | "other";
            /** Note */
            note: string | null;
            /** Room */
            room: string;
            /**
             * Room Id
             * Format: uuid
             */
            room_id: string;
            /**
             * Source
             * @enum {string}
             */
            source: "guest" | "staff";
            /** Started At */
            started_at: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "open" | "acknowledged" | "in_progress" | "done" | "cancelled";
            /** Stay Id */
            stay_id: string | null;
            /** Waiting Minutes */
            waiting_minutes: number;
        };
        /** RequestStaffRow */
        RequestStaffRow: {
            /** Done */
            done: number;
            /** Median Minutes To Done */
            median_minutes_to_done: number | null;
            /** Name */
            name: string;
            /** Staff Id */
            staff_id: string | null;
        };
        /** RequestSummary */
        RequestSummary: {
            /** Done Today */
            done_today: number;
            /** In Progress */
            in_progress: number;
            /** Median Minutes To Done */
            median_minutes_to_done: number | null;
            /** Open */
            open: number;
        };
        /**
         * RequestsReport
         * @description Guest service requests (D93) by kind and by who finished them.
         */
        RequestsReport: {
            /**
             * From
             * Format: date
             */
            from: string;
            /** Kinds */
            kinds: components["schemas"]["RequestKindRow"][];
            /** Staff */
            staff: components["schemas"]["RequestStaffRow"][];
            /**
             * To
             * Format: date
             */
            to: string;
        };
        /** ResendEmailCodeRequest */
        ResendEmailCodeRequest: {
            /** Email */
            email: string;
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
        /** RichText */
        RichText: {
            /** Body */
            body: string;
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "rich_text";
        };
        /** RoleActivity */
        RoleActivity: {
            /** Active 30D */
            active_30d: number;
            /** Active 7D */
            active_7d: number;
            /** Members */
            members: number;
            /** Role */
            role: string;
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
        /** SandboxOutcome */
        SandboxOutcome: {
            /**
             * Outcome
             * @enum {string}
             */
            outcome: "succeeded" | "failed";
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
        /** SentOut */
        SentOut: {
            /** Recipients */
            recipients: number;
        };
        /** Seo */
        Seo: {
            /** Description */
            description?: string | null;
            /** Image Id */
            image_id?: string | null;
            /**
             * Noindex
             * @default false
             */
            noindex: boolean;
            /** Title */
            title?: string | null;
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
        /** SettingsIn */
        SettingsIn: {
            analytics: components["schemas"]["Analytics-Input"];
            /** Base Url */
            base_url: string;
            contact: components["schemas"]["Contact"];
            /** Default Locale */
            default_locale: string;
            footer: components["schemas"]["Footer"];
            /** Lead Email */
            lead_email: string;
            /** Locales */
            locales: string[];
            /** Navigation */
            navigation: components["schemas"]["NavLink"][];
            seo: components["schemas"]["SiteSeo"];
            /** Site Name */
            site_name: string;
            /** Social */
            social: components["schemas"]["SocialLink"][];
            verification: components["schemas"]["Verification"];
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
            /** Locale */
            locale?: string | null;
            /** Menu Prices Include Vat */
            menu_prices_include_vat?: boolean | null;
            room_charge_auto_approve_limit?: components["schemas"]["Money"] | null;
            /** Room Charging Enabled */
            room_charging_enabled?: boolean | null;
            room_service_fee?: components["schemas"]["Money"] | null;
            /** Room Status After Checkout */
            room_status_after_checkout?: ("cleaning" | "available") | null;
            /** Tax Label */
            tax_label?: string | null;
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
        /** SignupDay */
        SignupDay: {
            /**
             * Day
             * Format: date
             */
            day: string;
            /** Signups */
            signups: number;
        };
        /** SignupHotel */
        SignupHotel: {
            address?: components["schemas"]["app__schemas__hotel__Address"] | null;
            /** Country */
            country: string;
            /** Currency */
            currency?: string | null;
            /** Email */
            email?: string | null;
            /** Legal Name */
            legal_name?: string | null;
            /** Locale */
            locale?: string | null;
            /** Name */
            name: string;
            /** Phone */
            phone?: string | null;
            /** Property Type */
            property_type?: ("hotel" | "boutique_hotel" | "resort" | "motel" | "inn" | "lodge" | "guest_house" | "bed_and_breakfast" | "aparthotel" | "serviced_apartments" | "holiday_home" | "country_house" | "hostel" | "camp" | "other") | null;
            /** Room Count */
            room_count?: number | null;
            /** Timezone */
            timezone?: string | null;
            /** Website */
            website?: string | null;
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
            /** Phone */
            phone?: string | null;
        };
        /** SignupRequest */
        SignupRequest: {
            /** Accepted Documents */
            accepted_documents?: string[];
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
        /** SiteSeo */
        SiteSeo: {
            /** Default Description */
            default_description?: string | null;
            /** Default Image Id */
            default_image_id?: string | null;
            /** Default Title */
            default_title?: string | null;
            /** Organization Logo Id */
            organization_logo_id?: string | null;
            /**
             * Title Template
             * @default %s | Diyneco
             */
            title_template: string;
        };
        /** Sitemap */
        Sitemap: {
            /** Data */
            data: components["schemas"]["SitemapEntry"][];
        };
        /** SitemapEntry */
        SitemapEntry: {
            /** Alternates */
            alternates: components["schemas"]["Alternate"][];
            /** Kind */
            kind: string;
            /** Locale */
            locale: string;
            /** Path */
            path: string;
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
        };
        /** SocialLink */
        SocialLink: {
            /**
             * Network
             * @enum {string}
             */
            network: "linkedin" | "facebook" | "instagram" | "x" | "youtube" | "tiktok";
            /** Url */
            url: string;
        };
        /** SoldOutChange */
        SoldOutChange: {
            /** Available */
            available: boolean;
        };
        /** Split */
        Split: {
            /** Body */
            body: string;
            cta?: components["schemas"]["Cta"] | null;
            /** Heading */
            heading: string;
            /** Image Id */
            image_id?: string | null;
            /**
             * Image Side
             * @default right
             * @enum {string}
             */
            image_side: "left" | "right";
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "split";
        };
        /**
         * StaffCodeLoginRequest
         * @description Room-service sign-in (D82): Hotel ID, the member's 8-digit staff code and their PIN.
         */
        StaffCodeLoginRequest: {
            /** Hotel Code */
            hotel_code: string;
            /** Pin */
            pin: string;
            /** Staff Code */
            staff_code: string;
        };
        /** StaffCodeOut */
        StaffCodeOut: {
            /** Hotel Code */
            hotel_code: string;
            /**
             * Staff Code
             * @description Shown once. Issuing again replaces it.
             */
            staff_code: string;
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
            /** Has Staff Code */
            has_staff_code: boolean;
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
        /** StaffRequestCreate */
        StaffRequestCreate: {
            /** Due At */
            due_at?: string | null;
            /**
             * Kind
             * @enum {string}
             */
            kind: "towels" | "toiletries" | "pillows" | "cleaning" | "turndown" | "maintenance" | "wake_up" | "late_checkout" | "luggage" | "other";
            /** Note */
            note?: string | null;
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
        /** StandardLayout */
        StandardLayout: {
            /** Categories */
            categories: components["schemas"]["CategoryOut"][];
            /** Created Categories */
            created_categories: string[];
            /** Created Stations */
            created_stations: string[];
            /** Stations */
            stations: components["schemas"]["StationOut"][];
        };
        /** StatItem */
        StatItem: {
            /** Label */
            label: string;
            /** Value */
            value: string;
        };
        /** StatementInvoice */
        StatementInvoice: {
            balance: components["schemas"]["SignedMoney"];
            /** Currency */
            currency: string;
            /** Due On */
            due_on: string | null;
            /**
             * Hotel Id
             * Format: uuid
             */
            hotel_id: string;
            /** Hotel Name */
            hotel_name: string;
            /**
             * Invoice Id
             * Format: uuid
             */
            invoice_id: string;
            /** Issued At */
            issued_at: string | null;
            /** Number */
            number: string | null;
            /** Status */
            status: string;
            total: components["schemas"]["SignedMoney"];
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
        /** Stats */
        Stats: {
            /** Heading */
            heading?: string | null;
            /** Items */
            items: components["schemas"]["StatItem"][];
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "stats";
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
        /** StepItem */
        StepItem: {
            /** Body */
            body: string;
            /** Title */
            title: string;
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
        /** Steps */
        Steps: {
            /** Heading */
            heading?: string | null;
            /** Items */
            items: components["schemas"]["StepItem"][];
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "steps";
        };
        /** SubjectScore */
        SubjectScore: {
            /** Average */
            average: number | null;
            /** Ratings */
            ratings: number;
            /**
             * Subject
             * @enum {string}
             */
            subject: "order" | "request" | "stay";
        };
        /** SubscribeOut */
        SubscribeOut: {
            invoice: components["schemas"]["SubscriptionInvoiceOut"];
            subscription: components["schemas"]["HotelSubscription"];
        };
        /**
         * SubscribeRequest
         * @description Prices are computed on the server; the hotel only chooses and accepts the terms.
         */
        SubscribeRequest: {
            /**
             * Accept Terms
             * @constant
             */
            accept_terms: true;
            /**
             * Interval
             * @enum {string}
             */
            interval: "month" | "quarter" | "year";
            /** Plan Code */
            plan_code: string;
        };
        /** SubscriptionInvoiceList */
        SubscriptionInvoiceList: {
            /** Data */
            data: components["schemas"]["SubscriptionInvoiceOut"][];
        };
        /** SubscriptionInvoiceOut */
        SubscriptionInvoiceOut: {
            balance: components["schemas"]["SignedMoney"];
            /** Buyer */
            buyer: {
                [key: string]: unknown;
            };
            credited: components["schemas"]["SignedMoney"];
            /** Credits Invoice Id */
            credits_invoice_id: string | null;
            /** Credits Number */
            credits_number: string | null;
            /** Currency */
            currency: string;
            /** Due On */
            due_on: string | null;
            /** Has Pdf */
            has_pdf: boolean;
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
            /** Is Tax Invoice */
            is_tax_invoice: boolean;
            /** Issued At */
            issued_at: string | null;
            /**
             * Kind
             * @enum {string}
             */
            kind: "invoice" | "credit_note";
            /** Lines */
            lines: components["schemas"]["InvoiceLineOut"][];
            /** Notes */
            notes: string | null;
            /** Number */
            number: string | null;
            paid: components["schemas"]["SignedMoney"];
            /** Period End */
            period_end: string | null;
            /** Period Start */
            period_start: string | null;
            /**
             * Purpose
             * @enum {string}
             */
            purpose: "manual" | "initial" | "renewal" | "proration" | "credit";
            /** Seller */
            seller: {
                [key: string]: unknown;
            };
            /**
             * Status
             * @enum {string}
             */
            status: "draft" | "issued" | "partially_paid" | "paid" | "overdue" | "void" | "credited";
            subtotal: components["schemas"]["SignedMoney"];
            tax: components["schemas"]["SignedMoney"];
            /** Tax Name */
            tax_name: string | null;
            /** Tax Rate Bp */
            tax_rate_bp: number | null;
            total: components["schemas"]["SignedMoney"];
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
            plan: components["schemas"]["app__schemas__plans__PlanOut"] | null;
            /** Renews On */
            renews_on: string | null;
            /**
             * Starts On
             * Format: date
             */
            starts_on: string;
            /** Status */
            status: string;
            /** Trial Ends On */
            trial_ends_on?: string | null;
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
            status: "trial" | "active" | "past_due" | "suspended" | "cancelled";
        };
        /** SummaryCurrency */
        SummaryCurrency: {
            arr: components["schemas"]["SignedMoney"];
            collected: components["schemas"]["SignedMoney"];
            credited: components["schemas"]["SignedMoney"];
            /** Currency */
            currency: string;
            invoiced: components["schemas"]["SignedMoney"];
            mrr: components["schemas"]["SignedMoney"];
            net_collected: components["schemas"]["SignedMoney"];
            outstanding: components["schemas"]["SignedMoney"];
            overdue: components["schemas"]["SignedMoney"];
            /** Overdue Invoices */
            overdue_invoices: number;
            refunded: components["schemas"]["SignedMoney"];
            test_collected: components["schemas"]["SignedMoney"];
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
        /** TaxRateCreate */
        TaxRateCreate: {
            /** Country */
            country: string;
            /**
             * Effective From
             * Format: date
             */
            effective_from: string;
            /** Rate Bp */
            rate_bp: number;
            /** Reason */
            reason: string;
            /** Tax Name */
            tax_name: string;
        };
        /** TaxRateList */
        TaxRateList: {
            /** Data */
            data: components["schemas"]["TaxRateOut"][];
        };
        /** TaxRateOut */
        TaxRateOut: {
            /**
             * Category
             * @enum {string}
             */
            category: "standard" | "zero_rated" | "exempt";
            /** Country */
            country: string;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /**
             * Effective From
             * Format: date
             */
            effective_from: string;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** In Force */
            in_force: boolean;
            /** Rate Bp */
            rate_bp: number;
            /** Reason */
            reason: string;
            /** Scheduled */
            scheduled: boolean;
            /** Tax Name */
            tax_name: string;
        };
        /** TaxToday */
        TaxToday: {
            /** Charged */
            charged: boolean;
            /** Rate Bp */
            rate_bp: number | null;
            /** Tax Name */
            tax_name: string | null;
        };
        /** Testimonial */
        Testimonial: {
            /** Hotel */
            hotel?: string | null;
            /** Name */
            name: string;
            /** Quote */
            quote: string;
            /** Role */
            role?: string | null;
        };
        /** Testimonials */
        Testimonials: {
            /** Heading */
            heading?: string | null;
            /** Items */
            items: components["schemas"]["Testimonial"][];
            /**
             * @description discriminator enum property added by openapi-typescript
             * @enum {string}
             */
            type: "testimonials";
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
        /** TrialGrant */
        TrialGrant: {
            /** Days */
            days: number;
            /** Reason */
            reason: string;
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
        /** Verification */
        Verification: {
            /** Bing */
            bing?: string | null;
            /** Google */
            google?: string | null;
        };
        /**
         * VerifyEmailCodeRequest
         * @description The 6-digit code emailed at sign-up (D84).
         */
        VerifyEmailCodeRequest: {
            /** Code */
            code: string;
            /** Email */
            email: string;
        };
        /** VerifyEmailRequest */
        VerifyEmailRequest: {
            /** Token */
            token: string;
        };
        /** VoidRequest */
        VoidRequest: {
            /** Reason */
            reason: string;
        };
        /** VoidedItemOut */
        VoidedItemOut: {
            /**
             * Id
             * Format: uuid
             */
            id: string;
            line_total: components["schemas"]["Money"];
            /** Name */
            name: string;
            /** Quantity */
            quantity: number;
            /** Reason */
            reason: string;
            /** Voided At */
            voided_at: string | null;
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
        /** WebhookAck */
        WebhookAck: {
            /** Status */
            status: string;
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
        /** WebhookEventList */
        WebhookEventList: {
            /** Data */
            data: components["schemas"]["WebhookEventRow"][];
        };
        /** WebhookEventRow */
        WebhookEventRow: {
            /** Error */
            error: string | null;
            /** Event Id */
            event_id: string;
            /** Event Type */
            event_type: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Outcome */
            outcome: string | null;
            /** Processed At */
            processed_at: string | null;
            /** Provider */
            provider: string;
            /**
             * Received At
             * Format: date-time
             */
            received_at: string;
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
        /** CheckoutOut */
        app__schemas__billing__CheckoutOut: {
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
        /** Address */
        app__schemas__company__Address: {
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
        /** Address */
        app__schemas__hotel__Address: {
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
            /** Province Code */
            province_code?: string | null;
        };
        /** PlanOut */
        app__schemas__hotel__PlanOut: {
            /** Code */
            code: string | null;
            /** Name */
            name: string | null;
            /** Subscription Status */
            subscription_status: string;
        };
        /** SettingsOut */
        app__schemas__hotel__SettingsOut: {
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
            /** Locale */
            locale: string;
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
            /** Tax Label */
            tax_label: string;
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
        /** QuoteLine */
        app__schemas__orders__QuoteLine: {
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
        /** QuoteRequest */
        app__schemas__orders__QuoteRequest: {
            /** Lines */
            lines: components["schemas"]["CartLine"][];
        };
        /** PlanOut */
        app__schemas__plans__PlanOut: {
            /** Archived At */
            archived_at: string | null;
            /** Can Downgrade */
            can_downgrade: boolean;
            /** Can Upgrade */
            can_upgrade: boolean;
            /** Code */
            code: string;
            /** Currency */
            currency: string;
            /** Description */
            description: string | null;
            /** Display Order */
            display_order: number;
            /** Features */
            features: {
                [key: string]: boolean;
            };
            /** Highlights */
            highlights: string[];
            /** History */
            history: components["schemas"]["PriceOut"][];
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /** Limits */
            limits: {
                [key: string]: number;
            };
            /** Name */
            name: string;
            /** Overage Policy */
            overage_policy: string | null;
            /** Prices */
            prices: {
                [key: string]: components["schemas"]["PriceOut"];
            };
            /** Promo Discount Bp */
            promo_discount_bp: number;
            /** Promo Ends On */
            promo_ends_on: string | null;
            /** Published At */
            published_at: string | null;
            /** Recommended */
            recommended: boolean;
            /** Scheduled */
            scheduled: components["schemas"]["PriceOut"][];
            setup_fee: components["schemas"]["SignedMoney"];
            /** Short Description */
            short_description: string | null;
            /**
             * Status
             * @enum {string}
             */
            status: "draft" | "published" | "archived";
            /** Support Level */
            support_level: string | null;
            /**
             * Tax Treatment
             * @enum {string}
             */
            tax_treatment: "exclusive" | "inclusive";
            /** Trial Days */
            trial_days: number;
            /** Version */
            version: number;
        };
        /** AnalyticsDay */
        app__schemas__reports__AnalyticsDay: {
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
        /** CancelRequest */
        app__schemas__reports__CancelRequest: {
            /** Reason */
            reason: string;
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
        /** QuoteLine */
        app__schemas__reports__QuoteLine: {
            /** Amount Minor */
            amount_minor: number;
            /** Code */
            code: string;
            /** Description */
            description: string;
            /** Discount Minor */
            discount_minor: number;
            /** Tax Minor */
            tax_minor: number;
            /** Total Minor */
            total_minor: number;
        };
        /** QuoteRequest */
        app__schemas__reports__QuoteRequest: {
            /**
             * Interval
             * @enum {string}
             */
            interval: "month" | "quarter" | "year";
            /** Plan Code */
            plan_code: string;
        };
        /** CancelRequest */
        app__schemas__requests__CancelRequest: {
            /** Reason */
            reason?: string | null;
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
        /** PaymentList */
        app__schemas__room_service__PaymentList: {
            /** Data */
            data: components["schemas"]["app__schemas__room_service__PaymentOut"][];
            /** Next Cursor */
            next_cursor?: string | null;
        };
        /** PaymentOut */
        app__schemas__room_service__PaymentOut: {
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
        /** AnalyticsDay */
        app__schemas__site__AnalyticsDay: {
            /**
             * Day
             * Format: date
             */
            day: string;
            /** Views */
            views: number;
            /** Visitors */
            visitors: number;
        };
        /** SettingsOut */
        app__schemas__site__SettingsOut: {
            /** Analytics */
            analytics: {
                [key: string]: unknown;
            };
            /** Base Url */
            base_url: string;
            /** Contact */
            contact: {
                [key: string]: unknown;
            };
            /** Default Locale */
            default_locale: string;
            /** Footer */
            footer: {
                [key: string]: unknown;
            };
            /** Lead Email */
            lead_email: string;
            /** Locales */
            locales: string[];
            /** Navigation */
            navigation: {
                [key: string]: unknown;
            }[];
            /** Seo */
            seo: {
                [key: string]: unknown;
            };
            /** Site Name */
            site_name: string;
            /** Social */
            social: {
                [key: string]: unknown;
            }[];
            /**
             * Updated At
             * Format: date-time
             */
            updated_at: string;
            /** Verification */
            verification: {
                [key: string]: unknown;
            };
        };
        /** CheckoutOut */
        app__schemas__sub_payments__CheckoutOut: {
            amount: components["schemas"]["SignedMoney"];
            /** Checkout Url */
            checkout_url: string;
            /** Completed At */
            completed_at: string | null;
            /**
             * Created At
             * Format: date-time
             */
            created_at: string;
            /** Failure Reason */
            failure_reason: string | null;
            /**
             * Id
             * Format: uuid
             */
            id: string;
            /**
             * Invoice Id
             * Format: uuid
             */
            invoice_id: string;
            /** Provider */
            provider: string;
            /** Provider Label */
            provider_label: string;
            /**
             * Status
             * @enum {string}
             */
            status: "pending" | "succeeded" | "failed" | "cancelled" | "expired";
            /** Test Mode */
            test_mode: boolean;
        };
        /** PaymentList */
        app__schemas__sub_payments__PaymentList: {
            /** Data */
            data: components["schemas"]["app__schemas__sub_payments__PaymentOut"][];
        };
        /** PaymentOut */
        app__schemas__sub_payments__PaymentOut: {
            amount: components["schemas"]["SignedMoney"];
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
             * Invoice Id
             * Format: uuid
             */
            invoice_id: string;
            /** Invoice Number */
            invoice_number: string | null;
            /** Method */
            method: string;
            /** Notes */
            notes?: string | null;
            /** Provider */
            provider: string;
            /** Provider Payment Id */
            provider_payment_id?: string | null;
            /**
             * Received On
             * Format: date
             */
            received_on: string;
            /** Reconciled At */
            reconciled_at?: string | null;
            /** Reconciliation Note */
            reconciliation_note?: string | null;
            /** Reconciliation Status */
            reconciliation_status?: ("unreconciled" | "matched" | "disputed") | null;
            /** Reference */
            reference: string | null;
            refunded: components["schemas"]["SignedMoney"];
            /** Test Mode */
            test_mode: boolean;
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
                    "application/json": components["schemas"]["Analytics-Output"];
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
    get_billing_settings_api_v1_admin_billing_settings_get: {
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
                    "application/json": components["schemas"]["BillingSettingsOut"];
                };
            };
        };
    };
    put_billing_settings_api_v1_admin_billing_settings_put: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BillingSettingsPut"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BillingSettingsOut"];
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
    billing_invoices_api_v1_admin_billing_invoices_get: {
        parameters: {
            query?: {
                q?: string | null;
                status?: ("issued" | "partially_paid" | "paid" | "overdue" | "void" | "credited") | null;
                from?: string | null;
                to?: string | null;
                plan?: string | null;
                payment?: ("paid" | "unpaid" | "partial" | "overdue") | null;
                limit?: number;
                offset?: number;
                format?: "json" | "csv";
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
                    "application/json": components["schemas"]["AdminInvoiceList"];
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
    billing_payments_api_v1_admin_billing_payments_get: {
        parameters: {
            query?: {
                q?: string | null;
                reconciliation?: ("unreconciled" | "matched" | "disputed") | null;
                from?: string | null;
                to?: string | null;
                limit?: number;
                offset?: number;
                format?: "json" | "csv";
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
                    "application/json": components["schemas"]["AdminPaymentList"];
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
    billing_provider_api_v1_admin_billing_provider_get: {
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
                    "application/json": components["schemas"]["ProviderStatusOut"];
                };
            };
        };
    };
    billing_summary_api_v1_admin_billing_summary_get: {
        parameters: {
            query?: {
                from?: string | null;
                to?: string | null;
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
                    "application/json": components["schemas"]["BillingSummary"];
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
    billing_webhooks_api_v1_admin_billing_webhooks_get: {
        parameters: {
            query?: {
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
                    "application/json": components["schemas"]["WebhookEventList"];
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
    get_company_api_v1_admin_company_get: {
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
                    "application/json": components["schemas"]["CompanySettingsOut"];
                };
            };
        };
    };
    put_company_api_v1_admin_company_put: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CompanySettingsPut"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CompanySettingsOut"];
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
    start_logo_upload_api_v1_admin_company_logo_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CompanyLogoUpload"];
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
    list_countries_api_v1_admin_countries_get: {
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
                    "application/json": components["schemas"]["AdminCountryList"];
                };
            };
        };
    };
    put_country_api_v1_admin_countries__code__put: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                code: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CountryPut"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AdminCountryOut"];
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
    admin_list_api_v1_admin_hotels__hotel_id__invoices_get: {
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
                    "application/json": components["schemas"]["SubscriptionInvoiceList"];
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
    draft_api_v1_admin_hotels__hotel_id__invoices_post: {
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
                "application/json": components["schemas"]["DraftCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SubscriptionInvoiceOut"];
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
    credit_api_v1_admin_hotels__hotel_id__invoices__invoice_id__credit_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                hotel_id: string;
                invoice_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["CreditRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SubscriptionInvoiceOut"];
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
    issue_api_v1_admin_hotels__hotel_id__invoices__invoice_id__issue_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                hotel_id: string;
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
                    "application/json": components["schemas"]["SubscriptionInvoiceOut"];
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
    admin_pdf_api_v1_admin_hotels__hotel_id__invoices__invoice_id__pdf_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                hotel_id: string;
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
                    "application/json": components["schemas"]["PdfLink"];
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
    resend_api_v1_admin_hotels__hotel_id__invoices__invoice_id__send_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                hotel_id: string;
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
                    "application/json": components["schemas"]["SentOut"];
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
    void_api_v1_admin_hotels__hotel_id__invoices__invoice_id__void_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                hotel_id: string;
                invoice_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["VoidRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SubscriptionInvoiceOut"];
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
    hotel_payments_api_v1_admin_hotels__hotel_id__payments_get: {
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
                    "application/json": components["schemas"]["app__schemas__sub_payments__PaymentList"];
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
    record_payment_api_v1_admin_hotels__hotel_id__payments_post: {
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
                "application/json": components["schemas"]["ManualPayment"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["app__schemas__sub_payments__PaymentOut"];
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
    reconcile_payment_api_v1_admin_hotels__hotel_id__payments__payment_id__reconcile_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                hotel_id: string;
                payment_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ReconcileRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["app__schemas__sub_payments__PaymentOut"];
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
    refund_payment_api_v1_admin_hotels__hotel_id__payments__payment_id__refund_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                hotel_id: string;
                payment_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RefundRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RefundOut"];
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
    grant_trial_api_v1_admin_hotels__hotel_id__trial_post: {
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
                "application/json": components["schemas"]["TrialGrant"];
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
    insights_api_v1_admin_insights_get: {
        parameters: {
            query?: {
                since?: string | null;
                until?: string | null;
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
                    "application/json": components["schemas"]["InsightsOut"];
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
    admin_list_api_v1_admin_legal_documents_get: {
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
                    "application/json": components["schemas"]["LegalDocumentList"];
                };
            };
        };
    };
    create_draft_api_v1_admin_legal_documents_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LegalDraftCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LegalDocumentOut"];
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
    delete_draft_api_v1_admin_legal_documents__document_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                document_id: string;
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
    update_draft_api_v1_admin_legal_documents__document_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                document_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LegalDraftPatch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LegalDocumentOut"];
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
    publish_api_v1_admin_legal_documents__document_id__publish_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                document_id: string;
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
                    "application/json": components["schemas"]["LegalDocumentOut"];
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
    owners_api_v1_admin_owners_get: {
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
                    "application/json": components["schemas"]["OwnerList"];
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
                    "application/json": components["schemas"]["app__schemas__plans__PlanOut"];
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
                    "application/json": components["schemas"]["app__schemas__plans__PlanOut"];
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
    archive_plan_api_v1_admin_plans__plan_id__archive_post: {
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
                "application/json": components["schemas"]["PlanStatusChange"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["app__schemas__plans__PlanOut"];
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
    preview_plan_api_v1_admin_plans__plan_id__preview_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                plan_id: string;
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
                    "application/json": components["schemas"]["PublicPlan"];
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
    add_price_api_v1_admin_plans__plan_id__prices_post: {
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
                "application/json": components["schemas"]["PriceCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["app__schemas__plans__PlanOut"];
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
    withdraw_price_api_v1_admin_plans__plan_id__prices__price_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                plan_id: string;
                price_id: string;
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
                    "application/json": components["schemas"]["app__schemas__plans__PlanOut"];
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
    publish_plan_api_v1_admin_plans__plan_id__publish_post: {
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
                "application/json": components["schemas"]["PlanStatusChange"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["app__schemas__plans__PlanOut"];
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
    restore_plan_api_v1_admin_plans__plan_id__restore_post: {
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
                "application/json": components["schemas"]["PlanStatusChange"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["app__schemas__plans__PlanOut"];
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
    analytics_api_v1_admin_site_analytics_get: {
        parameters: {
            query?: {
                since?: string | null;
                until?: string | null;
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
                    "application/json": components["schemas"]["AnalyticsOut"];
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
    list_entries_api_v1_admin_site_entries_get: {
        parameters: {
            query?: {
                kind?: ("page" | "post") | null;
                locale?: string | null;
                q?: string | null;
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
                    "application/json": components["schemas"]["EntryList"];
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
    create_entry_api_v1_admin_site_entries_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EntryCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EntryOut"];
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
    get_entry_api_v1_admin_site_entries__entry_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                entry_id: string;
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
                    "application/json": components["schemas"]["EntryOut"];
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
    delete_entry_api_v1_admin_site_entries__entry_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                entry_id: string;
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
    update_entry_api_v1_admin_site_entries__entry_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                entry_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["EntryPatch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["EntryOut"];
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
    preview_link_api_v1_admin_site_entries__entry_id__preview_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                entry_id: string;
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
                    "application/json": components["schemas"]["PreviewOut"];
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
    publish_entry_api_v1_admin_site_entries__entry_id__publish_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                entry_id: string;
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
                    "application/json": components["schemas"]["EntryOut"];
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
    unpublish_entry_api_v1_admin_site_entries__entry_id__unpublish_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                entry_id: string;
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
                    "application/json": components["schemas"]["EntryOut"];
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
    versions_api_v1_admin_site_entries__entry_id__versions_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                entry_id: string;
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
                    "application/json": components["schemas"]["EntryVersionList"];
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
    restore_version_api_v1_admin_site_entries__entry_id__versions__version__restore_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                entry_id: string;
                version: number;
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
                    "application/json": components["schemas"]["EntryOut"];
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
    list_leads_api_v1_admin_site_leads_get: {
        parameters: {
            query?: {
                status?: ("new" | "contacted" | "qualified" | "closed" | "spam") | null;
                kind?: ("demo" | "contact") | null;
                before?: string | null;
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
                    "application/json": components["schemas"]["LeadList"];
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
    erase_lead_api_v1_admin_site_leads__lead_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                lead_id: string;
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
    update_lead_api_v1_admin_site_leads__lead_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                lead_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LeadPatch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LeadOut"];
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
    list_media_api_v1_admin_site_media_get: {
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
                    "application/json": components["schemas"]["MediaList"];
                };
            };
        };
    };
    upload_media_api_v1_admin_site_media_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MediaUpload"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MediaOut"];
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
    delete_media_api_v1_admin_site_media__media_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                media_id: string;
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
    update_media_api_v1_admin_site_media__media_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                media_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MediaPatch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MediaOut"];
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
    list_redirects_api_v1_admin_site_redirects_get: {
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
                    "application/json": components["schemas"]["RedirectList"];
                };
            };
        };
    };
    create_redirect_api_v1_admin_site_redirects_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["RedirectIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RedirectOut"];
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
    delete_redirect_api_v1_admin_site_redirects__redirect_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                redirect_id: string;
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
    get_settings_api_v1_admin_site_settings_get: {
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
                    "application/json": components["schemas"]["app__schemas__site__SettingsOut"];
                };
            };
        };
    };
    put_settings_api_v1_admin_site_settings_put: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SettingsIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["app__schemas__site__SettingsOut"];
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
    list_staff_api_v1_admin_staff_get: {
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
                    "application/json": components["schemas"]["PlatformStaffList"];
                };
            };
        };
    };
    invite_api_v1_admin_staff_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PlatformStaffInvite"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PlatformStaffOut"];
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
    list_roles_api_v1_admin_staff_roles_get: {
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
                    "application/json": components["schemas"]["PlatformRoleList"];
                };
            };
        };
    };
    deactivate_api_v1_admin_staff__user_id__deactivate_post: {
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
                    "application/json": components["schemas"]["PlatformStaffOut"];
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
    reactivate_api_v1_admin_staff__user_id__reactivate_post: {
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
                    "application/json": components["schemas"]["PlatformStaffOut"];
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
    resend_invitation_api_v1_admin_staff__user_id__resend_invitation_post: {
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
                    "application/json": components["schemas"]["PlatformStaffOut"];
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
    change_roles_api_v1_admin_staff__user_id__roles_put: {
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
                "application/json": components["schemas"]["PlatformStaffRoles"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PlatformStaffOut"];
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
    list_tax_rates_api_v1_admin_tax_rates_get: {
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
                    "application/json": components["schemas"]["TaxRateList"];
                };
            };
        };
    };
    schedule_tax_rate_api_v1_admin_tax_rates_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["TaxRateCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["TaxRateList"];
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
    withdraw_tax_rate_api_v1_admin_tax_rates__rate_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                rate_id: string;
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
                    "application/json": components["schemas"]["TaxRateList"];
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
    resend_email_code_api_v1_auth_email_resend_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ResendEmailCodeRequest"];
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
    verify_email_code_api_v1_auth_email_verify_code_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["VerifyEmailCodeRequest"];
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
    accept_invitation_api_v1_auth_platform_invitations_accept_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PlatformInviteAccept"];
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
    platform_login_api_v1_auth_platform_login_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PlatformLoginRequest"];
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
    staff_code_login_api_v1_auth_staff_code_login_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["StaffCodeLoginRequest"];
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
    stitch_webhook_api_v1_billing_webhooks_stitch_post: {
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
                    "application/json": components["schemas"]["WebhookAck"];
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
    countries_api_v1_countries_get: {
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
                    "application/json": components["schemas"]["CountryList"];
                };
            };
        };
    };
    country_regions_api_v1_countries__code__regions_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                code: string;
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
                    "application/json": components["schemas"]["RegionList"];
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
    my_feedback_api_v1_guest_feedback_get: {
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
                    "application/json": components["schemas"]["FeedbackList"];
                };
            };
        };
    };
    give_feedback_api_v1_guest_feedback_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["FeedbackCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["FeedbackOut"];
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
    guest_documents_api_v1_guest_legal_get: {
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
                    "application/json": components["schemas"]["LegalDocumentList"];
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
                "application/json": components["schemas"]["app__schemas__orders__QuoteRequest"];
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
    my_requests_api_v1_guest_requests_get: {
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
                    "application/json": components["schemas"]["GuestRequestList"];
                };
            };
        };
    };
    ask_api_v1_guest_requests_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["GuestRequestCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GuestRequestOut"];
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
    cancel_request_api_v1_guest_requests__request_id__cancel_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                request_id: string;
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
                    "application/json": components["schemas"]["GuestRequestOut"];
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
                    "application/json": components["schemas"]["app__schemas__hotel__SettingsOut"];
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
                    "application/json": components["schemas"]["app__schemas__hotel__SettingsOut"];
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
    add_property_api_v1_hotels_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AddPropertyRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AddPropertyOut"];
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
    kitchen_menu_api_v1_kitchen_menu_get: {
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
                    "application/json": components["schemas"]["KitchenMenu"];
                };
            };
        };
    };
    kitchen_sold_out_api_v1_kitchen_menu_items__item_id__availability_post: {
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
                "application/json": components["schemas"]["SoldOutChange"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["KitchenMenuItem"];
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
    accept_api_v1_legal_accept_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LegalAccept"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["LegalDocumentList"];
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
    documents_api_v1_legal_documents_get: {
        parameters: {
            query?: {
                country?: string | null;
                audience?: "merchant" | "guest" | "all";
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
                    "application/json": components["schemas"]["LegalDocumentList"];
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
    document_api_v1_legal_documents__document_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                document_id: string;
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
                    "application/json": components["schemas"]["LegalDocumentOut"];
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
    pending_api_v1_legal_pending_get: {
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
                    "application/json": components["schemas"]["LegalDocumentList"];
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
    route_category_api_v1_menu_categories__category_id__station_post: {
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
                "application/json": components["schemas"]["CategoryRoute"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["CategoryRouted"];
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
    delete_group_api_v1_menu_modifier_groups__group_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                group_id: string;
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
    patch_group_api_v1_menu_modifier_groups__group_id__patch: {
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
                "application/json": components["schemas"]["ModifierGroupPatch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
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
    delete_option_api_v1_menu_modifier_options__option_id__delete: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                option_id: string;
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
    patch_option_api_v1_menu_modifier_options__option_id__patch: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                option_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["ModifierOptionPatch"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
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
    standard_layout_api_v1_menu_standard_layout_post: {
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
                    "application/json": components["schemas"]["StandardLayout"];
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
    void_item_api_v1_orders__order_id__items__item_id__void_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                order_id: string;
                item_id: string;
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
                    "application/json": components["schemas"]["app__schemas__room_service__PaymentList"];
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
                    "application/json": components["schemas"]["app__schemas__room_service__PaymentOut"];
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
    public_plans_api_v1_plans_get: {
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
                    "application/json": components["schemas"]["PublicPlanList"];
                };
            };
        };
    };
    portfolio_api_v1_portfolio_get: {
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
                    "application/json": components["schemas"]["PortfolioOut"];
                };
            };
        };
    };
    group_statement_api_v1_portfolio_billing_get: {
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
                    "application/json": components["schemas"]["GroupStatement"];
                };
            };
        };
    };
    invite_to_properties_api_v1_portfolio_invitations_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["MultiInvite"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["MultiInviteList"];
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
    pay_all_api_v1_portfolio_payments_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["GroupPayRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GroupCheckoutOut"];
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
    check_group_payment_api_v1_portfolio_payments__group_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                group_id: string;
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
                    "application/json": components["schemas"]["GroupPaymentOut"];
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
    group_sandbox_api_v1_portfolio_payments__group_id__sandbox_post: {
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
                "application/json": components["schemas"]["SandboxOutcome"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["GroupPaymentOut"];
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
    guest_feedback_api_v1_reports_feedback_get: {
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
                    "application/json": components["schemas"]["FeedbackReport"];
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
    service_requests_api_v1_reports_requests_get: {
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
                    "application/json": components["schemas"]["RequestsReport"];
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
    list_requests_api_v1_requests_get: {
        parameters: {
            query?: {
                scope?: "open" | "mine" | "recent";
                kind?: ("towels" | "toiletries" | "pillows" | "cleaning" | "turndown" | "maintenance" | "wake_up" | "late_checkout" | "luggage" | "other") | null;
                room_id?: string | null;
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
                    "application/json": components["schemas"]["RequestList"];
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
    log_request_api_v1_requests_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["StaffRequestCreate"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RequestOut"];
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
    acknowledge_api_v1_requests__request_id__acknowledge_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                request_id: string;
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
                    "application/json": components["schemas"]["RequestOut"];
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
    assign_api_v1_requests__request_id__assign_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                request_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["AssignRequestTo"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RequestOut"];
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
    cancel_api_v1_requests__request_id__cancel_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                request_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["app__schemas__requests__CancelRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["RequestOut"];
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
    done_api_v1_requests__request_id__done_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                request_id: string;
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
                    "application/json": components["schemas"]["RequestOut"];
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
    start_api_v1_requests__request_id__start_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                request_id: string;
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
                    "application/json": components["schemas"]["RequestOut"];
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
    public_entry_api_v1_site_entry_get: {
        parameters: {
            query: {
                kind: "page" | "post";
                locale: string;
                slug?: string;
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
                    "application/json": components["schemas"]["PublicEntry"];
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
    create_lead_api_v1_site_leads_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["LeadIn"];
            };
        };
        responses: {
            /** @description Successful Response */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        [key: string]: string;
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
    media_api_v1_site_media__media_id___width__webp_get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                media_id: string;
                width: number;
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
                    "application/json": unknown;
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
    public_posts_api_v1_site_posts_get: {
        parameters: {
            query: {
                locale: string;
                limit?: number;
                before?: string | null;
                tag?: string | null;
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
                    "application/json": components["schemas"]["PostCardList"];
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
    preview_entry_api_v1_site_preview_get: {
        parameters: {
            query: {
                token: string;
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
                    "application/json": components["schemas"]["PublicEntry"];
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
    public_redirects_api_v1_site_redirects_get: {
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
                    "application/json": components["schemas"]["RedirectList"];
                };
            };
        };
    };
    public_settings_api_v1_site_settings_get: {
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
                    "application/json": components["schemas"]["PublicSettings"];
                };
            };
        };
    };
    sitemap_api_v1_site_sitemap_get: {
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
                    "application/json": components["schemas"]["Sitemap"];
                };
            };
        };
    };
    record_view_api_v1_site_views_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PageViewIn"];
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
    issue_staff_code_api_v1_staff__user_id__staff_code_post: {
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
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["StaffCodeOut"];
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
    remove_staff_code_api_v1_staff__user_id__staff_code_delete: {
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
                    "application/json": components["schemas"]["app__schemas__billing__CheckoutOut"];
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
    get_billing_contact_api_v1_subscription_billing_contact_get: {
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
                    "application/json": components["schemas"]["BillingContactOut"];
                };
            };
        };
    };
    put_billing_contact_api_v1_subscription_billing_contact_put: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["BillingContactPut"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["BillingContactOut"];
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
    cancel_subscription_api_v1_subscription_cancel_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["app__schemas__reports__CancelRequest"];
            };
        };
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
    change_plan_api_v1_subscription_change_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["PlanChangeRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["PlanChangeOut"];
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
    my_invoices_api_v1_subscription_invoices_get: {
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
                    "application/json": components["schemas"]["SubscriptionInvoiceList"];
                };
            };
        };
    };
    my_invoice_api_v1_subscription_invoices__invoice_id__get: {
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
                    "application/json": components["schemas"]["SubscriptionInvoiceOut"];
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
    pay_invoice_api_v1_subscription_invoices__invoice_id__pay_post: {
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
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["app__schemas__sub_payments__CheckoutOut"];
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
    my_invoice_pdf_api_v1_subscription_invoices__invoice_id__pdf_get: {
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
                    "application/json": components["schemas"]["PdfLink"];
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
    my_attempts_api_v1_subscription_payment_attempts_get: {
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
                    "application/json": components["schemas"]["AttemptList"];
                };
            };
        };
    };
    check_attempt_api_v1_subscription_payment_attempts__attempt_id__get: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                attempt_id: string;
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
                    "application/json": components["schemas"]["AttemptOut"];
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
    sandbox_outcome_api_v1_subscription_payment_attempts__attempt_id__sandbox_post: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                attempt_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SandboxOutcome"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AttemptOut"];
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
    payment_options_api_v1_subscription_payment_options_get: {
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
                    "application/json": components["schemas"]["PaymentOptions"];
                };
            };
        };
    };
    my_payments_api_v1_subscription_payments_get: {
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
                    "application/json": components["schemas"]["app__schemas__sub_payments__PaymentList"];
                };
            };
        };
    };
    subscription_quote_api_v1_subscription_quote_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["app__schemas__reports__QuoteRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["QuoteOut"];
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
    resume_subscription_api_v1_subscription_resume_post: {
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
    subscribe_api_v1_subscription_subscribe_post: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": components["schemas"]["SubscribeRequest"];
            };
        };
        responses: {
            /** @description Successful Response */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SubscribeOut"];
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
