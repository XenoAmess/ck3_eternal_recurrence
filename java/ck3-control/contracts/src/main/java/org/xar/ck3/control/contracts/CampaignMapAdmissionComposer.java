package org.xar.ck3.control.contracts;

/** Production Java map producer. All input validation precedes constructing typed state. */
public final class CampaignMapAdmissionComposer {
    public static final String REQUEST_SCHEMA = CampaignMapComposeRequest.SCHEMA;
    private CampaignMapAdmissionComposer() { }

    public static byte[] compose(byte[] requestBody) {
        CampaignMapComposeRequest request = CampaignMapComposeRequest.fromBytes(requestBody);
        CampaignMapAdmission admission = new CampaignMapAdmission(request.machineId(), request.nativeLaunch(),
                request.recordingSessionId(), request.actualInitialFrame(), request.observedAtUtc());
        // Preserve the established Python-only numeric FILETIME and canonical receipt bytes.
        return CampaignMapAdmission.fromJson(admission.toJson()).toCanonicalBytes();
    }
}
