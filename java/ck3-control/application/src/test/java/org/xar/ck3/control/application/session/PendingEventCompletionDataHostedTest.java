package org.xar.ck3.control.application.session;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.NativeArchiveDataCodec;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Hosted, original DATA only. This adapter issues no Root, Session, Native or cycle permission. */
public final class PendingEventCompletionDataHostedTest {
    @Test public void actualApplied527SelectsOnlyUnchangedZeroDayData() throws Exception {
        Fixture f = Fixture.load();
        byte[] headBefore = f.headBytes.clone();
        byte[] stateBefore = StrictJson.canonical(f.state.toJson(),ActionCodec.MAX_COMMAND_BYTES);
        byte[] commandBefore = ActionCodec.encodeCommand(f.latest.command());
        var selected = ContinuityBatchJournal.readOnlyPendingEventCompletionRoot(f.state, f.owner, f.actions, f.archive);
        assertEquals(f.latest, selected.orElseThrow(), "real complete canonical527 must be selected as DATA");
        assertInstanceOf(ActionState.Settled.class, selected.orElseThrow().state());
        var settled = (ActionState.Settled) selected.orElseThrow().state();
        assertInstanceOf(ActionState.Applied.class, settled.settlement());
        assertFalse(f.latest.eligibleAdvance());
        assertEquals(f.latest.command().before().frame().identity().dateRaw(),
                ((ActionState.Applied) settled.settlement()).observation().after().frame().identity().dateRaw());
        assertArrayEquals(commandBefore, ActionCodec.encodeCommand(selected.orElseThrow().command()));
        assertEquals("2026-11-05T01:55:03.894579600Z", selected.orElseThrow().command().deadline().toString());
        assertArrayEquals(headBefore, f.archive.raw(f.headRef));
        assertArrayEquals(stateBefore, StrictJson.canonical(f.state.toJson(),ActionCodec.MAX_COMMAND_BYTES));
        var reversed = new ArrayList<>(f.actions); java.util.Collections.reverse(reversed);
        assertEquals(f.latest, ContinuityBatchJournal.readOnlyPendingEventCompletionRoot(
                f.state, f.owner, reversed, f.archive).orElseThrow(), "complete canonical set is independent of caller order");
        assertEquals(0, f.archive.writes);
        System.out.println("DATA actual527_complete_chain=true original_settled=true original_command_unchanged=true zero_day=true unissued_no_Root_or_cycle_credit=true");
    }

    @Test public void ownerCanonicalAndOriginalBindingsRejectWithoutAuthority() throws Exception {
        Fixture f = Fixture.load(); int rejected = 0;
        assertTrue(ContinuityBatchJournal.readOnlyPendingEventCompletionRoot(f.state,
                new SessionIdentity(f.owner.machineId(), f.owner.game(), f.owner.sessionId()+"-wrong"), f.actions, f.archive).isEmpty()); rejected++;
        assertTrue(ContinuityBatchJournal.readOnlyPendingEventCompletionRoot(f.state,
                new SessionIdentity(f.owner.machineId()+"-wrong", f.owner.game(), f.owner.sessionId()), f.actions, f.archive).isEmpty()); rejected++;
        var missing = new ArrayList<>(f.actions); missing.remove(f.latest);
        assertTrue(ContinuityBatchJournal.readOnlyPendingEventCompletionRoot(f.state,f.owner,missing,f.archive).isEmpty()); rejected++;
        var duplicate = new ArrayList<>(f.actions); duplicate.add(f.latest);
        assertTrue(ContinuityBatchJournal.readOnlyPendingEventCompletionRoot(f.state,f.owner,duplicate,f.archive).isEmpty()); rejected++;
        assertTrue(ContinuityBatchJournal.readOnlyPendingEventCompletionRoot(f.state,f.owner,List.of(f.latest),f.archive).isEmpty()); rejected++;
        var settled=(ActionState.Settled)f.latest.state();
        var applied=(ActionState.Applied)settled.settlement();
        var fresh=(ObservationProvenance.FreshSnapshotQuery)applied.observation().provenance();
        var cold=(ObservationProvenance.ColdAfterAcknowledgement)fresh.basis();
        ExactRef dispatch=f.archive.referenceOf(settled.dispatch());
        ExactRef prepared=f.archive.requestReferenceOf(settled.attempt().preparedRequest());
        ExactRef record=ContinuityActionJournal.recordHead(f.state).orElseThrow();
        for (ExactRef denied : List.of(cold.originalReceipt(),dispatch,prepared,record)) {
            f.archive.denied.add(denied);
            assertTrue(ContinuityBatchJournal.readOnlyPendingEventCompletionRoot(f.state,f.owner,f.actions,f.archive).isEmpty(),
                    "actual selector must reject missing original role: "+denied.sha256());
            f.archive.denied.remove(denied); rejected++;
            assertEquals(f.latest,ContinuityBatchJournal.readOnlyPendingEventCompletionRoot(f.state,f.owner,f.actions,f.archive).orElseThrow());
        }
        byte[] altered=f.archive.raw(prepared); altered[altered.length-1]^=1;
        f.archive.overrides.put(prepared,altered);
        assertTrue(ContinuityBatchJournal.readOnlyPendingEventCompletionRoot(f.state,f.owner,f.actions,f.archive).isEmpty()); rejected++;
        f.archive.overrides.remove(prepared);
        assertEquals(f.latest,ContinuityBatchJournal.readOnlyPendingEventCompletionRoot(f.state,f.owner,f.actions,f.archive).orElseThrow());
        assertEquals(0,f.archive.writes);
        System.out.println("DATA actual_selector_negative_count="+rejected+" no_builder_exception_credit=true restored_positive=true unissued_no_Root=true");
    }

    @Test public void actual663RetainsOldSchedulerAsStageOnlyDataWithoutReplay() throws Exception {
        DataArchive archive=DataArchive.open();
        Path delta=Path.of(System.getProperty("xar.test.retained_stage_delta")).toAbsolutePath().normalize();
        String deltaSha=System.getProperty("xar.test.retained_stage_delta_sha256");
        assertEquals("a14e27efe4a0d3acc8471fcbd5b6c41fddc4f9be80ec943ff192359398542f2e",deltaSha);
        assertTrue(Files.isRegularFile(delta,LinkOption.NOFOLLOW_LINKS));
        byte[] deltaBytes=Files.readAllBytes(delta);
        assertEquals(199963,deltaBytes.length);assertEquals(deltaSha,ActionCodec.sha256(deltaBytes));
        var extra=StrictJson.parse(deltaBytes,ActionCodec.MAX_COMMAND_BYTES);
        var declaredBase=ExactRef.fromJson(extra.get("base_manifest"));
        assertEquals(Path.of(System.getProperty("xar.test.pending_event_manifest")).toAbsolutePath().normalize(),Path.of(declaredBase.path()).toAbsolutePath().normalize());
        assertEquals(System.getProperty("xar.test.pending_event_manifest_sha256"),declaredBase.sha256());
        assertEquals(1008039,declaredBase.bytes());assertEquals(190,extra.path("rows").size());
        for(var row:extra.path("rows")) {
            ExactRef original=ExactRef.fromJson(row.get("original")),frozen=ExactRef.fromJson(row.get("frozen"));
            Path file=Path.of(frozen.path()).toAbsolutePath().normalize();
            assertEquals(original.bytes(),frozen.bytes());assertEquals(original.sha256(),frozen.sha256());
            assertTrue(file.startsWith(delta.getParent()));assertTrue(Files.isRegularFile(file,LinkOption.NOFOLLOW_LINKS));
            Path old=archive.files.putIfAbsent(original,file);assertTrue(old==null||old.equals(file));
        }
        assertEquals(1258,archive.files.size());
        ExactRef headRef=ExactRef.fromJson(extra.get("current_head664").get("original"));
        assertEquals("6b598b0012592c0a42141f7bd0350f4bf9b55f13a561e0a105c117616ce4af37",headRef.sha256());
        archive.headRef=headRef;byte[] headBytes=archive.raw(headRef);
        var headJson=(ObjectNode)StrictJson.parse(headBytes,ActionCodec.MAX_COMMAND_BYTES);
        ContinuityState state=ContinuityState.fromJson(headJson,StrictJson.text(headJson.get("machine_id")));
        List<ActionReceipt> actions=ContinuityActionJournal.receipts(state,archive);
        ActionReceipt latest=actions.stream().max(java.util.Comparator.comparingLong(ActionReceipt::sequence)).orElseThrow();
        assertEquals(664,state.sequence());assertEquals(663,latest.sequence());
        assertEquals("ordinary-sway-c4c6f206f8d0f41889079158503f3c74b37f660b",latest.command().actionId());
        assertInstanceOf(ActionState.CompositeUnknown.class,latest.state());
        assertEquals(1,actions.stream().filter(a->!a.settled()).count());
        var command=latest.command();var owner=new SessionIdentity(command.before().machineId(),command.before().game(),command.sessionId());
        assertEquals(java.time.Instant.parse("2026-11-05T15:30:08.542561600Z"),command.deadline());
        byte[] stateBefore=StrictJson.canonical(state.toJson(),ActionCodec.MAX_COMMAND_BYTES),commandBefore=ActionCodec.encodeCommand(command);
        var bodyRef=org.xar.ck3.control.continuity.writer.DomainBodies.reference(state,
                org.xar.ck3.control.continuity.writer.DomainBodies.Slot.SWAY).orElseThrow();
        byte[] bodyBytes=archive.raw(bodyRef.payload());var body=(ObjectNode)StrictJson.parse(bodyBytes,ActionCodec.MAX_COMMAND_BYTES);
        ExactRef stageRef=ExactRef.fromJson(body.get("active_stage"));
        var stage=org.xar.ck3.control.application.planning.sway.SwaySchedulerReplay.decodeStage(archive.raw(stageRef));
        byte[] priorBytes=archive.raw(stage.inputDomain());var prior=(ObjectNode)StrictJson.parse(priorBytes,ActionCodec.MAX_COMMAND_BYTES);
        ExactRef oldStageRef=ExactRef.fromJson(prior.get("active_stage"));
        assertEquals(53162232,StrictJson.integer(prior.path("scheduler").get("last_check_date_raw"),0,StrictJson.MAX_SAFE_INTEGER));
        assertEquals(53162952,command.before().frame().identity().dateRaw().longValueExact());
        assertEquals(prior.get("scheduler"),body.get("scheduler"));
        var inverse=body.deepCopy();inverse.set("active_stage",prior.get("active_stage"));
        assertArrayEquals(priorBytes,StrictJson.canonical(inverse,ActionCodec.MAX_COMMAND_BYTES));
        assertEquals(latest,ContinuityBatchJournal.readOnlyUnstartedSwayRecoveryRoot(state,owner,actions,archive).orElseThrow());
        int[] denied={0};
        java.util.function.BiConsumer<SessionIdentity,List<ActionReceipt>> reject=(candidateOwner,candidateActions)->{
            assertTrue(ContinuityBatchJournal.readOnlyUnstartedSwayRecoveryRoot(state,candidateOwner,candidateActions,archive).isEmpty());
            denied[0]++;
        };
        reject.accept(new SessionIdentity(owner.machineId(),owner.game(),owner.sessionId()+"-foreign"),actions);
        assertEquals(latest,ContinuityBatchJournal.readOnlyUnstartedSwayRecoveryRoot(state,owner,actions,archive).orElseThrow());
        var missing=new ArrayList<>(actions);missing.remove(latest);reject.accept(owner,missing);
        assertEquals(latest,ContinuityBatchJournal.readOnlyUnstartedSwayRecoveryRoot(state,owner,actions,archive).orElseThrow());
        var duplicated=new ArrayList<>(actions);duplicated.add(actions.getFirst());reject.accept(owner,duplicated);
        assertEquals(latest,ContinuityBatchJournal.readOnlyUnstartedSwayRecoveryRoot(state,owner,actions,archive).orElseThrow());
        for(ExactRef absent:List.of(bodyRef.payload(),stageRef,stage.inputDomain(),oldStageRef)) {
            archive.decoded.clear();archive.denied.add(absent);
            try {reject.accept(owner,actions);} finally {archive.denied.remove(absent);archive.decoded.clear();}
            assertEquals(latest,ContinuityBatchJournal.readOnlyUnstartedSwayRecoveryRoot(state,owner,actions,archive).orElseThrow());
        }
        byte[] altered=bodyBytes.clone();altered[altered.length-1]^=1;
        archive.decoded.clear();archive.overrides.put(bodyRef.payload(),altered);
        try {reject.accept(owner,actions);} finally {archive.overrides.remove(bodyRef.payload());archive.decoded.clear();}
        assertEquals(latest,ContinuityBatchJournal.readOnlyUnstartedSwayRecoveryRoot(state,owner,actions,archive).orElseThrow());
        assertEquals(8,denied[0]);assertEquals(0,archive.writes);
        assertArrayEquals(headBytes,archive.raw(headRef));assertArrayEquals(stateBefore,StrictJson.canonical(state.toJson(),ActionCodec.MAX_COMMAND_BYTES));
        assertArrayEquals(commandBefore,ActionCodec.encodeCommand(latest.command()));
        assertArrayEquals(bodyBytes,archive.raw(bodyRef.payload()));assertArrayEquals(priorBytes,archive.raw(stage.inputDomain()));
        System.out.println("DATA actual663_stage_old_metadata=true canonical_actions="+actions.size()+" denials="+denied[0]
                +" restored_positive=true original_state_command_deadline=true old_scheduler_preserved=true unissued_no_Root=true");
    }

    private record Fixture(DataArchive archive, ExactRef headRef, byte[] headBytes,
            ContinuityState state, SessionIdentity owner, List<ActionReceipt> actions, ActionReceipt latest) {
        static Fixture load() throws IOException {
            DataArchive archive=DataArchive.open();
            ExactRef head=archive.headRef;
            byte[] bytes=archive.raw(head);
            var json=(ObjectNode)StrictJson.parse(bytes,ActionCodec.MAX_COMMAND_BYTES);
            ContinuityState state=ContinuityState.fromJson(json,StrictJson.text(json.get("machine_id")));
            var actions=ContinuityActionJournal.receipts(state,archive);
            var latest=actions.stream().max(java.util.Comparator.comparingLong(ActionReceipt::sequence)).orElseThrow();
            assertEquals(527,latest.sequence());
            var owner=new SessionIdentity(latest.command().before().machineId(),latest.command().before().game(),latest.command().sessionId());
            return new Fixture(archive,head,bytes,state,owner,actions,latest);
        }
    }

    /** Only exact frozen bytes and public DATA codecs. No borrowed writer or installed Root is created. */
    private static final class DataArchive implements ActionPorts.OutcomeArchive {
        ExactRef headRef;
        int writes;
        final Set<ExactRef> denied=new HashSet<>();
        final Map<ExactRef,byte[]> overrides=new HashMap<>();
        final Map<ExactRef,Path> files=new HashMap<>();
        final Map<ExactRef,byte[]> bytesCache=new HashMap<>();
        final Map<ExactRef,Object> decoded=new HashMap<>();
        final NativeArchiveDataCodec codec=new NativeArchiveDataCodec((ref,max)->{
            byte[] bytes=raw(ref);if(bytes.length>max)throw new IOException("original exceeds actual DATA codec bound");return bytes;
        });
        static DataArchive open() throws IOException {
            String configured=System.getProperty("xar.test.pending_event_manifest");
            String sha=System.getProperty("xar.test.pending_event_manifest_sha256");
            if(configured==null || sha==null || !sha.matches("[0-9a-f]{64}"))throw new IOException("explicit pinned hosted manifest properties required");
            Path manifest=Path.of(configured).toAbsolutePath().normalize();
            if(!Files.isRegularFile(manifest,LinkOption.NOFOLLOW_LINKS))throw new IOException("plain hosted manifest required");
            byte[] bytes=Files.readAllBytes(manifest);
            if(bytes.length>ActionReceiptCodec.MAXIMUM_RECEIPT_BYTES || !ActionCodec.sha256(bytes).equals(sha))throw new IOException("hosted manifest changed");
            var root=StrictJson.parse(bytes,ActionCodec.MAX_COMMAND_BYTES);
            var rows=root.get("rows");
            if(rows==null || !rows.isArray() || rows.isEmpty() || rows.size()>4096)throw new IOException("bounded actual original map required");
            DataArchive result=new DataArchive();
            for(var row:rows){
                ExactRef original=ExactRef.fromJson(row.get("original"));
                ExactRef frozen=ExactRef.fromJson(row.get("frozen"));
                Path path=Path.of(frozen.path()).toAbsolutePath().normalize();
                if(original.bytes()!=frozen.bytes() || !original.sha256().equals(frozen.sha256())
                        || !path.startsWith(manifest.getParent()) || !Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS))
                    throw new IOException("only identical plain frozen originals in this hosted bundle are allowed");
                Path prior=result.files.putIfAbsent(original,path);
                if(prior!=null && !prior.equals(path))throw new IOException("ambiguous original byte map");
                if(row.has("role") && row.get("role").asText().equals("current_head527")){
                    if(result.headRef!=null && !result.headRef.equals(original))throw new IOException("one exact actual head required");
                    result.headRef=original;
                }
            }
            if(result.headRef==null)throw new IOException("actual527 head is absent");
            return result;
        }
        byte[] raw(ExactRef ref) {
            if(denied.contains(ref))throw new IllegalArgumentException("deliberately missing original "+ref.sha256());
            if(ref.bytes()<0 || ref.bytes()>RawJson.MAXIMUM_BYTES)throw new IllegalArgumentException("bounded original DATA required");
            byte[] bytes=overrides.get(ref);
            if(bytes==null)bytes=bytesCache.get(ref);
            if(bytes==null){
                Path file=files.get(ref);if(file==null)throw new IllegalArgumentException("fixture original not held: "+ref.path()+" sha="+ref.sha256());
                try{
                    if(!Files.isRegularFile(file,LinkOption.NOFOLLOW_LINKS))throw new IOException("plain frozen file required");
                    bytes=Files.readAllBytes(file);
                }catch(IOException failure){throw new UncheckedIOException(failure);}
            }
            if(bytes.length!=ref.bytes() || !ActionCodec.sha256(bytes).equals(ref.sha256()))throw new IllegalArgumentException("frozen original bytes/SHA changed "+ref.sha256());
            if(!overrides.containsKey(ref))bytesCache.putIfAbsent(ref,bytes.clone());
            return bytes.clone();
        }
        private ExactRef existing(Object value){
            for(var row:decoded.entrySet())if(row.getValue()==value){raw(row.getKey());return row.getKey();}
            for(var row:decoded.entrySet())if(row.getValue().equals(value)){raw(row.getKey());return row.getKey();}
            if(value instanceof RawJson raw){
                String sha=ActionCodec.sha256(raw.bytes());ExactRef found=null;
                for(ExactRef ref:files.keySet())if(ref.bytes()==raw.bytes().length && ref.sha256().equals(sha)){
                    if(!java.util.Arrays.equals(raw(ref),raw.bytes()))throw new IllegalArgumentException("material exact bytes differ");
                    if(found!=null && !found.equals(ref))throw new IllegalArgumentException("ambiguous existing material");found=ref;
                }
                if(found!=null)return found;
            }
            throw new IllegalArgumentException("original object has no verified pinned DATA reference: "+value.getClass().getName());
        }
        private UnsupportedOperationException readOnly(){writes++;return new UnsupportedOperationException("UNISSUED read-only DATA");}
        @Override public ExactRef preserve(NativeActionPort.DispatchOutcome value){throw readOnly();}
        @Override public NativeActionPort.DispatchOutcome load(ExactRef ref){
            raw(ref);if(decoded.containsKey(ref))return (NativeActionPort.DispatchOutcome)decoded.get(ref);
            try{var value=codec.decodeDispatchData(ref);decoded.put(ref,value);return value;}catch(IOException e){throw new UncheckedIOException(e);}
        }
        @Override public ExactRef preserveRequest(NativeRequest value){throw readOnly();}
        @Override public NativeRequest loadRequest(ExactRef ref){
            raw(ref);if(decoded.containsKey(ref))return (NativeRequest)decoded.get(ref);
            try{var value=codec.decodePreparedRequestData(ref);decoded.put(ref,value);return value;}catch(IOException e){throw new UncheckedIOException(e);}
        }
        @Override public ExactRef referenceOf(NativeActionPort.DispatchOutcome value){return existing(value);}
        @Override public ExactRef requestReferenceOf(NativeRequest value){return existing(value);}
        @Override public ExactRef preserveRead(PlanningReadReceipt value){throw readOnly();}
        @Override public PlanningReadReceipt loadRead(ExactRef ref){
            raw(ref);if(decoded.containsKey(ref))return (PlanningReadReceipt)decoded.get(ref);
            try{var value=codec.readData(ref).receipt();decoded.put(ref,value);return value;}catch(IOException e){throw new UncheckedIOException(e);}
        }
        @Override public ExactRef readReferenceOf(PlanningReadReceipt value){return existing(value);}
        @Override public ExactRef preserveRecord(ActionRecord value){throw readOnly();}
        @Override public ActionRecord loadRecord(ExactRef ref){
            byte[] raw=raw(ref);if(decoded.containsKey(ref))return (ActionRecord)decoded.get(ref);
            var value=ActionRecordCodec.decode(raw,this);decoded.put(ref,value);return value;
        }
        @Override public ExactRef recordReferenceOf(ActionRecord value){return existing(value);}
        @Override public ExactRef preserveReceipt(ActionReceipt value){throw readOnly();}
        @Override public ActionReceipt loadReceipt(ExactRef ref){
            byte[] raw=raw(ref);if(decoded.containsKey(ref))return (ActionReceipt)decoded.get(ref);
            var value=ActionReceiptCodec.decodeReceiptUsingCanonicalCommand(raw,this);decoded.put(ref,value);return value;
        }
        @Override public ExactRef receiptReferenceOf(ActionReceipt value){return existing(value);}
        @Override public ExactRef preserveMaterial(RawJson value){throw readOnly();}
        @Override public RawJson loadMaterial(ExactRef ref){
            byte[] raw=raw(ref);if(decoded.containsKey(ref))return (RawJson)decoded.get(ref);
            RawJson value=new RawJson(raw);decoded.put(ref,value);return value;
        }
        @Override public RawJson loadFullMaterial(ExactRef ref){return loadMaterial(ref);}
        @Override public ExactRef materialReferenceOf(RawJson value){return existing(value);}
        @Override public ExactRef preserveNativeFrame(NativeObservationPort.ObservedFrame value){throw readOnly();}
        @Override public byte[] loadNativeFrame(ExactRef ref){return raw(ref);}
        @Override public byte[] readOriginalPacket(ExactRef ref){return raw(ref);}
    }
}
