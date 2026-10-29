package org.xar.ck3.control.nativebridge.capabilities.diagnostics;

import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeObservationPort.TransportSession;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativeTransportDiagnostics;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/** Original bridge diagnostics DATA. None of these values advertises a gameplay capability or authorizes an action. */
public final class BridgeDiagnostics {
    private BridgeDiagnostics() { }
    public record Request() { }
    public enum RequiredInput {
        REJECTED_STATE_SNAPSHOT_COUNT, LAST_REJECTED_STATE_SNAPSHOT, SNAPSHOT_PUBLISH_DIAGNOSTIC_COUNT,
        TRANSPORT_REFUSAL, PENDING_DECLARATION_QUERY, FRONTEND_START_CAMPAIGN_ROOT_QUERY
    }
    /** Explicit original null is Optional.empty; an unavailable producer is MissingInputs, never an empty value. */
    public record Supplement(Optional<Obj> pendingDeclarationQuery, Optional<Obj> frontendStartCampaignRootQuery) {
        public Supplement {
            Objects.requireNonNull(pendingDeclarationQuery);Objects.requireNonNull(frontendStartCampaignRootQuery);
        }
    }
    public static Set<RequiredInput> supplementInputs(){return Set.of(RequiredInput.PENDING_DECLARATION_QUERY,RequiredInput.FRONTEND_START_CAMPAIGN_ROOT_QUERY);}
    /** Four fields come only from the actual Native lifetime producer, never from a generic supplement callback. */
    public static NativeTransportDiagnostics.Production requireNativeProduction(Received actual)throws MissingInputs {
        Objects.requireNonNull(actual);var production=actual.original().production();
        if(production.isEmpty())throw new MissingInputs(Set.of(RequiredInput.REJECTED_STATE_SNAPSHOT_COUNT,RequiredInput.LAST_REJECTED_STATE_SNAPSHOT,
                RequiredInput.SNAPSHOT_PUBLISH_DIAGNOSTIC_COUNT,RequiredInput.TRANSPORT_REFUSAL),Optional.of(actual));
        var value=production.orElseThrow();StrictJson.require(value.session().equals(actual.original().session()),"diagnostic production crossed its held transport session");
        if(!(value.adoption() instanceof NativeTransportDiagnostics.Observed))throw new MissingInputs(Set.of(RequiredInput.TRANSPORT_REFUSAL),Optional.of(actual));
        return value;
    }
    public record PrivateObservers(Optional<Obj> trucePreview,Optional<Obj> vfsMount,Optional<Obj> physfsMountedData) {
        public PrivateObservers {Objects.requireNonNull(trucePreview);Objects.requireNonNull(vfsMount);Objects.requireNonNull(physfsMountedData);}
    }
    /** Captured from the actual held transport; timestamps remain in the typed original received evidence. */
    public record Received(String pipeName,NativeGameTransport.TransportDiagnostics original,
            Optional<Obj> hello,Optional<Obj> heartbeat,Optional<Obj> pong,Optional<Obj> error,
            Optional<Obj> snapshotPublishDiagnostic,PrivateObservers privateObservers,Optional<Obj> modalChoiceHint,
            Optional<org.xar.ck3.control.application.action.NativeObservationPort.ObservedFrame> retainedSnapshot) {
        public Received {
            StrictJson.text(pipeName);Objects.requireNonNull(original);Objects.requireNonNull(hello);Objects.requireNonNull(heartbeat);
            Objects.requireNonNull(pong);Objects.requireNonNull(error);Objects.requireNonNull(snapshotPublishDiagnostic);
            Objects.requireNonNull(privateObservers);Objects.requireNonNull(modalChoiceHint);Objects.requireNonNull(retainedSnapshot);
        }
        public Optional<TransportSession> session(){return original.session();}
    }
    public record Report(Received received,boolean semanticStateAvailable,Supplement supplement) {
        public Report {Objects.requireNonNull(received);Objects.requireNonNull(supplement);}
    }
    /** Keeps the actual received partial evidence separate from a complete public Report. */
    public static final class MissingInputs extends IOException {
        private static final long serialVersionUID=1L;
        private final transient Set<RequiredInput> missing;
        private final transient Optional<Received> received;
        public MissingInputs(Set<RequiredInput> missing,Optional<Received> received) {
            super("actual bridge diagnostics unavailable; missing original producers: "+List.copyOf(missing));
            this.missing=Set.copyOf(missing);this.received=Objects.requireNonNull(received);
            StrictJson.require(!this.missing.isEmpty(),"missing diagnostics inputs must be explicit");
        }
        public Set<RequiredInput> missing(){return missing;}
        public Optional<Received> received(){return received;}
    }
}
