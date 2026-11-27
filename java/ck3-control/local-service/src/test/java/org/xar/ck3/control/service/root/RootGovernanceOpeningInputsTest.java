package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.application.planning.governance.GovernanceOpeningDocument;
import org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.OpeningStage;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.SavedContinuityBootstrap;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.continuity.writer.WriterContracts.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Actual opening retained-body boundary and strict codec, with in-memory I/O doubles; no private Root restoration or native FileID claim. */
final class RootGovernanceOpeningInputsTest {
    private static final String MACHINE="opening-retained-body-unit-machine";
    private static final Instant AT=Instant.parse("2026-10-24T00:00:00Z");
    private static final ExactRef HEAD=ref("unit-head"),HISTORICAL=ref("missing-historical-code.java"),CURRENT=ref("different-current-code.java"),COMMAND=ref("original-pending-command");
    private static ExactRef ref(String name) {return new ExactRef(name,17,"a".repeat(64));}
    private static GovernanceOpeningDocument.Document pending() {
        var frame=new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),BigInteger.TEN,BigInteger.valueOf(1000)),
                "synthetic-native-10",BigInteger.TEN,"unit-episode");
        var observed=new ObservationIdentity(MACHINE,new GameGeneration(123,new PythonOnlyUInt64(new BigInteger("133700000000000001"))),frame,1);
        return new GovernanceOpeningDocument.Document(observed,new G2Source(MACHINE,AT.toString(),"1.20.0.4",CURRENT),"unit-session",
                OpeningStage.AWAIT_RECEIPT,Optional.empty(),Optional.empty(),List.of(COMMAND),Optional.of(COMMAND),Optional.empty());
    }
    private static final class Store implements ContinuityStorePort.Session {
        ContinuityState state;DomainBodies.Read body;int mutations;
        ContinuityState historical;

        @Override public ContinuityState requireHistoricalState(long sequence, String digest) throws IOException {
            if (historical == null || historical.sequence() != sequence || !ContinuityJson.digest(historical.toJson()).equals(digest))
                throw new IOException("test historical state was not retained");
            return historical;
        }
        Store(byte[] bytes) {
            var raw=StrictJson.object().put("schema","root.ck3.continuity-window/v1").put("machine_id",MACHINE)
                    .put("sequence",0).put("window_id",1).put("status","running").put("start_date_raw",1000)
                    .put("target_days",1).put("target_date_raw",1024).put("last_settled_cycles",0).put("last_settled_date_raw",1000);
            state=ContinuityState.fromJson(raw,MACHINE);
            var payload=new ExactRef("unit-opening-body",bytes.length,ActionCodec.sha256(bytes));
            var reference=new DomainBodies.BodyRef(DomainBodies.Slot.OPENING_GATE,GovernanceOpeningDocument.SCHEMA,payload,
                    new FileIdentity("1","2","133700000000000001",AT.toString(),bytes.length),List.of(HISTORICAL));
            state=DomainBodies.reduceImport(state,reference);body=new DomainBodies.Available(reference,bytes,HEAD,List.of());
        }
        @Override public void requireWriter(Path lock) {throw new AssertionError("body seam cannot grant Root writer custody");}
        @Override public Pin capturePin(ExactRef ref,int maximum) {throw new AssertionError("unit does not capture physical files");}
        @Override public void verifyPin(Pin pin) {throw new AssertionError("unit does not verify physical files");}
        @Override public Head head() {return new Head(state,List.of(),List.of(),List.of(),false);}
        @Override public ExactRef persistedHead() {return HEAD;}
        @Override public DomainBodies.Read readDomain(DomainBodies.Slot slot) {
            assertEquals(DomainBodies.Slot.OPENING_GATE,slot);return body;
        }
        @Override public Prepared preview(Request request) {mutations++;throw new AssertionError("retained read cannot initialize");}
        @Override public Receipt commit(Prepared prepared) {mutations++;throw new AssertionError("retained read cannot publish");}
    }
    @Test void historicalTracePreservesPendingPreparedOriginalWithoutCompletingOrPublishing() throws Exception {
        byte[] bytes=GovernanceOpeningDocument.encode(pending());var store=new Store(bytes);var before=store.state;
        var inputs=new RootGovernanceOpeningInputs(List.of(CURRENT));
        var retained=inputs.retainedBody(store,HEAD);var decoded=GovernanceOpeningDocument.decode(retained.canonicalBody());
        assertEquals(pending(),decoded);assertEquals(OpeningStage.AWAIT_RECEIPT,decoded.stage());
        assertEquals(Optional.of(COMMAND),decoded.preparedCommand());assertTrue(decoded.actionReceipt().isEmpty());assertTrue(decoded.checkpoint().isEmpty());
        assertEquals(List.of(HISTORICAL),retained.reference().producerSources());assertFalse(retained.reference().producerSources().contains(CURRENT));
        assertEquals(retained.reference(),DomainBodies.BodyRef.fromJson(StrictJson.parse(StrictJson.canonical(retained.reference().toJson()))));
        assertArrayEquals(bytes,GovernanceOpeningDocument.encode(decoded));assertArrayEquals(bytes,retained.canonicalBody());
        assertSame(before,store.state);assertEquals(HEAD,store.persistedHead());assertEquals(0,store.mutations);
    }
    @Test void historicalTraceCannotAuthorizeWrongHeadSlotSchemaOrReplacedNativeMember() {
        byte[] bytes=GovernanceOpeningDocument.encode(pending());
        for(int mismatch=0;mismatch<5;mismatch++) {
            var store=new Store(bytes);var saved=((DomainBodies.Available)store.body).reference();
            var replaced=new DomainBodies.BodyRef(mismatch==1?DomainBodies.Slot.COUNCIL:saved.slot(),
                    mismatch==2?"wrong-schema":saved.contractSchema(),
                    mismatch==4?new ExactRef("not-the-persisted-body",bytes.length,saved.payload().sha256()):saved.payload(),
                    mismatch==3?new FileIdentity("1","3","133700000000000001",AT.toString(),bytes.length):saved.identity(),saved.producerSources());
            store.body=new DomainBodies.Available(replaced,bytes,mismatch==0?ref("other-head"):HEAD,List.of());
            var inputs=new RootGovernanceOpeningInputs(List.of(CURRENT));
            assertThrows(IllegalArgumentException.class,()->inputs.retainedBody(store,HEAD));
            assertEquals(saved,DomainBodies.reference(store.state,DomainBodies.Slot.OPENING_GATE).orElseThrow());assertEquals(0,store.mutations);
        }
    }
    @Test void everyUnavailableReasonRemainsUnavailableWithoutInitializingAnOpeningGate() {
        for(var reason:DomainBodies.Reason.values()) {
            var store=new Store(GovernanceOpeningDocument.encode(pending()));var before=store.state;
            store.body=new DomainBodies.Unavailable(reason,Optional.of(HEAD),"unit unavailable body");
            assertThrows(IOException.class,()->new RootGovernanceOpeningInputs(List.of(CURRENT)).retainedBody(store,HEAD));
            assertSame(before,store.state);assertEquals(0,store.mutations);
        }
    }
    @Test void namedSaveUsesTheOriginalOpeningBodyWithoutAPhysicalRestore() throws Exception {
        var original = pending();
        var document = new GovernanceOpeningDocument.Document(original.observed(), original.source(), original.sessionId(),
                OpeningStage.AWAIT_SUBMIT, Optional.empty(), Optional.empty(), original.originals());
        var store = new Store(GovernanceOpeningDocument.encode(document));
        var departed = new SessionIdentity(MACHINE, document.observed().game(), document.sessionId());
        var replacement = new GameGeneration(124, new PythonOnlyUInt64(new BigInteger("133700000000000002")));
        var owner = new SessionIdentity(MACHINE, replacement, "named-session");
        var frame = new ObservationIdentity(MACHINE, replacement,
                new JointBudgetSelector.ProposalFrame(
                        new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.ONE, BigInteger.valueOf(1024)),
                        "named-frame", BigInteger.ONE, "unit-episode"), 1);
        var saved = new CheckpointPair(witness("original-save","a"), witness("original-driver","a"), document.observed(),
                "original-lineage", 1, "save-action", ref("save-ack"), AT);
        var retiredHead = ref("retired-actions");
        var originState = store.state.toJson().put("sequence", 1).put("status", "repair_required");
        originState.set("game_binding", departed.game().toJson());
        originState.set(WriterContracts.ACTION_LIFECYCLE_FIELD, retiredHead.toJson());
        originState.putObject(SavedContinuityBootstrap.FIELD).set("checkpoint_pair", StrictJson.parse(CheckpointPairCodec.encode(saved)));
        store.historical = ContinuityState.fromJson(originState, MACHINE);

        var origin = StrictJson.object().put("schema", "xar.java-ordinary-external-save-origin/v1")
                .put("predecessor_sequence", 1).put("predecessor_digest", ContinuityJson.digest(store.historical.toJson()));
        origin.set("departed", OrdinaryCycleTransitions.sessionToJson(departed));
        origin.set("successor", OrdinaryCycleTransitions.sessionToJson(owner));
        origin.set("saved_pair", StrictJson.parse(CheckpointPairCodec.encode(saved)));
        origin.set("loaded_file", CheckpointPairCodec.fileWitnessToJson(witness("named-save","b")));
        origin.set("retired_action_head", retiredHead.toJson());
        origin.putObject("opening").put("machine_id", MACHINE).put("session_id", owner.sessionId())
                .put("connection_generation", "1").put("actor", 29829).put("date_raw", 1024)
                .put("snapshot_id", "named-frame").put("native_revision", "1").set("game", replacement.toJson());
        var bytes = ContinuityJson.canonical(origin);
        var originRef = new ExactRef("external-origin", bytes.length, ActionCodec.sha256(bytes));
        var current = originState.deepCopy().put("sequence", 3).put("status", "running");
        current.set("game_binding", replacement.toJson());
        current.set(WriterContracts.ORDINARY_EXTERNAL_SAVE_ORIGIN_FIELD, originRef.toJson());
        store.state = ContinuityState.fromJson(current, MACHINE);
        var archive = (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(getClass().getClassLoader(),
                new Class<?>[]{ActionPorts.OutcomeArchive.class}, (proxy, method, args) -> {
                    assertEquals("loadMaterial", method.getName());
                    assertEquals(originRef, args[0]);
                    return new RawJson(bytes);
                });
        var body = (DomainBodies.Available) store.body;
        var archived = RootGovernanceOpeningInputs.externalOpeningEvidence(store, archive, owner, document, frame, body).orElseThrow();
        assertEquals(List.of(originRef, body.reference().payload()), archived);
        var rebound = GovernanceOpeningDocument.decode(
                OpeningTransitions.externalUnissuedDocument(document, frame, document.source(), owner, archived));
        assertEquals(frame, rebound.observed());
        assertEquals(owner.sessionId(), rebound.sessionId());
        assertEquals(OpeningStage.AWAIT_SUBMIT, rebound.stage());
        assertTrue(rebound.originals().containsAll(List.of(originRef, body.reference().payload(), COMMAND)));
        assertTrue(rebound.preparedCommand().isEmpty());
        assertTrue(rebound.actionReceipt().isEmpty());
        assertTrue(rebound.checkpoint().isEmpty());
        assertThrows(IllegalArgumentException.class, () ->
                OpeningTransitions.externalUnissuedDocument(original, frame, document.source(), owner, archived));
        assertTrue(RootGovernanceOpeningInputs.externalOpeningEvidence(store, archive,
                new SessionIdentity(MACHINE, replacement, "other-session"), document, frame, body).isEmpty());
        var changed = new DomainBodies.Available(body.reference(), body.canonicalBody(), ref("new-head"), List.of());
        assertThrows(IllegalArgumentException.class, () ->
                RootGovernanceOpeningInputs.externalOpeningEvidence(store, archive, owner, document, frame, changed));
        assertEquals(0, store.mutations);
    }

    private static CheckpointPair.FileWitness witness(String path, String digestCharacter) {
        return new CheckpointPair.FileWitness(new ExactRef(path, 17, digestCharacter.repeat(64)),
                new FileStatIdentity(BigInteger.valueOf(17), "1", "0"));
    }

    @Test void malformedRetainedOpeningStillFailsTheSameStrictDecoderInsteadOfBecomingClear() throws Exception {
        var raw=(com.fasterxml.jackson.databind.node.ObjectNode)StrictJson.parse(GovernanceOpeningDocument.encode(pending()));
        raw.put("stage",true);byte[] bytes=StrictJson.canonical(raw);var store=new Store(bytes);
        var retained=new RootGovernanceOpeningInputs(List.of(HISTORICAL)).retainedBody(store,HEAD);
        assertThrows(IllegalArgumentException.class,()->GovernanceOpeningDocument.decode(retained.canonicalBody()));assertEquals(0,store.mutations);
    }
}
