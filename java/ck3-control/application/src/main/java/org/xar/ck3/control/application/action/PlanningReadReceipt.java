package org.xar.ck3.control.application.action;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;

/** Retains the original native read; only the registered domain decoder may interpret its proof. */
public record PlanningReadReceipt(PlanningReadRequest request, String contractId, String requestId,
        PlanningReadGuard before, PlanningReadGuard after, NativeActionPort.AckReceived original,
        Optional<PlanningReadAdoption> adoption, ArchiveVersion archiveVersion) {
    /** Original storage version is explicit DATA so strict historical locators never drift to v2. */
    public enum ArchiveVersion { HISTORICAL_V1, CURRENT_V2, PHYSICAL_STATUS_V3 }
    public PlanningReadReceipt {
        Objects.requireNonNull(request); StrictJson.text(contractId); StrictJson.text(requestId);
        Objects.requireNonNull(before); Objects.requireNonNull(after); Objects.requireNonNull(original);
        adoption = Objects.requireNonNull(adoption);
        Objects.requireNonNull(archiveVersion);
        boolean physical = request.origin() instanceof CommandOrigin.PhysicalStatusOnly;
        StrictJson.require(physical == (archiveVersion == ArchiveVersion.PHYSICAL_STATUS_V3),
                "physical status requires its exact v3 read receipt and cannot alias historical or ordinary reads");
        if (physical) {
            StrictJson.require(contractId.equals(PhysicalStatusIdentity.CONTRACT_ID)
                    && request.operation().value().equals(PhysicalStatusIdentity.OPERATION)
                    && request.arguments().members().isEmpty() && adoption.isEmpty()
                    && before.guardMode() == ReadContract.GuardMode.STATUS_ONLY
                    && after.guardMode() == ReadContract.GuardMode.STATUS_ONLY,
                    "physical status receipt crossed its finite contract/operation/empty arguments or adopted ordinary history");
        }
        StrictJson.require(archiveVersion != ArchiveVersion.HISTORICAL_V1 || adoption.isEmpty(),
                "historical v1 read cannot carry later adoption provenance");
        StrictJson.require(original.nativeOk() && original.requestId().equals(requestId), "successful original query ACK with matching request identity required");
        StrictJson.require(request.origin().acceptsGuard(before.binding().origin())
                && before.binding().origin().acceptsGuard(after.binding().origin())
                && before.guardMode() == after.guardMode(), "query receipt crossed origin or source frame");
        StrictJson.require(request.source().equals(before.binding().source()) && request.source().equals(after.binding().source())
                && request.sessionId().equals(before.binding().sessionId()) && request.sessionId().equals(after.binding().sessionId())
                && request.operation().equals(before.binding().operation()) && request.operation().equals(after.binding().operation()), "query receipt binding drift");
        StrictJson.require(before.binding().connectionGeneration().equals(after.binding().connectionGeneration())
                && before.binding().authorityId().equals(after.binding().authorityId()), "query receipt crossed native connection or installed authority");
    }
    /** Current ordinary receipts have no late-read provenance; v1 readers set their explicit version. */
    public PlanningReadReceipt(PlanningReadRequest request, String contractId, String requestId,
            PlanningReadGuard before, PlanningReadGuard after, NativeActionPort.AckReceived original) {
        this(request, contractId, requestId, before, after, original, Optional.empty(), request.origin() instanceof CommandOrigin.PhysicalStatusOnly
                ? ArchiveVersion.PHYSICAL_STATUS_V3 : ArchiveVersion.CURRENT_V2);
    }
    public PlanningReadReceipt(PlanningReadRequest request, String contractId, String requestId,
            PlanningReadGuard before, PlanningReadGuard after, NativeActionPort.AckReceived original,
            Optional<PlanningReadAdoption> adoption) {
        this(request, contractId, requestId, before, after, original, adoption, request.origin() instanceof CommandOrigin.PhysicalStatusOnly
                ? ArchiveVersion.PHYSICAL_STATUS_V3 : ArchiveVersion.CURRENT_V2);
    }
}
