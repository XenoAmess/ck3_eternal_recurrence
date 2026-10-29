package org.xar.ck3.control.nativebridge.capabilities.publicmethods.driverregistry;

import java.io.IOException;
import java.util.Objects;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.family.CachedSuccession12004;
import org.xar.ck3.control.nativebridge.capabilities.family.CachedSuccessionService;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.driverregistry.DriverRegistryContract.*;

/** Calls the actual same-Root installed private READ; observation never implies succession eligibility or business credit. */
public final class DriverRegistryService {
    public record Definitions(ReadContract<CachedSuccession12004.Observation> cached, ExactRef decoderSource) {
        public Definitions {
            Objects.requireNonNull(cached); Objects.requireNonNull(decoderSource);
            StrictJson.require(cached.operation().equals(new OperationKey(CachedSuccession12004.STEP))
                    && cached.permissionMode() == ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE
                    && cached.wireProfile() == ReadContract.WireProfile.SNAPSHOT_REVISION_ONLY
                    && cached.permissionKey().equals(CachedSuccession12004.PERMISSION) && cached.hasPureReplay()
                    && decoderSource.bytes() > 0, "identical source-qualified cached-succession contract/decoder required");
        }
    }
    /** The Root source factory supplies the actual private admission; no default permissive qualifier exists. */
    public static Definitions definitions(ExactRef originalNativeSource, ExactRef actualDecoderSource,
            CachedSuccessionService.Admission qualifiedPrivateAdmission) {
        Objects.requireNonNull(qualifiedPrivateAdmission);
        var empty = (org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj)
                org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(new byte[]{'{', '}'});
        var contract = new ReadContract<CachedSuccession12004.Observation>("driver-public/actor-cached-succession12004",
                new OperationKey(CachedSuccession12004.STEP), java.util.Optional.empty(), CachedSuccession12004.PERMISSION,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE, ReadContract.WireProfile.SNAPSHOT_REVISION_ONLY,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP, originalNativeSource,
                (request, requestId) -> {
                    StrictJson.require(request.arguments().equals(empty), "cached succession accepts no selectors");
                    qualifiedPrivateAdmission.verify(request);
                    return new NativeRequest(CachedSuccession12004.STEP, java.util.Optional.empty(), new org.xar.ck3.control.application.action.RawJson(new byte[]{'{', '}'}));
                }, CachedSuccessionService::decode, CachedSuccessionService::decode);
        return new Definitions(contract, actualDecoderSource);
    }
    @FunctionalInterface public interface Current {
        PlanningReadResult<CachedSuccession12004.Observation> read(CachedRequest request) throws IOException, InterruptedException;
    }
    private final Definitions definitions;
    private final Current actual;
    public DriverRegistryService(Definitions sameDefinitions, Current actualCurrentRoot) {
        definitions = Objects.requireNonNull(sameDefinitions); actual = Objects.requireNonNull(actualCurrentRoot);
    }
    public CachedResponse queryCachedSuccession(CachedRequest request) throws IOException, InterruptedException {
        var result = actual.read(Objects.requireNonNull(request));
        if (result instanceof PlanningReadResult.Known<CachedSuccession12004.Observation> known) {
            StrictJson.require(known.receipt().contractId().equals(definitions.cached().contractId()) && known.originalReceipt().bytes() > 0
                    && known.receipt().request().before().frame().revision().equals(request.expectedRevision())
                    && known.value().equals(CachedSuccessionService.decode(known.receipt())), "public cached query lost its actual original read/frame");
            return new CachedResponse(known.value());
        }
        var unavailable = (PlanningReadResult.Unavailable<CachedSuccession12004.Observation>) result;
        throw new IOException("actual cached-succession read unavailable: " + unavailable.reason());
    }
}
