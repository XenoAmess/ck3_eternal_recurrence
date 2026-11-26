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
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.NativeRequestChronology;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.IndependentReadPair;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.NativeCandidate;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.ReadWindow;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService.ReplacementAck;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentAuthority;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore;
import org.xar.ck3.control.application.checkpoint.SavedAttachmentSourceStore.ImportedRecoveryBasis;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.NativeCharacterId;
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
    private final Optional<RootProcessAttach.LoadedReplacement> loadedReplacement;
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
        this(lifecycle,source,lineageId,archive,store,borrowed,authority,Optional.empty());
    }
    public GameRestoreNativeAdapter(JavaGameLifecycle lifecycle,G2Source source,String lineageId,ActionPorts.OutcomeArchive archive,
            ContinuityStorePort store,BorrowedSessions borrowed,SessionAuthority authority,RootProcessAttach.LoadedReplacement actualLoadedReplacement){
        this(lifecycle,source,lineageId,archive,store,borrowed,authority,Optional.of(Objects.requireNonNull(actualLoadedReplacement)));
    }
    private GameRestoreNativeAdapter(JavaGameLifecycle lifecycle,G2Source source,String lineageId,ActionPorts.OutcomeArchive archive,
            ContinuityStorePort store,BorrowedSessions borrowed,SessionAuthority authority,Optional<RootProcessAttach.LoadedReplacement> loadedReplacement){
        this.lifecycle=Objects.requireNonNull(lifecycle);this.source=Objects.requireNonNull(source);this.archive=Objects.requireNonNull(archive);
        this.store=Objects.requireNonNull(store);this.borrowed=Objects.requireNonNull(borrowed);this.authority=Objects.requireNonNull(authority);
        this.loadedReplacement=Objects.requireNonNull(loadedReplacement);
        if(lineageId==null||lineageId.isBlank())throw new IllegalArgumentException("Original lineage required");this.lineageId=lineageId;
    }
    @Override public NativeCandidate observe(ReplacementAck ack,ReadWindow reads)throws IOException,InterruptedException {
        Objects.requireNonNull(ack);Objects.requireNonNull(reads);reads.requireReplacement(ack);Win32Host.deadline(reads.deadline());
        if(loadedReplacement.isPresent())loadedReplacement.orElseThrow().requireOriginalRequest(reads.original());
        ManagedGameSession session=requireReplacement(ack,reads.deadline());
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
            reads.requireReplacement(ack);if(requireReplacement(ack,reads.deadline())!=session)throw new IOException("actual replacement changed during original READ");
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
    private ManagedGameSession requireReplacement(ReplacementAck ack,Instant readDeadline)throws IOException {
        if(loadedReplacement.isPresent()){
            var actual=loadedReplacement.orElseThrow();actual.requireAck(ack,readDeadline);ManagedGameSession session=actual.attached();
            var originalSave=actual.pair().save();
            boolean exactSave=ack.importedSaveTransfer().map(transfer->transfer.original().equals(originalSave)
                    &&transfer.staged().reference().equals(ack.loadedSave()))
                    .orElseGet(()->originalSave.reference().equals(ack.loadedSave()));
            if(!session.generation().equals(ack.replacement())||!session.machineId().equals(source.machineId())
                    ||!actual.pair().lineageId().equals(lineageId)||!exactSave)
                throw new IOException("loaded replacement READ crossed its exact Game/source/SAVE lineage");
            var origin=source.sourceRef();new ControlBuild.FileRef(origin.path(),origin.bytes(),origin.sha256()).verify();return session;
        }
        JavaGameLifecycle.ReplacementResult retained=lifecycle.queryReplacement(ack.requestId());
        if(!(retained instanceof JavaGameLifecycle.Replaced replaced)||!replaced.previous().equals(ack.previous())
                ||!replaced.lifecycleEvidence().equals(ack.lifecycleEvidence())
                ||!replaced.importedSaveTransfer().equals(ack.importedSaveTransfer()))
            throw new IOException("no same-producer original replacement ACK/load transfer retained");
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
        var transfer=ack.importedSaveTransfer().map(RestoreCheckpointService.ImportedSaveTransfer::proof);
        var data=new PairData(ack.requestId(),ack.lifecycleEvidence(),ack.loadedSave(),left.original(),right.original(),transfer);
        return withWriter(same->{
            var original=archive.withSession(same);byte[] bytes=data.encode();
            if(!Arrays.equals(bytes,PairData.decode(bytes).encode()))throw new IOException("restore READ DATA round trip changed original roles");
            var manifest=original.preserveMaterial(new RawJson(bytes));
            var pair=new IndependentReadPair(manifest,data.first().acknowledgement(),data.first().nativePacket(),data.second().acknowledgement(),data.second().nativePacket());
            var pins=new java.util.ArrayList<WriterContracts.Pin>();
            for(ExactRef ref:pair.references())pins.add(same.capturePin(ref,WriterContracts.MAX_PIN_BYTES));
            if(transfer.isPresent()) pins.add(same.capturePin(transfer.orElseThrow(),WriterContracts.MAX_PIN_BYTES));
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
                    ||!data.importedSaveTransfer().equals(ack.importedSaveTransfer().map(RestoreCheckpointService.ImportedSaveTransfer::proof))
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
    /** Historical packet data tied to the one actual attachment edge, retaining its original connection. */
    public record CommittedImportedReads(WriterContracts.HistoricalTransition attachment,ImportedRecoveryBasis basis,
            NativeObservationPort.ObservedFrame firstOriginal,NativeObservationPort.ObservedFrame secondOriginal) { }

    /** Reads the immediate committed imported attachment from this writer and the same now reattached successor. */
    public CommittedImportedReads readCommittedImportedOriginals(ContinuityStorePort.Session same,
            WriterContracts.Pin actualAttachment,Instant readDeadline)throws IOException {
        authority.require(same);store.requireSession(same);
        var loaded=loadedReplacement.orElseThrow(()->new IOException("Committed imported READ recovery requires its actual attached successor owner"));
        loaded.requireMembership(readDeadline);
        var committed=readCommittedAttachment(same,actualAttachment);
        var basis=committed.basis();var ack=loaded.cachedAck();
        var transfer=ack.importedSaveTransfer().orElseThrow(()->new IOException("Committed imported recovery requires the original transferred LOAD"));
        if(!committed.pair().equals(loaded.pair())||!lineageId.equals(committed.pair().lineageId())
                ||!source.machineId().equals(basis.successor().machineId())||!basis.departed().equals(loaded.previousOwner())
                ||!basis.requestId().equals(loaded.originalParentId())||!basis.lifecycleDeadline().equals(loaded.originalDeadline())
                ||!basis.lifecycleControl().reference().equals(loaded.parentControl())||!basis.transferProof().reference().equals(transfer.proof())
                ||!basis.stagedLoad().equals(transfer.staged().reference())||!committed.pair().save().equals(transfer.original()))
            throw new IOException("Committed imported READ recovery crossed its original lifecycle, physical pair or stage");
        loaded.requireCurrent(readDeadline);
        var attached=loaded.attached();var current=attached.nativeTransport().diagnostics().session()
                .orElseThrow(()->new IOException("Actual successor Native READ session is absent"));
        try {
            var result=readCommittedPair(same,archive.withSession(same),committed,current);
            loaded.requireMembership(readDeadline);attached.verify();
            var checked=attached.nativeTransport().diagnostics();
            if(checked.session().filter(current::equals).isEmpty()||checked.terminalFailure().isPresent())
                throw new IOException("Actual successor Native session changed during committed history read");
            authority.require(same);store.requireSession(same);return result;
        } catch(UncheckedIOException failure){throw failure.getCause();}
    }

    record CommittedAttachment(WriterContracts.HistoricalTransition edge,ImportedRecoveryBasis basis,CheckpointPair pair,ObjectNode opening) { }

    static CommittedAttachment readCommittedAttachment(ContinuityStorePort.Session same,WriterContracts.Pin event)throws IOException {
        var head=same.head();var edge=same.readHistoricalTransition(event);
        if(!SavedAttachmentAuthority.KIND.equals(edge.kind())||head.snapshotNeedsRecovery()||!head.indexRepairs().isEmpty()
                ||edge.sequence()!=head.state().sequence()||!ContinuityJson.digest(edge.after().toJson()).equals(head.digest()))
            throw new IOException("Immediate clean committed imported attachment required");
        try {
            var details=ContinuityJson.parseObject(edge.details(),ContinuityJson.DOCUMENT_MAX_BYTES);
            var basis=SavedAttachmentSourceStore.importedRecoveryBasis(details)
                    .orElseThrow(()->new IOException("Original committed imported READ basis was not recorded"));
            var sources=SavedAttachmentSourceStore.Sources.decode(details.get(SavedAttachmentSourceStore.SOURCES_DETAIL));
            var origin=sources.importedOrigin().orElseThrow(()->new IOException("Committed READ basis requires its actual imported source occurrence"));
            var pair=CheckpointPairCodec.decode(ContinuityJson.canonical(details.get(SavedAttachmentAuthority.PAIR_DETAIL)));
            var before=edge.before().toJson();var after=edge.after().toJson();
            var opening=ContinuityJson.object(after.get("latest_binding"));
            if(edge.before().sequence()!=basis.predecessorSequence()||!ContinuityJson.digest(before).equals(basis.predecessorDigest())
                    ||!basis.requestId().equals(StrictJson.text(details.get("evidence_id")))||!basis.departed().equals(origin.owner())
                    ||!basis.departed().game().equals(GameGeneration.fromJson(before.get("game_binding")))
                    ||!basis.successor().game().equals(GameGeneration.fromJson(after.get("game_binding")))
                    ||!basis.successor().equals(openingOwner(opening))||!basis.successor().machineId().equals(edge.after().machineId())
                    ||!pair.save().equals(sources.physicalSaveWitness().orElse(null))
                    ||!basis.secondNative().reference().equals(sources.restoredNative())
                    ||!basis.secondNative().reference().equals(ExactRef.fromJson(opening.get("original_native_packet")))
                    ||!pair.lineageId().equals(StrictJson.text(opening.get("lineage_id")))
                    ||!pair.frame().frame().episodeRunId().equals(StrictJson.text(opening.get("episode_run_id"))))
                throw new IOException("Committed imported READ basis differs from its canonical predecessor, successor, physical pair or opening");
            return new CommittedAttachment(edge,basis,pair,opening);
        }catch(IllegalArgumentException|java.time.DateTimeException invalid){throw new IOException("Invalid committed imported attachment DATA",invalid);}
    }

    private static SessionIdentity openingOwner(ObjectNode opening) {
        return new SessionIdentity(StrictJson.text(opening.get("machine_id")),GameGeneration.fromJson(opening.get("game")),
                StrictJson.text(opening.get("session_id")));
    }

    static CommittedImportedReads readCommittedPair(ContinuityStorePort.Session same,ActionPorts.OutcomeArchive original,
            CommittedAttachment committed,NativeObservationPort.TransportSession attached)throws IOException {
        var basis=committed.basis();var owner=basis.successor();
        if(!owner.equals(new SessionIdentity(attached.machineId(),attached.game(),attached.sessionId())))
            throw new IOException("Committed READ recovery requires the actual same successor owner");
        for(var pin:basis.pins())same.verifyPin(pin);
        var manifest=same.readPinned(basis.readManifest(),65536);
        try {
            var pair=PairData.decode(manifest);
            if(!Arrays.equals(manifest,pair.encode())||!Arrays.equals(manifest,original.loadMaterial(basis.readManifest().reference()).bytes()))
                throw new IOException("Committed original independent READ manifest differs from its exact archive Pin");
            requireCommittedPairRoles(pair,basis);
            var first=readPinnedOriginal(same,original,pair.first(),basis.firstReadAck(),basis.firstNative());
            var second=readPinnedOriginal(same,original,pair.second(),basis.secondReadAck(),basis.secondNative());
            NativeFreshSnapshotPort.verifyAfterOriginal(first.ack(),second.ack(),second.frame(),second.received());
            RestoreCheckpointService.requireStableReadProgression(first.frame(),second.frame());
            var historical=second.frame().session();
            if(!owner.equals(new SessionIdentity(historical.machineId(),historical.game(),historical.sessionId()))
                    ||attached.connectionGeneration().compareTo(historical.connectionGeneration())<=0)
                throw new IOException("Historical READs must retain their original connection before this actual successor attachment");
            requireCommittedOpening(committed,second.frame());
            for(var pin:basis.pins())same.verifyPin(pin);
            if(!same.head().digest().equals(ContinuityJson.digest(committed.edge().after().toJson())))
                throw new IOException("Committed original READ verification changed the canonical head");
            return new CommittedImportedReads(committed.edge(),basis,first.frame(),second.frame());
        }catch(IllegalArgumentException|java.time.DateTimeException invalid){throw new IOException("Invalid committed original READ archive DATA",invalid);}
    }

    static void requireCommittedPairRoles(PairData pair,ImportedRecoveryBasis basis)throws IOException {
        if(!pair.restoreRequestId().equals(basis.requestId())||!pair.lifecycleEvidence().equals(basis.lifecycleControl().reference())
                ||!pair.loadedSave().equals(basis.stagedLoad())||!pair.importedSaveTransfer().equals(Optional.of(basis.transferProof().reference()))
                ||!pair.first().acknowledgement().equals(basis.firstReadAck().reference())||!pair.first().nativePacket().equals(basis.firstNative().reference())
                ||!pair.second().acknowledgement().equals(basis.secondReadAck().reference())||!pair.second().nativePacket().equals(basis.secondNative().reference()))
            throw new IOException("Committed original independent READ manifest crossed its labeled Pins");
    }

    private static ArchivedRead readPinnedOriginal(ContinuityStorePort.Session same,ActionPorts.OutcomeArchive archive,
            ReadOriginal original,WriterContracts.Pin ack,WriterContracts.Pin packet)throws IOException {
        byte[] receipt=same.readPinned(ack,DriverJson.MAX_NATIVE_BYTES+4);
        if(!Arrays.equals(receipt,archive.loadMaterial(original.acknowledgement()).bytes()))
            throw new IOException("Original committed restore ACK differs from its exact archive Pin");
        byte[] bytes=same.readPinned(packet,DriverJson.MAX_NATIVE_BYTES+4);
        if(!Arrays.equals(bytes,archive.loadNativeFrame(original.nativePacket())))
            throw new IOException("Original committed restore snapshot differs from its exact archive Pin");
        return readOriginal(archive,original,bytes);
    }

    private static void requireCommittedOpening(CommittedAttachment committed,NativeObservationPort.ObservedFrame second)throws IOException {
        var opening=committed.opening();var physical=committed.pair().frame().frame().identity();
        var state=FullJsonTree.parse(second.state().bytes(),DriverJson.MAX_NATIVE_BYTES);var actor=state.get("played_character");
        if(!second.snapshotId().equals(StrictJson.text(opening.get("snapshot_id")))
                ||!second.nativeRevision().toString().equals(StrictJson.text(opening.get("native_revision")))
                ||!physical.player().equals(NativeCharacterId.fromJson(opening.get("actor_character_id")).asBigInteger())
                ||physical.dateRaw().longValueExact()!=StrictJson.integer(opening.get("date_raw"),0,StrictJson.MAX_SAFE_INTEGER)
                ||physical.dateRaw().longValueExact()!=StrictJson.integer(state.get("date_raw"),0,StrictJson.MAX_SAFE_INTEGER)
                ||!state.path("map_ready").isBoolean()||!state.path("map_ready").booleanValue()
                ||!state.path("paused").isBoolean()||!state.path("paused").booleanValue()
                ||actor==null||!actor.path("alive").isBoolean()||!actor.path("alive").booleanValue()
                ||!physical.player().equals(NativeCharacterId.fromJson(actor.get("character_id")).asBigInteger()))
            throw new IOException("Historical second READ differs from the committed paused opening and original SAVE actor/date");
    }

    private static ArchivedRead readOriginal(ActionPorts.OutcomeArchive original,ReadOriginal data)throws IOException {
        return readOriginal(original,data,null);
    }
    private static ArchivedRead readOriginal(ActionPorts.OutcomeArchive original,ReadOriginal data,byte[] pinnedPacket)throws IOException {
        var outcome=original.load(data.acknowledgement());
        if(!(outcome instanceof NativeActionPort.AckReceived ack))throw new IOException("original restore READ ACK is unavailable");
        var custody=ack.custody().orElseThrow(()->new IOException("original restore READ chronology unavailable"));
        byte[] packet=pinnedPacket!=null?pinnedPacket:original.loadNativeFrame(data.nativePacket());var decoded=NativeWire.decode(packet);
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
    record PairData(String restoreRequestId,ExactRef lifecycleEvidence,ExactRef loadedSave,ReadOriginal first,
            ReadOriginal second,Optional<ExactRef> importedSaveTransfer) {
        private static final String SCHEMA="xar.restore.independent-read-pair/v1";
        private static final String IMPORTED_SCHEMA="xar.restore.independent-read-pair/v2";
        private static final Set<String> FIELDS=Set.of("schema","restore_request_id","lifecycle_evidence","loaded_save","first","second");
        private static final Set<String> IMPORTED_FIELDS=Set.of("schema","restore_request_id","lifecycle_evidence","loaded_save","first","second","imported_save_transfer");
        PairData(String restoreRequestId,ExactRef lifecycleEvidence,ExactRef loadedSave,ReadOriginal first,ReadOriginal second) {
            this(restoreRequestId,lifecycleEvidence,loadedSave,first,second,Optional.empty());
        }
        PairData {
            StrictJson.text(restoreRequestId);Objects.requireNonNull(lifecycleEvidence);Objects.requireNonNull(loadedSave);
            Objects.requireNonNull(first);Objects.requireNonNull(second);Objects.requireNonNull(importedSaveTransfer);
            StrictJson.require(lifecycleEvidence.bytes()>0&&loadedSave.bytes()>0
                    &&importedSaveTransfer.map(ref->ref.bytes()>0).orElse(true),"nonempty original restore lifecycle/SAVE required");
            StrictJson.require(!first.acknowledgement().equals(second.acknowledgement())&&!first.nativePacket().equals(second.nativePacket())
                    &&new BigInteger(first.receivedOrder()).compareTo(new BigInteger(second.receivedOrder()))<0
                    &&!Instant.parse(second.receivedAtUtc()).isBefore(Instant.parse(first.receivedAtUtc())),"ordered independent restore READ DATA required");
        }
        byte[] encode() {
            var row=StrictJson.object();row.put("schema",importedSaveTransfer.isPresent()?IMPORTED_SCHEMA:SCHEMA);
            row.put("restore_request_id",restoreRequestId);row.set("lifecycle_evidence",lifecycleEvidence.toJson());row.set("loaded_save",loadedSave.toJson());
            row.set("first",first.toJson());row.set("second",second.toJson());
            importedSaveTransfer.ifPresent(ref->row.set("imported_save_transfer",ref.toJson()));
            return StrictJson.canonical(row);
        }
        static PairData decode(byte[] bytes) {
            var raw=StrictJson.parse(bytes);String schema=StrictJson.text(raw.get("schema"));
            StrictJson.require(SCHEMA.equals(schema)||IMPORTED_SCHEMA.equals(schema),"restore READ DATA schema required");
            boolean imported=IMPORTED_SCHEMA.equals(schema);
            var row=StrictJson.object(raw,imported?IMPORTED_FIELDS:FIELDS);
            return new PairData(StrictJson.text(row.get("restore_request_id")),ExactRef.fromJson(row.get("lifecycle_evidence")),
                    ExactRef.fromJson(row.get("loaded_save")),ReadOriginal.decode(row.get("first")),ReadOriginal.decode(row.get("second")),
                    imported?Optional.of(ExactRef.fromJson(row.get("imported_save_transfer"))):Optional.empty());
        }
    }
}
