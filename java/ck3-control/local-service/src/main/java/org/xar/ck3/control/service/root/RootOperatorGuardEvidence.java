package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.application.readiness.NativeSourceProofCodec;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One strict DATA codec for the private operator guard. Decoding does not grant a live actor rebind or ordinary readiness. */
public final class RootOperatorGuardEvidence {
    public static final String SCHEMA="xar.java.operator-current-guard/v1";
    private static final Set<String> REQUIRED_FIELDS=Set.of("schema","authority_id","operation","action_id","body_sha256",
            "native_frame","driver_facts","original_driver","original_auxiliary","hello","heartbeat","writer_sequence","writer_sha256");
    private static final Set<String> OPTIONAL_FIELDS=Set.of("source_qualification","source_epoch","source_epoch_manifest","game_executable");
    private RootOperatorGuardEvidence() { }

    /** Historical originals only. The actual installed private issuer supplies live authority separately. */
    public record Original(DriverObservationAssembler.FullSnapshot frame,ExactRef driver,ExactRef auxiliary,
            ExactRef hello,ExactRef heartbeat,Optional<ExactRef> sourceQualification,Optional<String> sourceEpoch,
            Optional<ExactRef> sourceEpochManifest,Optional<ExactRef> gameExecutable,long writerSequence,String writerSha256) {
        public Original {
            Objects.requireNonNull(frame);Objects.requireNonNull(driver);Objects.requireNonNull(auxiliary);
            for(var ref:List.of(driver,auxiliary,hello,heartbeat))
                StrictJson.require(ref.bytes()>0,"nonempty original operator guard role required");
            Objects.requireNonNull(sourceQualification);Objects.requireNonNull(sourceEpoch);Objects.requireNonNull(sourceEpochManifest);Objects.requireNonNull(gameExecutable);
            sourceQualification.ifPresent(ref->StrictJson.require(ref.bytes()>0,"nonempty optional source qualification"));sourceEpochManifest.ifPresent(ref->StrictJson.require(ref.bytes()>0,"nonempty optional source epoch"));gameExecutable.ifPresent(ref->StrictJson.require(ref.bytes()>0,"nonempty optional executable"));sourceEpoch.ifPresent(WriterContracts::requireDigest);
            WriterContracts.requireDigest(writerSha256);StrictJson.safe(writerSequence,0);
        }
    }

    /** Called only with this package's actual physical issuer and original command under the same writer. */
    static ExactRef preserve(RootOperatorPhysicalEvidence.Captured original,ActionCommand command,String authorityId,
            ActionPorts.OutcomeArchive archive,WriterContracts.Head head,ContinuityStorePort.Session same)throws IOException {
        Objects.requireNonNull(original);Objects.requireNonNull(command);original.requireRetained(same);
        StrictJson.require(command.expectation() instanceof CommandExpectation.OperatorRebind,"operator guard cannot serve an ordinary action");
        var row=StrictJson.object();row.put("schema",SCHEMA).put("authority_id",StrictJson.text(authorityId))
                .put("operation",command.operation().value()).put("action_id",command.actionId()).put("body_sha256",ActionCodec.bodySha256(command));
        row.set("native_frame",original.full().originalEvidence().toJson());row.set("driver_facts",original.full().facts().semanticFactsEvidence().toJson());
        row.set("original_driver",original.driver().toJson());row.set("original_auxiliary",original.auxiliary().toJson());
        row.set("hello",original.hello().toJson());row.set("heartbeat",original.heartbeat().toJson());
        var metadata=original.metadata();
        if(metadata.isPresent()){
            var qualified=metadata.orElseThrow();
            row.set("source_qualification",ExactRef.optionalToJson(original.source().proof()));
            row.put("source_epoch",qualified.ownerSourceEpoch());
            row.set("source_epoch_manifest",qualified.epochManifest().toJson());
            row.set("game_executable",qualified.gameExecutable().toJson());
        } else {
            row.set("source_qualification",ExactRef.optionalToJson(original.source().proof()));row.putNull("source_epoch");row.putNull("source_epoch_manifest");row.putNull("game_executable");
        }
        row.put("writer_sequence",head.state().sequence()).put("writer_sha256",head.digest());
        RawJson encoded=new RawJson(StrictJson.canonical(row));ExactRef result=archive.preserveMaterial(encoded);
        StrictJson.require(archive.loadMaterial(result).equals(encoded),"operator guard archive readback differs");return result;
    }

    /** Sole cold DATA reader. It checks exact roles and replays the full original projection, never a source permission. */
    public static Original read(ActionCommand command,GuardEvidence guard,ActionPorts.OutcomeArchive archive)throws IOException {
        Objects.requireNonNull(command);Objects.requireNonNull(guard);Objects.requireNonNull(archive);
        StrictJson.require(command.expectation() instanceof CommandExpectation.OperatorRebind
                &&guard.origin().equals(command.origin())&&guard.operation().equals(command.operation())
                &&guard.source().equals(command.source())&&guard.sessionId().equals(command.sessionId())
                &&guard.supportingEvidence().size()==1,"exact source-owned operator command/guard required");
        ExactRef basis=guard.supportingEvidence().getFirst();RawJson bytes=archive.loadMaterial(basis);exact(basis,bytes.bytes());
        ObjectNode row=StrictJson.object(StrictJson.parse(bytes.bytes()),REQUIRED_FIELDS,OPTIONAL_FIELDS);
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema")))
                &&guard.authorityId().equals(StrictJson.text(row.get("authority_id")))
                &&command.operation().value().equals(StrictJson.text(row.get("operation")))
                &&command.actionId().equals(StrictJson.text(row.get("action_id")))
                &&ActionCodec.bodySha256(command).equals(StrictJson.text(row.get("body_sha256"))),"operator original guard body changed");
        ExactRef nativeFrame=reference(row,"native_frame"),factsRef=reference(row,"driver_facts"),driverRef=reference(row,"original_driver"),aux=reference(row,"original_auxiliary");
        ExactRef hello=reference(row,"hello"),heartbeat=reference(row,"heartbeat");
        Optional<ExactRef> qualification=ExactRef.optionalFromJson(row.get("source_qualification"));
        Optional<String> epoch=row.has("source_epoch")&&!row.get("source_epoch").isNull()?Optional.of(StrictJson.text(row.get("source_epoch"))):Optional.empty();
        Optional<ExactRef> epochManifest=ExactRef.optionalFromJson(row.get("source_epoch_manifest"));
        Optional<ExactRef> executable=ExactRef.optionalFromJson(row.get("game_executable"));
        StrictJson.require(nativeFrame.equals(guard.nativeEvidence())&&hello.equals(guard.capabilityEvidence()),"operator guard substituted native or HELLO roles");
        byte[] nativePacket=archive.loadNativeFrame(nativeFrame);exact(nativeFrame,nativePacket);
        RawJson facts=archive.loadFullMaterial(factsRef),driver=archive.loadFullMaterial(driverRef);exact(factsRef,facts.bytes());exact(driverRef,driver.bytes());
        StrictJson.require(DriverObservationEvidenceReader.currentDriverReference(factsRef,facts).equals(driverRef),"operator facts selected another original Driver");
        var observed=DriverObservationEvidenceReader.nativeFrame(factsRef,facts,nativePacket);
        var decoded=DriverObservationEvidenceReader.decode(factsRef,facts,driver,observed);
        var assembler=new DriverObservationAssembler();var full=assembler.projectFull(observed,decoded,nativeFrame);
        StrictJson.require(observed.session().connectionGeneration().equals(guard.connectionGeneration())
                &&observed.session().game().equals(command.origin().game())&&observed.session().sessionId().equals(command.sessionId())
                &&observed.observedAt().equals(guard.observedAt())&&decoded.source().equals(command.source()),
                "operator original full native/Driver/session/source differs from its guard");
        var actualHello=NativeWire.decode(archive.readOriginalPacket(hello));
        var actualHeartbeat=NativeWire.decode(archive.readOriginalPacket(heartbeat));
        StrictJson.require(actualHello instanceof NativeWire.Hello&&actualHeartbeat instanceof NativeWire.Notice
                &&((NativeWire.Notice)actualHeartbeat).kind()==NativeWire.NoticeKind.HEARTBEAT,
                "operator guard needs its original HELLO and heartbeat packets");
        var helloPacket=(NativeWire.Hello)actualHello;
        StrictJson.require(helloPacket.pid()==observed.session().game().pid()
                &&helloPacket.connectionGeneration().equals(guard.connectionGeneration())&&helloPacket.buildMatch(),"operator HELLO belongs to another Game/build");
        if(executable.isPresent())StrictJson.require(helloPacket.gameSha256().equalsIgnoreCase(executable.orElseThrow().sha256()),"operator HELLO game SHA differs from archived executable");
        requireSupported(helloPacket);
        var expected=((CommandExpectation.OperatorRebind)command.expectation()).expected();expected.validateCommand(command);
        StrictJson.require(expected.beforeDriver().equals(driverRef)&&expected.episodeEpoch()==decoded.episodeEpoch()
                &&expected.episodeRunId().equals(decoded.driver().session().episodeRunId()),"operator expectation differs from original full Driver");
        if(command.origin() instanceof CommandOrigin.Gameplay gameplay) {
            var projected=assembler.assemble(observed,decoded,nativeFrame);
            var player=full.semantic().get("played_character");
            StrictJson.require(projected instanceof DriverObservationAssembler.Complete
                    &&player instanceof OpportunityJson.Obj character&&character.get("alive") instanceof OpportunityJson.Bool alive&&alive.value()
                    &&((DriverObservationAssembler.Complete)projected).identity().equals(gameplay.before()),
                    "operator gameplay origin is not the actual original living-subject data join");
        } else {
            StrictJson.require(command.origin() instanceof CommandOrigin.LifecycleTerminal,"operator cannot borrow frontend or reconciliation authority");
            var projected=LifecycleOriginFactory.projectOperatorBefore(full,hello,driverRef,qualification,expected.request());
            StrictJson.require(projected instanceof LifecycleOriginFactory.Projected
                    &&((LifecycleOriginFactory.Projected)projected).identity().equals(command.origin().requireLifecycleTerminal()),
                    "operator terminal origin differs from its original source-bound projection");
        }
        exact(aux,archive.loadFullMaterial(aux).bytes());
        OperatorPlayerSwitch.requireBefore(expected.request(),FullJsonTree.parse(DriverJson.encode(full.semantic()),DriverJson.MAX_NATIVE_BYTES));
        return new Original(full,driverRef,aux,hello,heartbeat,qualification,epoch,epochManifest,executable,
                StrictJson.integer(row.get("writer_sequence"),0,StrictJson.MAX_SAFE_INTEGER),StrictJson.text(row.get("writer_sha256")));
    }
    /** Historical membership is checked by the caller's actual Session, in addition to the DATA decoder. */
    public static Original requireHistorical(ContinuityStorePort.Session same,ActionCommand command,GuardEvidence guard,
            ActionPorts.OutcomeArchive archive)throws IOException {
        Original original=read(command,guard,archive);same.requireHistoricalState(original.writerSequence(),original.writerSha256());return original;
    }
    private static ExactRef reference(ObjectNode row,String key){return ExactRef.fromJson(row.get(key));}
    static void requireSupported(NativeWire.Hello hello){
        String version="ck3-1.19.0.6-msvc-x64".equals(hello.adapterId())?"1.19.0.6":"unsupported-adapter";
        OperatorPlayerSwitch.requireSupported(version,hello.gameSha256(),Set.copyOf(hello.capabilities()));
    }
    private static void exact(ExactRef ref,byte[] bytes){StrictJson.require(ref.bytes()==bytes.length&&ref.sha256().equals(DriverJson.sha256(bytes)),"operator original bytes differ from their exact immutable reference");}
}
