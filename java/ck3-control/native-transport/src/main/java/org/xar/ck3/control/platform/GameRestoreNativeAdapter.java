package org.xar.ck3.control.platform;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.Arrays;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.NativeRequestChronology;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.IndependentReadPair;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.NativeCandidate;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.ReadWindow;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.ReplacementAck;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Actual replacement READ originals. Cache observation and decoded DATA never mint Root authority. */
public final class GameRestoreNativeAdapter implements RestoreCheckpointService.RestoreNativePort {
    @FunctionalInterface public interface BorrowedSessions { Optional<ContinuityStorePort.Session> current() throws IOException; }
    @FunctionalInterface public interface SessionAuthority { void require(ContinuityStorePort.Session same) throws IOException; }
    @FunctionalInterface private interface Work<T> { T run(ContinuityStorePort.Session same)throws IOException; }
    private final ContinuityStorePort store;
    private final BorrowedSessions borrowed;
    private final SessionAuthority authority;
    private final JavaGameLifecycle lifecycle;
    private final G2Source source;
    private final String lineageId;
    private final ActionPorts.OutcomeArchive archive;
    private final ConcurrentHashMap<String,ReadState> readsByRestore=new ConcurrentHashMap<>();
    private final Map<NativeCandidate,Sample> samples=Collections.synchronizedMap(new IdentityHashMap<>());
    private final Map<IndependentReadPair,PairCustody> pairs=Collections.synchronizedMap(new IdentityHashMap<>());
    private static final int MAX_SAMPLES=1024,MAX_RESTORES=128,MAX_PAIRS=256;
    private static final class ReadState {
        private final ReplacementAck replacement;
        private final FreshReadCustody fresh=new FreshReadCustody();
        private ReadState(ReplacementAck actual){replacement=actual;}
    }
    @FunctionalInterface interface UnavailableRetention {void retain(NativeFreshSnapshotPort.Unavailable original)throws IOException;}
    /** The production read/collect state, independently testable through the real packet receiver; grants no Game authority. */
    static final class FreshReadCustody {
        private String pending;
        private NativeFreshSnapshotPort.Unavailable terminal;
        private NativeFreshSnapshotPort.Received received;
        synchronized NativeFreshSnapshotPort.Received read(NativeFreshSnapshotPort port,Instant deadline,UnavailableRetention originals)throws IOException,InterruptedException {
            Objects.requireNonNull(port);Objects.requireNonNull(originals);Objects.requireNonNull(deadline);
            if(terminal!=null){originals.retain(terminal);throw new IOException("original restore READ terminal unavailability retained; no new dispatch: "+terminal.reason());}
            if(received!=null)return received;
            var result=pending==null?port.readFreshFullState(deadline):port.collectFreshFullState(pending,deadline);
            if(result instanceof NativeFreshSnapshotPort.Received actual){received=actual;return actual;}
            var unavailable=(NativeFreshSnapshotPort.Unavailable)result;pending=unavailable.dispatch().requestId();
            if(unavailable.dispatch() instanceof NativeActionPort.RejectedBeforeDispatch
                    ||unavailable.dispatch() instanceof NativeActionPort.AckReceived rejected&&!rejected.nativeOk())terminal=unavailable;
            // Retain the original result before propagating unavailability; an archive exception cannot clear pending.
            originals.retain(unavailable);
            throw new IOException("ACTUAL_RESTORE_READ_UNAVAILABLE: original dispatch retained: "+unavailable.reason());
        }
        synchronized void archived(NativeFreshSnapshotPort.Received actual)throws IOException {
            if(actual!=received)throw new IOException("restore READ archive acknowledgement is not this retained original");
            pending=null;received=null;
        }
    }
    private record Sample(ReplacementAck replacement,NativeFreshSnapshotPort.Received received,ReadOriginal original){ }
    private record PairCustody(ReplacementAck replacement,PairData data,List<WriterContracts.Pin> pins){ }
    private record ArchivedRead(NativeActionPort.AckReceived ack,NativeObservationPort.ObservedFrame frame,NativeRequestChronology.Event received){ }
    public GameRestoreNativeAdapter(JavaGameLifecycle lifecycle,G2Source source,String lineageId,ActionPorts.OutcomeArchive archive,
            ContinuityStorePort store,BorrowedSessions borrowed,SessionAuthority authority){
        this.lifecycle=Objects.requireNonNull(lifecycle);this.source=Objects.requireNonNull(source);this.archive=Objects.requireNonNull(archive);
        this.store=Objects.requireNonNull(store);this.borrowed=Objects.requireNonNull(borrowed);this.authority=Objects.requireNonNull(authority);
        if(lineageId==null||lineageId.isBlank())throw new IllegalArgumentException("Original lineage required");this.lineageId=lineageId;
    }
    @Override public NativeCandidate observe(ReplacementAck ack,ReadWindow reads)throws IOException,InterruptedException {
        Objects.requireNonNull(ack);Objects.requireNonNull(reads);reads.requireReplacement(ack);Win32Host.deadline(reads.deadline());
        ManagedGameSession session=requireReplacement(ack);
        if(!readsByRestore.containsKey(ack.requestId())&&readsByRestore.size()>=MAX_RESTORES)throw new IOException("bounded restore READ custody exhausted");
        ReadState state=readsByRestore.computeIfAbsent(ack.requestId(),ignored->new ReadState(ack));
        synchronized(state) {
            if(state.replacement!=ack)throw new IOException("restore READ request changed its private replacement");
            if(samples.size()>=MAX_SAMPLES)throw new IOException("bounded restore READ sample custody exhausted");
            NativeFreshSnapshotPort port=session.nativeTransport();
            var actual=state.fresh.read(port,reads.deadline(),unavailable->withWriter(same->{
                var original=archive.withSession(same);original.preserve(unavailable.dispatch());
                if(unavailable.originalFrame().isPresent())original.preserveNativeFrame(unavailable.originalFrame().orElseThrow());return null;
            }));
            NativeFreshSnapshotPort.verifyOriginal(actual.acknowledgement(),actual.originalFrame(),actual.snapshotReceived());
            reads.requireReplacement(ack);if(requireReplacement(ack)!=session)throw new IOException("actual replacement changed during original READ");
            var frame=actual.originalFrame();
            if(!frame.session().game().equals(session.generation())||!frame.session().sessionId().equals(session.sessionId())
                    ||!frame.session().machineId().equals(session.machineId()))throw new IOException("replacement READ native session changed");
            // Keep Received until archive success: an archive exception cannot cause a second request.
            NativeCandidate result=withWriter(same->{
                reads.requireReplacement(ack);var original=archive.withSession(same);var ackRef=original.preserve(actual.acknowledgement());
                var packet=original.preserveNativeFrame(frame);var candidate=new NativeCandidate(frame,source,lineageId,packet);
                var data=new ReadOriginal(ackRef,packet,actual.snapshotReceived().order().toString(),actual.snapshotReceived().observedAt().toString());
                samples.put(candidate,new Sample(ack,actual,data));reads.requireReplacement(ack);return candidate;
            });
            state.fresh.archived(actual);return result;
        }
    }
    private ManagedGameSession requireReplacement(ReplacementAck ack)throws IOException {
        JavaGameLifecycle.ReplacementResult retained=lifecycle.queryReplacement(ack.requestId());
        if(!(retained instanceof JavaGameLifecycle.Replaced replaced)||!replaced.previous().equals(ack.previous())
                ||!replaced.lifecycleEvidence().equals(ack.lifecycleEvidence()))throw new IOException("no same-producer original replacement ACK retained");
        ManagedGameSession session=lifecycle.currentSession().orElseThrow(()->new IOException("original replacement disappeared"));
        if(session!=replaced.replacement().session()||!session.generation().equals(ack.replacement())||!source.machineId().equals(session.machineId())
                ||!(session.launchPlan().load() instanceof NativeLaunchPlan.SavedGame saved)||!LifecycleEvidence.exact(saved.save()).equals(ack.loadedSave()))
            throw new IOException("restore READ belongs to another generation/source/SAVE");
        var proof=ack.lifecycleEvidence();new ControlBuild.FileRef(proof.path(),proof.bytes(),proof.sha256()).verify();
        var origin=source.sourceRef();new ControlBuild.FileRef(origin.path(),origin.bytes(),origin.sha256()).verify();session.verify();return session;
    }
    @Override public IndependentReadPair requireIndependentPair(ReplacementAck ack,NativeCandidate first,NativeCandidate second)throws IOException {
        Sample left=samples.get(first),right=samples.get(second);
        if(left==null||right==null||left==right||left.replacement()!=ack||right.replacement()!=ack)
            throw new IOException("restore pair requires two exact privately retained receiver samples");
        NativeFreshSnapshotPort.verifyOriginal(left.received().acknowledgement(),first.actual(),left.received().snapshotReceived());
        NativeFreshSnapshotPort.verifyAfter(left.received().acknowledgement(),right.received());
        RestoreCheckpointService.requireStableReadProgression(first.actual(),second.actual());
        if(pairs.size()>=MAX_PAIRS)throw new IOException("bounded restore READ pair custody exhausted");
        var data=new PairData(ack.requestId(),ack.lifecycleEvidence(),ack.loadedSave(),left.original(),right.original());
        return withWriter(same->{
            var original=archive.withSession(same);byte[] bytes=data.encode();
            if(!Arrays.equals(bytes,PairData.decode(bytes).encode()))throw new IOException("restore READ DATA round trip changed original roles");
            var manifest=original.preserveMaterial(new RawJson(bytes));
            var pair=new IndependentReadPair(manifest,data.first().acknowledgement(),data.first().nativePacket(),data.second().acknowledgement(),data.second().nativePacket());
            var pins=new java.util.ArrayList<WriterContracts.Pin>();
            for(ExactRef ref:pair.references())pins.add(same.capturePin(ref,WriterContracts.MAX_PIN_BYTES));
            pairs.put(pair,new PairCustody(ack,data,List.copyOf(pins)));requireHistoricalPair(same,ack,pair);return pair;
        });
    }
    @Override public void requireHistoricalPair(ContinuityStorePort.Session same,ReplacementAck ack,IndependentReadPair pair)throws IOException {
        authority.require(same);store.requireSession(same);String head=same.head().digest();PairCustody custody=pairs.get(pair);
        if(custody==null||custody.replacement()!=ack)throw new IOException("decoded restore READ DATA cannot recreate its private receiver issuer");
        for(var pin:custody.pins()){same.readPinned(pin,Math.toIntExact(pin.reference().bytes()));same.verifyPin(pin);}
        try {
            var original=archive.withSession(same);byte[] manifest=original.loadMaterial(pair.manifest()).bytes();var data=PairData.decode(manifest);
            if(!Arrays.equals(data.encode(),custody.data().encode())||!Arrays.equals(manifest,data.encode())
                    ||!data.restoreRequestId().equals(ack.requestId())||!data.lifecycleEvidence().equals(ack.lifecycleEvidence())||!data.loadedSave().equals(ack.loadedSave())
                    ||!pair.firstAck().equals(data.first().acknowledgement())||!pair.firstNative().equals(data.first().nativePacket())
                    ||!pair.secondAck().equals(data.second().acknowledgement())||!pair.secondNative().equals(data.second().nativePacket()))
                throw new IOException("original restore READ manifest roles changed");
            var first=readOriginal(original,data.first());var second=readOriginal(original,data.second());
            NativeFreshSnapshotPort.verifyAfterOriginal(first.ack(),second.ack(),second.frame(),second.received());
            if(!first.frame().session().game().equals(ack.replacement())||!first.frame().session().equals(second.frame().session())
                    ||!first.frame().session().machineId().equals(source.machineId())
                    ||second.frame().nativeRevision().compareTo(first.frame().nativeRevision())<=0
                    ||!RestoreCheckpointService.sameStableReadState(first.frame(),second.frame()))throw new IOException("original restore READ pair crossed Game/source/session/paused state");
            RestoreCheckpointService.requireStableReadProgression(first.frame(),second.frame());
        }catch(UncheckedIOException failure){throw failure.getCause();}
        if(!head.equals(same.head().digest()))throw new IOException("historical READ verification changed the canonical head");
        authority.require(same);store.requireSession(same);
    }
    private static ArchivedRead readOriginal(ActionPorts.OutcomeArchive original,ReadOriginal data)throws IOException {
        var outcome=original.load(data.acknowledgement());
        if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("original restore READ ACK is unavailable");
        var custody=ack.custody().orElseThrow(()->new IOException("original restore READ chronology unavailable"));
        byte[] packet=original.loadNativeFrame(data.nativePacket());var decoded=NativeWire.decode(packet);
        if(!(decoded instanceof NativeWire.Snapshot snapshot))throw new IOException("original restore READ snapshot unavailable");
        var event=new NativeRequestChronology.Event(new BigInteger(data.receivedOrder()),Instant.parse(data.receivedAtUtc()));
        var frame=new NativeObservationPort.ObservedFrame(custody.session(),snapshot.snapshotId(),snapshot.revision(),new RawJson(snapshot.state().value()),packet,event.observedAt());
        NativeFreshSnapshotPort.verifyOriginal(ack,frame,event);return new ArchivedRead(ack,frame,event);
    }
    private <T>T withWriter(Work<T> work)throws IOException {
        try {
            Optional<ContinuityStorePort.Session> active=Objects.requireNonNull(borrowed.current());
            if(active.isPresent()){var same=active.orElseThrow();authority.require(same);store.requireSession(same);T result=work.run(same);authority.require(same);store.requireSession(same);return result;}
            return store.locked(same->{authority.require(same);store.requireSession(same);T result=work.run(same);authority.require(same);store.requireSession(same);return result;});
        }catch(UncheckedIOException failure){throw failure.getCause();}
    }
    /** Closed archive DATA; none of these records constructs Received, ManagedGame or RestoreBinding. */
    record ReadOriginal(ExactRef acknowledgement,ExactRef nativePacket,String receivedOrder,String receivedAtUtc) {
        ReadOriginal {
            Objects.requireNonNull(acknowledgement);Objects.requireNonNull(nativePacket);StrictJson.utc(receivedAtUtc);
            StrictJson.require(acknowledgement.bytes()>0&&nativePacket.bytes()>0,"nonempty original READ DATA artifacts required");
            StrictJson.require(receivedOrder!=null&&receivedOrder.matches("[1-9][0-9]*")&&receivedOrder.length()<=20
                    &&new BigInteger(receivedOrder).compareTo(StrictJson.UINT64_MAX)<=0,"canonical uint64 original READ receive order required");
        }
        ObjectNode toJson(){var row=StrictJson.object();row.set("acknowledgement",acknowledgement.toJson());row.set("native_packet",nativePacket.toJson());
            row.put("received_order",receivedOrder);row.put("received_at_utc",receivedAtUtc);return row;}
        static ReadOriginal decode(JsonNode value){var row=StrictJson.object(value,Set.of("acknowledgement","native_packet","received_order","received_at_utc"));
            return new ReadOriginal(ExactRef.fromJson(row.get("acknowledgement")),ExactRef.fromJson(row.get("native_packet")),StrictJson.text(row.get("received_order")),StrictJson.text(row.get("received_at_utc")));}
    }
    record PairData(String restoreRequestId,ExactRef lifecycleEvidence,ExactRef loadedSave,ReadOriginal first,ReadOriginal second) {
        private static final String SCHEMA="xar.restore.independent-read-pair/v1";
        PairData {StrictJson.text(restoreRequestId);Objects.requireNonNull(lifecycleEvidence);Objects.requireNonNull(loadedSave);Objects.requireNonNull(first);Objects.requireNonNull(second);
            StrictJson.require(lifecycleEvidence.bytes()>0&&loadedSave.bytes()>0,"nonempty original restore lifecycle/SAVE required");
            StrictJson.require(!first.acknowledgement().equals(second.acknowledgement())&&!first.nativePacket().equals(second.nativePacket())
                    &&new BigInteger(first.receivedOrder()).compareTo(new BigInteger(second.receivedOrder()))<0
                    &&!Instant.parse(second.receivedAtUtc()).isBefore(Instant.parse(first.receivedAtUtc())),"ordered independent restore READ DATA required");}
        byte[] encode(){var row=StrictJson.object();row.put("schema",SCHEMA);row.put("restore_request_id",restoreRequestId);row.set("lifecycle_evidence",lifecycleEvidence.toJson());
            row.set("loaded_save",loadedSave.toJson());row.set("first",first.toJson());row.set("second",second.toJson());return StrictJson.canonical(row);}
        static PairData decode(byte[] bytes){var row=StrictJson.object(StrictJson.parse(bytes),Set.of("schema","restore_request_id","lifecycle_evidence","loaded_save","first","second"));
            StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"restore READ DATA schema required");
            return new PairData(StrictJson.text(row.get("restore_request_id")),ExactRef.fromJson(row.get("lifecycle_evidence")),ExactRef.fromJson(row.get("loaded_save")),ReadOriginal.decode(row.get("first")),ReadOriginal.decode(row.get("second")));}
    }
}
