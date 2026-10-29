package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeObservationPort;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.NativeRequestChronology;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointPairCodec;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.lifecycle.LifecycleProofCodec;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.OriginalLegacyResume;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.nativebridge.NativeFreshSnapshotPort;
import org.xar.ck3.control.nativebridge.NativeWire;

/** A new cold issuer from actual private bootstrap, two native READs and the real installed Root.
 * The existing COLD_CHECKPOINT migration is the one canonical attachment. No second commit, CAS,
 * process replacement, saved-material relabelling or resurrection of an old daemon issuer occurs here.
 */
public final class RootColdReboundRuntime {
    private RootColdReboundRuntime(){ }

    /** Call only after Core's original migration commit/adopt and this context's real catalog/physical binding. */
    public static ColdReboundOrigin complete(RootPrivateBootstrap.Original original,RootRuntimeContext context,Instant deadline)
            throws IOException,InterruptedException {
        Objects.requireNonNull(original);Objects.requireNonNull(context);Objects.requireNonNull(deadline);
        requireContext(original,context);context.requireCurrent(deadline);sources(context);
        context.withSession(same->{original.requireCurrent(same,context);return null;});
        // These are actual independent transport calls after Legacy's last-packet-sensitive commit/adopt window.
        var firstRead=fresh(context,deadline);var first=firstRead.originalFrame();
        var firstOriginal=context.withSession(same->preserveRead(same,context,firstRead));
        var secondRead=fresh(context,deadline);var second=secondRead.originalFrame();
        var secondOriginal=context.withSession(same->preserveRead(same,context,secondRead));
        NativeFreshSnapshotPort.verifyAfter(firstRead.acknowledgement(),secondRead);
        StrictJson.require(secondRead.acknowledgement().custody().orElseThrow().writeEntered().order().compareTo(firstRead.snapshotReceived().order())>0,
                "second cold full-state READ did not follow the actual first snapshot receive");
        requireRaw(original,context,first);requireRaw(original,context,second);
        StrictJson.require(first.session().equals(second.session())&&first.nativeRevision().equals(second.nativeRevision())
                &&Arrays.equals(first.state().bytes(),second.state().bytes()),"independent cold restored paused READs changed Game/transport/revision/state");
        return context.withSession(same->{
            original.requireCurrent(same,context);requireContext(original,context);sources(context);
            var domains=context.remainingDomains();domains.lifecycle().requireContext(context);
            var physical=domains.lifecycle().physical();
            var owner=new SessionIdentity(context.game().machineId(),context.game().generation(),context.game().sessionId());
            return physical.withSnapshot(same,deadline,lease->{
                lease.assertCurrent(same);original.requireCurrent(same,context);
                var qualified=lease.sourceQualification();qualified.assertCurrent(same);
                var metadata=context.sources().optionalMetadata(same,qualified);if(metadata.isPresent())metadata.orElseThrow().requireCurrent(same);
                var complete=lease.ordinary().orElseThrow(()->new IOException("actual cold Root has no complete living physical Driver/SEM"));
                var known=lease.factsKnown();var full=lease.fullSnapshot();requireRaw(original,context,full.actual());
                StrictJson.require(full.actual().session().equals(second.session())
                        &&full.actual().snapshotId().equals(second.snapshotId())&&Arrays.equals(full.actual().originalPacket(),second.originalPacket())
                        &&full.actual().nativeRevision().equals(second.nativeRevision())
                        &&Arrays.equals(full.actual().state().bytes(),second.state().bytes())
                        &&complete.connectionGeneration().equals(second.session().connectionGeneration())
                        &&complete.source().equals(context.source())&&complete.sessionId().equals(owner.sessionId())
                        &&complete.identity().game().equals(owner.game())&&complete.identity().machineId().equals(owner.machineId())
                        &&known.stamp().game().equals(owner.game())&&known.driver().session().bridgePid()==owner.game().pid()
                        &&known.driver().session().episodeRunId().equals(original.pair().frame().frame().episodeRunId())
                        &&known.driver().session().actorId().equals(original.pair().frame().frame().identity().player())
                        &&Arrays.equals(full.facts().driver().encode(),known.driver().encode()),
                        "actual cold Root current full Driver/source/transport differs from the privately adopted Game");
                var semantic=physical.semantic(same,owner,lease);
                StrictJson.require(semantic.frame().equals(complete.identity()),"actual cold physical SEM does not name its held complete frame");
                var migration=originalMigration(same,original);
                String head=same.head().digest();long sequence=same.head().state().sequence();
                var refs=new LinkedHashSet<ExactRef>();refs.add(original.evidence());refs.add(firstOriginal.acknowledgement().reference());refs.add(firstOriginal.nativePacket().reference());
                refs.add(secondOriginal.acknowledgement().reference());refs.add(secondOriginal.nativePacket().reference());refs.addAll(semantic.references());
                refs.add(lease.originalHello());refs.add(lease.originalHeartbeat());qualified.proof().ifPresent(refs::add);refs.add(full.facts().semanticFactsEvidence());
                var pins=new ArrayList<WriterContracts.Pin>();
                for(var ref:refs)pins.add(pin(same,ref));
                var data=new Data(original.pair(),owner,context.source(),second.session().connectionGeneration().toString(),
                        migration.eventPin(),find(pins,original.evidence()),firstOriginal,secondOriginal,semantic,
                        known.stamp().driverVersion(),known.stamp().episodeEpoch(),head,sequence,List.copyOf(pins));
                // A DATA round trip never substitutes for either the private bootstrap or this held physical scope.
                StrictJson.require(Arrays.equals(data.encode(),Data.decode(data.encode()).encode()),"actual cold rebound DATA round trip changed identity or JSON types");
                var basis=context.archive().withSession(same).preserveMaterial(new RawJson(data.encode()));
                var basisPin=pin(same,basis);
                var result=new ColdReboundOrigin(original,context,data,basisPin);
                result.requireOriginal(same);qualified.assertCurrent(same);if(metadata.isPresent())metadata.orElseThrow().requireCurrent(same);lease.assertCurrent(same);
                StrictJson.require(head.equals(same.head().digest()),"cold rebound publication wrote a second canonical attachment");
                context.bindColdReboundOrigin(same,result);result.requireOriginal(same);return result;
            });
        });
    }

    /** Opaque new-daemon provenance. DATA decode, an old RestoreBinding and a reader cannot construct it. */
    public static final class ColdReboundOrigin {
        private final RootPrivateBootstrap.Original original;
        private final RootRuntimeContext context;
        private final Data data;
        private final WriterContracts.Pin dataOriginal;
        private ColdReboundOrigin(RootPrivateBootstrap.Original original,RootRuntimeContext context,Data data,WriterContracts.Pin dataOriginal) {
            this.original=original;this.context=context;this.data=data;this.dataOriginal=dataOriginal;
        }
        public RootRuntimeContext context(){return context;}
        public Data data(){return data;}
        public ExactRef originalData(){return dataOriginal.reference();}
        public long newSavedDayCredit(){return 0;}
        public long newCycleCredit(){return 0;}
        /** Historical originals only. This does not retain or revive a physical SnapshotLease/current permission. */
        public void requireOriginal(ContinuityStorePort.Session same)throws IOException {
            context.writer().requireSession(same);original.requireOriginal(same);requireContext(original,context);
            var migration=originalMigration(same,original);
            StrictJson.require(migration.eventPin().equals(data.migrationEvent())&&data.pair().equals(original.pair())
                    &&data.owner().game().equals(original.game().generation())&&data.owner().sessionId().equals(original.game().sessionId())
                    &&data.source().equals(context.source()),"cold rebound lost its actual private cold attachment/Game/source");
            for(var pin:data.proofPins())verify(same,pin);
            var first=readOriginal(same,context,data.firstRead());var second=readOriginal(same,context,data.secondRead());
            NativeFreshSnapshotPort.verifyAfterOriginal(first.acknowledgement(),second.acknowledgement(),second.frame(),second.received());
            requireRaw(original,context,first.frame());requireRaw(original,context,second.frame());
            StrictJson.require(first.frame().session().equals(second.frame().session())
                    &&first.frame().nativeRevision().equals(second.frame().nativeRevision())&&Arrays.equals(first.frame().state().bytes(),second.frame().state().bytes())
                    &&second.frame().session().connectionGeneration().toString().equals(data.connectionGeneration()),
                    "historical cold independent READ originals changed state, transport or connection");
            context.semanticVerifier().verify(same,data.owner(),data.semantic());
            verify(same,dataOriginal);
            StrictJson.require(Arrays.equals(data.encode(),same.readPinned(dataOriginal,Math.toIntExact(dataOriginal.reference().bytes()))),
                    "actual original cold rebound DATA changed");
            same.requireHistoricalState(data.captureSequence(),data.captureHeadDigest());
            context.writer().requireSession(same);
        }
    }

    /** Explicit cold wire domain. It makes no claim that a previous live process was stopped by this daemon. */
    public record Data(CheckpointPair pair,SessionIdentity owner,G2Source source,String connectionGeneration,
            WriterContracts.Pin migrationEvent,WriterContracts.Pin bootstrapEvidence,ReadOriginal firstRead,
            ReadOriginal secondRead,SemanticEvidence semantic,long driverVersion,long episodeEpoch,
            String captureHeadDigest,long captureSequence,List<WriterContracts.Pin> proofPins) {
        public static final String SCHEMA="xar.java-cold-rebound-original/v1";
        public static final int MAXIMUM_BYTES=1024*1024;
        private static final Set<String> FIELDS=Set.of("schema","pair","owner","source","connection_generation","migration_event",
                "bootstrap_evidence","first_read","second_read","semantic","driver_version","episode_epoch","capture_head_sha256","capture_sequence","proof_pins");
        public Data {
            Objects.requireNonNull(pair);Objects.requireNonNull(owner);Objects.requireNonNull(source);Objects.requireNonNull(semantic);
            Objects.requireNonNull(migrationEvent);Objects.requireNonNull(bootstrapEvidence);Objects.requireNonNull(firstRead);Objects.requireNonNull(secondRead);
            proofPins=List.copyOf(proofPins);StrictJson.safe(driverVersion,0);StrictJson.safe(episodeEpoch,0);StrictJson.safe(captureSequence,1);
            WriterContracts.requireDigest(captureHeadDigest);
            StrictJson.require(connectionGeneration!=null&&connectionGeneration.matches("[1-9][0-9]*")&&connectionGeneration.length()<=20
                    &&new java.math.BigInteger(connectionGeneration).bitLength()<=64,"canonical decimal cold connection required");
            StrictJson.require(!pair.frame().game().equals(owner.game())&&pair.frame().machineId().equals(owner.machineId())
                    &&source.machineId().equals(owner.machineId())&&semantic.frame().game().equals(owner.game())
                    &&semantic.frame().machineId().equals(owner.machineId())
                    &&semantic.frame().frame().episodeRunId().equals(pair.frame().frame().episodeRunId())
                    &&semantic.frame().frame().identity().player().equals(pair.frame().frame().identity().player())
                    &&semantic.frame().frame().identity().dateRaw().equals(pair.frame().frame().identity().dateRaw())
                    &&semantic.originalNativePacket().equals(secondRead.nativePacket().reference())
                    &&!proofPins.isEmpty()&&proofPins.size()<=32&&Set.copyOf(proofPins).size()==proofPins.size()
                    &&proofPins.containsAll(List.of(bootstrapEvidence,firstRead.acknowledgement(),firstRead.nativePacket(),secondRead.acknowledgement(),secondRead.nativePacket()))
                    &&proofPins.stream().map(WriterContracts.Pin::reference).toList().containsAll(semantic.references()),
                    "cold original DATA must retain its saved-vs-current Game, actual episode and complete original pin roles");
        }
        public byte[] encode() {
            var row=StrictJson.object();row.put("schema",SCHEMA);row.set("pair",StrictJson.parse(CheckpointPairCodec.encode(pair)));
            row.set("owner",OrdinaryCycleTransitions.sessionToJson(owner));row.set("source",StrictJson.parse(G2Wire.sourceBytes(source)));
            row.put("connection_generation",connectionGeneration);row.set("migration_event",LifecycleProofCodec.encodePin(migrationEvent));
            row.set("bootstrap_evidence",LifecycleProofCodec.encodePin(bootstrapEvidence));row.set("first_read",firstRead.toJson());
            row.set("second_read",secondRead.toJson());row.set("semantic",OrdinaryCycleTransitions.semanticToJson(semantic));
            row.put("driver_version",driverVersion);row.put("episode_epoch",episodeEpoch);row.put("capture_head_sha256",captureHeadDigest);
            row.put("capture_sequence",captureSequence);var pins=row.putArray("proof_pins");proofPins.forEach(pin->pins.add(LifecycleProofCodec.encodePin(pin)));
            return StrictJson.canonical(row,MAXIMUM_BYTES);
        }
        public static Data decode(byte[] raw) {
            var row=StrictJson.object(StrictJson.parse(raw,MAXIMUM_BYTES),FIELDS);
            StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema")))&&row.get("proof_pins").isArray(),"cold original schema/pin array required");
            var pins=new ArrayList<WriterContracts.Pin>();row.get("proof_pins").forEach(pin->pins.add(LifecycleProofCodec.decodePin(pin)));
            return new Data(CheckpointPairCodec.decode(StrictJson.canonical(row.get("pair"))),OrdinaryCycleTransitions.sessionFromJson(row.get("owner")),
                    G2Wire.source(row.get("source")),StrictJson.text(row.get("connection_generation")),LifecycleProofCodec.decodePin(row.get("migration_event")),
                    LifecycleProofCodec.decodePin(row.get("bootstrap_evidence")),ReadOriginal.fromJson(row.get("first_read")),ReadOriginal.fromJson(row.get("second_read")),
                    OrdinaryCycleTransitions.semanticFromJson(row.get("semantic")),StrictJson.integer(row.get("driver_version"),0,StrictJson.MAX_SAFE_INTEGER),
                    StrictJson.integer(row.get("episode_epoch"),0,StrictJson.MAX_SAFE_INTEGER),StrictJson.text(row.get("capture_head_sha256")),
                    StrictJson.integer(row.get("capture_sequence"),1,StrictJson.MAX_SAFE_INTEGER),pins);
        }
    }
    /** Immutable archived READ roles; decode grants neither Received nor native/source custody. */
    public record ReadOriginal(WriterContracts.Pin acknowledgement,WriterContracts.Pin nativePacket,
            String snapshotReceivedOrder,String snapshotReceivedAtUtc) {
        public ReadOriginal {
            Objects.requireNonNull(acknowledgement);Objects.requireNonNull(nativePacket);StrictJson.utc(snapshotReceivedAtUtc);
            StrictJson.require(snapshotReceivedOrder!=null&&snapshotReceivedOrder.matches("[1-9][0-9]*")&&snapshotReceivedOrder.length()<=128,
                    "canonical positive actual READ receive order required");
        }
        ObjectNode toJson() {
            var row=StrictJson.object();row.set("acknowledgement",LifecycleProofCodec.encodePin(acknowledgement));
            row.set("native_packet",LifecycleProofCodec.encodePin(nativePacket));row.put("snapshot_received_order",snapshotReceivedOrder);
            row.put("snapshot_received_at_utc",snapshotReceivedAtUtc);return row;
        }
        static ReadOriginal fromJson(com.fasterxml.jackson.databind.JsonNode value) {
            var row=StrictJson.object(value,Set.of("acknowledgement","native_packet","snapshot_received_order","snapshot_received_at_utc"));
            return new ReadOriginal(LifecycleProofCodec.decodePin(row.get("acknowledgement")),LifecycleProofCodec.decodePin(row.get("native_packet")),
                    StrictJson.text(row.get("snapshot_received_order")),StrictJson.text(row.get("snapshot_received_at_utc")));
        }
    }
    private record ArchivedRead(NativeActionPort.AckReceived acknowledgement,NativeObservationPort.ObservedFrame frame,NativeRequestChronology.Event received){ }
    private static NativeFreshSnapshotPort.Received fresh(RootRuntimeContext context,Instant deadline)throws IOException,InterruptedException {
        NativeFreshSnapshotPort actualPort=context.transport();var result=actualPort.readFreshFullState(deadline);
        if(result instanceof NativeFreshSnapshotPort.Received actual) {
            NativeFreshSnapshotPort.verifyOriginal(actual.acknowledgement(),actual.originalFrame(),actual.snapshotReceived());return actual;
        }
        var unavailable=(NativeFreshSnapshotPort.Unavailable)result;
        context.withSession(same->{
            var archive=context.archive().withSession(same);archive.preserve(unavailable.dispatch());
            if(unavailable.originalFrame().isPresent())archive.preserveNativeFrame(unavailable.originalFrame().orElseThrow());return null;
        });
        throw new IOException("ACTUAL_COLD_READ_UNAVAILABLE: original dispatch retained without a new request: "+unavailable.reason());
    }
    private static ReadOriginal preserveRead(ContinuityStorePort.Session same,RootRuntimeContext context,NativeFreshSnapshotPort.Received actual)throws IOException {
        NativeFreshSnapshotPort.verifyOriginal(actual.acknowledgement(),actual.originalFrame(),actual.snapshotReceived());
        var archive=context.archive().withSession(same);archive.preserve(actual.acknowledgement());
        var ack=pin(same,archive.referenceOf(actual.acknowledgement()));var packet=pin(same,archive.preserveNativeFrame(actual.originalFrame()));
        return new ReadOriginal(ack,packet,actual.snapshotReceived().order().toString(),actual.snapshotReceived().observedAt().toString());
    }
    private static ArchivedRead readOriginal(ContinuityStorePort.Session same,RootRuntimeContext context,ReadOriginal original)throws IOException {
        verify(same,original.acknowledgement());verify(same,original.nativePacket());var archive=context.archive().withSession(same);
        var dispatch=archive.load(original.acknowledgement().reference());
        if(!(dispatch instanceof NativeActionPort.AckReceived ack))throw new IOException("actual cold READ ACK original metadata is absent");
        var custody=ack.custody().orElseThrow(()->new IOException("actual cold READ original custody is absent"));
        byte[] packet=archive.loadNativeFrame(original.nativePacket().reference());var decoded=NativeWire.decode(packet);
        if(!(decoded instanceof NativeWire.Snapshot snapshot))throw new IOException("actual cold READ original full-state packet is absent");
        var event=new NativeRequestChronology.Event(new BigInteger(original.snapshotReceivedOrder()),Instant.parse(original.snapshotReceivedAtUtc()));
        var frame=new NativeObservationPort.ObservedFrame(custody.session(),snapshot.snapshotId(),snapshot.revision(),new RawJson(snapshot.state().value()),packet,event.observedAt());
        NativeFreshSnapshotPort.verifyOriginal(ack,frame,event);return new ArchivedRead(ack,frame,event);
    }
    private static void requireContext(RootPrivateBootstrap.Original original,RootRuntimeContext context)throws IOException {
        if(original.context()!=context||original.game()!=context.game()||original.adopted()!=context.adopted()
                ||!original.adopted().source().equals(context.source()))throw new IOException("cold rebound crossed the actual privately adopted Root/context/source");
    }
    private static WriterContracts.HistoricalTransition originalMigration(ContinuityStorePort.Session same,RootPrivateBootstrap.Original original)throws IOException {
        original.requireOriginal(same);var receipt=original.commitReceipt();var request=original.migrationRequest();
        String name=String.format(java.util.Locale.ROOT,"%08d.json",receipt.head().sequence());
        var pin=same.head().documents().stream().filter(value->Path.of(value.reference().path()).getFileName().toString().equals(name)).findFirst()
                .orElseThrow(()->new IOException("actual cold migration event FileID is absent from canonical history"));
        var event=same.readHistoricalTransition(pin);
        StrictJson.require(event.sequence()==receipt.head().sequence()&&event.eventIdentity().equals(receipt.eventIdentity())
                &&event.eventIdentity().equals(request.identity())&&event.kind().equals(request.kind())
                &&Arrays.equals(event.details(),request.details())&&ContinuityJson.same(event.after().toJson(),receipt.head().toJson()),
                "actual cold migration original event/receipt differs");
        OriginalLegacyResume.requireReduction(event.before(),event.after(),request,true);return event;
    }
    private static void requireRaw(RootPrivateBootstrap.Original original,RootRuntimeContext context,NativeObservationPort.ObservedFrame raw) {
        var transport=raw.session();var pair=original.pair();
        DriverObservationAssembler.originalNativeState(raw);
        StrictJson.require(transport.machineId().equals(context.game().machineId())&&transport.game().equals(context.game().generation())
                &&transport.sessionId().equals(context.game().sessionId())&&!transport.game().equals(pair.frame().game()),"cold READ belongs to another physical Game/session");
        var parsed=FullJsonTree.parse(raw.state().bytes(),DriverJson.MAX_NATIVE_BYTES);
        StrictJson.require(parsed instanceof ObjectNode,"actual cold native map object required");var state=(ObjectNode)parsed;
        StrictJson.trueValue(state.get("map_ready"));StrictJson.trueValue(state.get("paused"));
        StrictJson.require(state.get("played_character") instanceof ObjectNode,"actual cold played character required");var player=(ObjectNode)state.get("played_character");
        StrictJson.trueValue(player.get("alive"));
        StrictJson.require(NativeCharacterId.fromJson(player.get("character_id")).asBigInteger().equals(pair.frame().frame().identity().player())
                &&StrictJson.integer(state.get("date_raw"),0,StrictJson.MAX_SAFE_INTEGER)==pair.frame().frame().identity().dateRaw().longValueExact(),
                "actual cold READ changed loaded SAVE actor/date");
    }
    private static WriterContracts.Pin pin(ContinuityStorePort.Session same,ExactRef reference)throws IOException {
        StrictJson.require(reference.bytes()>0&&reference.bytes()<=WriterContracts.MAX_PIN_BYTES,"cold original exceeds actual writer physical pin lane");
        var pin=same.capturePin(reference,Math.toIntExact(reference.bytes()));verify(same,pin);return pin;
    }
    private static void verify(ContinuityStorePort.Session same,WriterContracts.Pin pin)throws IOException {
        same.readPinned(pin,Math.toIntExact(pin.reference().bytes()));same.verifyPin(pin);
    }
    private static WriterContracts.Pin find(List<WriterContracts.Pin> pins,ExactRef reference)throws IOException {
        return pins.stream().filter(pin->pin.reference().equals(reference)).findFirst().orElseThrow(()->new IOException("actual cold proof pin missing"));
    }
    /** Sole actual loaded-class roster. Configuration maps each real Class through getNestHost to its source. */
    public static List<Class<?>> requiredSourceTypes(){
        var types=new LinkedHashSet<Class<?>>(List.of(RootColdReboundRuntime.class,ColdReboundOrigin.class,Data.class,
                ReadOriginal.class,ArchivedRead.class,NativeFreshSnapshotPort.class,NativeFreshSnapshotPort.Received.class));
        types.addAll(RootPrivateBootstrap.requiredSourceTypes());return List.copyOf(types);
    }
    private static void sources(RootRuntimeContext context)throws IOException {
        for(Class<?> type:requiredSourceTypes())context.game().launchPlan().sources().requireLoadedClass(type);
        context.game().launchPlan().sources().verify();
    }
}
