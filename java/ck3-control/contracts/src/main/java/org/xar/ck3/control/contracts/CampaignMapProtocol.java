package org.xar.ck3.control.contracts;

/** Stable metadata shared by the map producer and its existing HTTP adapter. */
public final class CampaignMapProtocol {
    public static final String PRODUCER = "java-quarkus-map-admission/v1";
    public static final String PRODUCER_VERSION = "0.1.0";
    public static final String IDENTITY_SCHEMA = "xar.java-map-admission-producer-identity/v1";
    public static final String ERROR_SCHEMA = "xar.java-contract-error/v1";
    public static final String PRODUCER_HEADER = "X-Xar-Producer";
    public static final String VERSION_HEADER = "X-Xar-Producer-Version";
    public static final String CONTRACT_HEADER = "X-Xar-Contract-Revision";

    private CampaignMapProtocol() { }

    public record ContractError(String schema, String status, String error) { }

    public record ProducerIdentity(String schema, String producer, String producer_version,
                                   String request_schema, String implementation, String maven_group_id,
                                   String maven_artifact_id, String maven_version) { }

    public static ProducerIdentity identity(String implementation) {
        return new ProducerIdentity(IDENTITY_SCHEMA, PRODUCER, PRODUCER_VERSION,
                CampaignMapComposeRequest.SCHEMA, StrictJson.text(implementation),
                "org.xar.ck3.control", "ck3-control-local-service", "0.1.0-SNAPSHOT");
    }

    public static ContractError rejected(String message) {
        return new ContractError(ERROR_SCHEMA, "rejected", StrictJson.text(message));
    }
}
