"use client";

import { ApiError, newIdempotencyKey } from "@diyneco/api-client";
import { type DeviceSetup, DeviceSetupForm } from "@diyneco/shared-ui";

import { API_URL, APP_VERSION } from "./config";
import { credential } from "./device";

/** First start (D82): the Hotel ID, an 8-digit setup code a manager creates in the Merchant
 * app (Devices) and that manager's PIN. */
export function PairScreen({ onPaired }: { onPaired: (stations: string[]) => void }) {
  const pair = async ({ hotelCode, code, pin }: DeviceSetup) => {
    const res = await fetch(`${API_URL}/api/v1/devices/pair`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Idempotency-Key": newIdempotencyKey() },
      body: JSON.stringify({
        hotel_code: hotelCode,
        code,
        pin,
        device_info: { os: navigator.platform || "browser", app_version: APP_VERSION },
      }),
    });
    const body = await res.json();
    if (!res.ok) throw new ApiError(res.status, body.error);
    if (body.kind !== "kitchen") {
      throw new ApiError(422, {
        code: "PAIRING_INVALID",
        message: "That code is for a guest tablet. Create a kitchen display code instead.",
        request_id: null,
        details: {},
      });
    }
    credential.set(body.device_credential);
    onPaired((body.stations as { name: string }[]).map((s) => s.name));
  };

  return (
    <div className="kds">
      <DeviceSetupForm
        title="Set up this display"
        intro="In the Merchant app, open Devices and add a kitchen display. Enter what it shows."
        submitLabel="Set up display"
        onSubmit={pair}
      />
    </div>
  );
}
