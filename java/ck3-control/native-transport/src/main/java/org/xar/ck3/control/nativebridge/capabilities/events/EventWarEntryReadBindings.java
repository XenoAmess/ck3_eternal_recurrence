package org.xar.ck3.control.nativebridge.capabilities.events;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.events.EventPolicies;
import org.xar.ck3.control.application.planning.events.EventReadBinding;
import org.xar.ck3.control.application.planning.military.ForecastReadObservation;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Routes the existing Bookmark policy query through the actual installed Army read family.
 * No native operation, capability advertisement, evaluator or event strategy is introduced here. */
public final class EventWarEntryReadBindings {
    public static final String WINDOW_STEP = EventWindowRead.STEP;
    public static final String GENERIC_CAPABILITY = WarEntryAssessmentCodec.CAPABILITY;
    public static final String SAVED_SCOPE_CAPABILITY = WarEntryAssessmentCodec.RESERVED_EVENT_SCOPE_CAPABILITY;
    private final ArmyForecastReads forecasts;
    private final Supplier<RootReadContractCatalog> catalogs;
    private final ReadContract<EventPolicies.ReadPublication> window;
    private final NativeGameTransport transport;
    private final ActionPorts.OutcomeArchive originals;
    private final Supplier<Session> sessions;

    public EventWarEntryReadBindings(ArmyForecastReads sameForecasts, Supplier<RootReadContractCatalog> actualCatalog,
            ReadContract<EventPolicies.ReadPublication> sameInstalledWindow, NativeGameTransport sameTransport,
            ActionPorts.OutcomeArchive sameArchive, Supplier<Session> borrowedSession) {
        forecasts=Objects.requireNonNull(sameForecasts);catalogs=Objects.requireNonNull(actualCatalog);
        window=Objects.requireNonNull(sameInstalledWindow);transport=Objects.requireNonNull(sameTransport);
        originals=Objects.requireNonNull(sameArchive);sessions=Objects.requireNonNull(borrowedSession);
        require(window.operation().value().equals(WINDOW_STEP), "the actual event window contract is required");
    }
    public EventReadBinding<ForecastReadObservation> binding() {
        return EventReadBinding.actualReceiptFamily(new OperationKey("event-war-entry-assessments-family"),
                selected -> WarEntryAssessmentCodec.parseStep(selected.value()).isPresent(), this::resolve);
    }
    private EventReadBinding.ReceiptResolution<ForecastReadObservation> resolve(PlanningRequest actual, OperationKey selected) {
        var targets=WarEntryAssessmentCodec.parseStep(selected.value()).orElseThrow(() -> new IllegalArgumentException("not an original single-target WarEntry operation"));
        require(targets.size()==1, "Bookmark requires its sole saved target");
        var archive=originals.withSession(Objects.requireNonNull(sessions.get(), "event read requires the current borrowed writer session"));
        NativeWire.Hello hello;
        try { hello=transport.originalHello(); } catch(IOException unavailable) { throw new UncheckedIOException(unavailable); }
        RootReadContractCatalog catalog=Objects.requireNonNull(catalogs.get());
        SavedScope scope=SavedScope.from(actual, targets.getFirst(), catalog, window, archive, hello);
        var context=new Context(actual.before(),actual.source(),actual.sessionId(),actual.deadline());
        var call=new ArmyCalls.WarEntry(new ArmyCalls.Revision(new Present<>(actual.before().frame().revision())), List.of(new PositiveId(scope.targetCharacterId())));
        var selection=new ArmyForecastReads.Selection(call,context,Optional.of(scope));
        var contract=forecasts.contract(catalog,selection);
        require(contract.operation().equals(selected), "Army changed the original Bookmark query operation");
        ObjectNode arguments=StrictJson.parse(ArmyCallCodec.encode(call).bytes()).deepCopy();
        arguments.set("event_saved_scope_read", StrictJson.parse(scope.key().bytes()));
        var frozen=DriverJson.object(StrictJson.canonical(arguments),DriverJson.MAX_NATIVE_BYTES);
        return new EventReadBinding.ReceiptResolution<>(contract,frozen,known -> {
            require(known.value() instanceof ForecastReadObservation.WarEntry, "actual Army WarEntry decoder required");
            scope.requireAssessmentReceipt(known.receipt());
            return new EventPolicies.ReadPublication(known.value().normalizedResult(),Optional.empty());
        });
    }

    /** Private mint retains the original installed window decoder and canonical read reference.
     * An opaque scope is read custody, not permission to submit a Game action. */
    public static final class SavedScope {
        private final PlanningRequest original;
        private final int target;
        private final ReadContract<EventPolicies.ReadPublication> window;
        private final ExactRef windowRef;
        private final PlanningReadReceipt windowReceipt;
        private final ExactRef helloRef;
        private final RawJson key;
        private SavedScope(PlanningRequest actual,int target,ReadContract<EventPolicies.ReadPublication> window,
                ExactRef windowRef,PlanningReadReceipt receipt,ExactRef helloRef) {
            original=actual;this.target=target;this.window=window;this.windowRef=windowRef;windowReceipt=receipt;this.helloRef=helloRef;
            ObjectNode row=StrictJson.object().put("schema","xar.event-window-saved-scope-read/v1")
                    .put("window_contract_id",window.contractId()).put("target_character_id",target);
            row.set("window_original_receipt",windowRef.toJson());row.set("original_hello",helloRef.toJson());
            key=new RawJson(StrictJson.canonical(row));
        }
        /** Source-bound software entry point: all arguments are re-read through the installed canonical contract. */
        public static SavedScope from(PlanningRequest actual,int target,RootReadContractCatalog catalog,
                ReadContract<EventPolicies.ReadPublication> window,ActionPorts.OutcomeArchive archive,NativeWire.Hello receivedHello) {
            Objects.requireNonNull(actual);Objects.requireNonNull(catalog);Objects.requireNonNull(window);Objects.requireNonNull(archive);
            require(target>0 && window.operation().value().equals(WINDOW_STEP) && catalog.containsIdentity(window), "same installed window contract required");
            ExactRef reference=null;
            var history=actual.observations().history();
            for(int index=history.size()-1;index>=0;index--) {
                var row=history.get(index);
                if(new OpportunityJson.Text(WINDOW_STEP).equals(row.get("command")) && new OpportunityJson.Bool(true).equals(row.get("ok"))) {
                    reference=ExactRef.fromJson(OpportunityJson.toNode(row.get("native_read_original_receipt")));break;
                }
            }
            require(reference!=null, "Bookmark requires its actual successful original window read");
            PlanningReadReceipt receipt=archive.loadRead(reference);
            require(archive.readReferenceOf(receipt).equals(reference), "window is not the canonical archived original");
            requireRequest(actual,receipt,window);
            var publication=window.replay(receipt);
            JsonNode context=context(publication);
            var saved=WarEntryAssessmentCodec.raiktorSavedScopeTarget(OpportunityJson.toNode(actual.observations().snapshot()),context);
            require(saved.isPresent() && saved.getAsInt()==target, "query target is not this original Bookmark saved character");
            NativeWire.Hello hello=decodeHello(receivedHello);
            ExactRef evidence=receipt.before().binding().capabilityEvidence();
            require(hello.packet().value().length==evidence.bytes() && ActionCodec.sha256(hello.packet().value()).equals(evidence.sha256())
                    && evidence.equals(receipt.after().binding().capabilityEvidence()), "cached Hello differs from original window evidence");
            require(hello.connectionGeneration().equals(receipt.before().binding().connectionGeneration()) && hello.buildMatch()
                    && hello.capabilities().contains(GENERIC_CAPABILITY), "original native Hello does not grant the existing WarEntry family");
            var diagnostics=OpportunityJson.object(actual.observations().snapshot().get("diagnostics"),"diagnostics");
            require(OpportunityJson.integer(diagnostics.get("bridge_pid"),"bridge_pid").equals(java.math.BigInteger.valueOf(hello.pid())), "original Hello PID differs from current native frame");
            boolean ordinary=true;
            try { WarEntryAssessmentCodec.targetScopes(OpportunityJson.toNode(actual.observations().snapshot()),List.of(target)); }
            catch(IllegalArgumentException absent) { ordinary=false; }
            require(ordinary || hello.capabilities().contains(SAVED_SCOPE_CAPABILITY), "saved-scope-only WarEntry is not advertised by the actual Native producer");
            // Current native producer accepts declarable/active targets. A reserved name in source is never an advertisement.
            return new SavedScope(actual,target,window,reference,receipt,evidence);
        }
        public int targetCharacterId() { return target; }
        public RawJson key() { return key; }
        public WarEntryAssessmentCodec.Scopes scopes(Context actual,OpportunityJson.Obj snapshot,ActionPorts.OutcomeArchive archive) {
            require(actual.before().equals(original.before()) && actual.source().equals(original.source()) && actual.sessionId().equals(original.sessionId())
                    && actual.deadline().equals(original.deadline()), "saved event read crossed the original frame/source/session/deadline");
            for(String field:List.of("snapshot_id","revision","native_revision","date_raw","episode_run_id","active_event","paused","declarable_wars","active_wars"))
                require(Objects.equals(snapshot.get(field),original.observations().snapshot().get(field)), "saved event read changed frozen operand "+field);
            PlanningReadReceipt receipt=archive.loadRead(windowRef);
            require(receipt.equals(windowReceipt) && archive.readReferenceOf(receipt).equals(windowRef), "saved event original window changed");
            requireRequest(original,receipt,window);
            JsonNode context=context(window.replay(receipt));
            var saved=WarEntryAssessmentCodec.raiktorSavedScopeTarget(OpportunityJson.toNode(snapshot),context);
            require(saved.isPresent() && saved.getAsInt()==target, "saved event target no longer matches its original window");
            return WarEntryAssessmentCodec.targetScopes(OpportunityJson.toNode(snapshot),List.of(target),context);
        }
        public void requireAssessmentReceipt(PlanningReadReceipt receipt) {
            var request=receipt.request();
            require(request.before().equals(original.before()) && request.source().equals(original.source()) && request.sessionId().equals(original.sessionId()) && request.deadline().equals(original.deadline())
                    && request.operation().value().equals(WarEntryAssessmentCodec.step(List.of(target))), "assessment crossed the selected original event query");
            require(Objects.equals(request.arguments().get("event_saved_scope_read"),OpportunityJson.parse(key.bytes())), "assessment lacks its original window custody key");
            for(var guard:List.of(receipt.before().binding(),receipt.after().binding()))
                require(guard.capabilityEvidence().equals(helloRef) && guard.connectionGeneration().equals(windowReceipt.before().binding().connectionGeneration()), "assessment crossed the original window Hello or connection");
        }
        private static void requireRequest(PlanningRequest actual,PlanningReadReceipt receipt,ReadContract<EventPolicies.ReadPublication> window) {
            var request=receipt.request();
            require(receipt.contractId().equals(window.contractId()) && request.operation().equals(window.operation()) && request.before().equals(actual.before())
                    && request.source().equals(actual.source()) && request.sessionId().equals(actual.sessionId()) && request.deadline().equals(actual.deadline()), "window read crossed installed contract or original planner frame/deadline");
        }
        private static JsonNode context(EventPolicies.ReadPublication publication) {
            var result=publication.result();
            require(result.get("current_event_window_context") instanceof OpportunityJson.Obj, "actual window decoder did not publish current event context");
            return OpportunityJson.toNode(result.get("current_event_window_context"));
        }
        private static NativeWire.Hello decodeHello(NativeWire.Hello received) {
            Objects.requireNonNull(received);
            try {
                var decoded=NativeWire.decode(received.packet().value());
                require(decoded instanceof NativeWire.Hello, "actual complete Hello packet required");
                return (NativeWire.Hello)decoded;
            } catch(IOException invalid) { throw new UncheckedIOException(invalid); }
        }
    }
    private static void require(boolean condition,String message) { StrictJson.require(condition,message); }
}
