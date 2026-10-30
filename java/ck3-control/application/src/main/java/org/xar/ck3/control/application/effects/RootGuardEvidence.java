package org.xar.ck3.control.application.effects;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.GenericPublicPauseRecovery.ParentProof;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.readiness.ReadinessAuthority;
import org.xar.ck3.control.application.session.SessionPorts.SemanticEvidence;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyDerivedAdmissionEvidence;

/** Named immutable guard originals and their actual writer history point. Loading data is not historical qualification. */
public final class RootGuardEvidence {
    public static final String SCHEMA="xar.java.root-guard-original-basis/v3";
    private static final String READ_ONLY_V2="xar.java.root-guard-original-basis/v2";
    private static final Set<String> V2_FIELDS=Set.of("schema","operation","authority_id","native_frame","driver_facts","semantic","driver_stamp","original_driver","capabilities","hello","heartbeat","source_qualification");
    private static final Set<String> V3_FIELDS=java.util.stream.Stream.concat(V2_FIELDS.stream(),java.util.stream.Stream.of("writer_point")).collect(java.util.stream.Collectors.toUnmodifiableSet());
    private RootGuardEvidence() { }
    public record WriterPoint(long sequence,String digest) {
        public WriterPoint {
            StrictJson.safe(sequence,0);
            StrictJson.require(digest!=null && digest.matches("[0-9a-f]{64}"),"exact original writer digest required");
        }
        private ObjectNode json() { return StrictJson.object().put("sequence",sequence).put("digest",digest); }
    }
    /**
     * Original DATA from one actual physical capture. This record cannot mint a
     * SnapshotLease, source qualification, ordinary Ready, action or read permission.
     */
    public record PhysicalReadOriginals(Complete frame,SemanticEvidence semantic,ExactRef hello,ExactRef heartbeat,
            Optional<ExactRef> sourceQualification,ExactRef capabilities) {
        public PhysicalReadOriginals {
            Objects.requireNonNull(frame);Objects.requireNonNull(semantic);
            Objects.requireNonNull(sourceQualification);
            for(ExactRef original:List.of(hello,heartbeat,capabilities))
                StrictJson.require(original.bytes()>0,"nonempty exact physical guard original required");
            sourceQualification.ifPresent(original->StrictJson.require(original.bytes()>0,"nonempty supplied historical source original required"));
            StrictJson.require(semantic.frame().equals(frame.identity())
                    &&semantic.originalNativePacket().equals(frame.originalEvidence())
                    &&semantic.observedAt().equals(frame.observedAt()),
                    "physical guard semantic/native/frame/time originals differ");
            NativeEffectEvidence.basis(frame);
        }
        public PhysicalReadOriginals(Complete frame,SemanticEvidence semantic,ExactRef hello,ExactRef heartbeat,
                ExactRef sourceQualification,ExactRef capabilities) {
            this(frame,semantic,hello,heartbeat,Optional.of(sourceQualification),capabilities);
        }
    }
    /** Ordinary callers retain their original actual readiness lease and the same v3 field contract. */
    public static ExactRef preserve(ReadinessAuthority.LeaseSnapshot lease,OperationKey operation,String authorityId,ExactRef capabilities,
            ActionPorts.OutcomeArchive archive,WriterContracts.Head actualHead) {
        Objects.requireNonNull(lease);
        return preservePhysicalRead(new PhysicalReadOriginals(lease.frame(),lease.semantic(),lease.originalHello(),
                lease.originalHeartbeat(),lease.originalSourceQualification(),capabilities),operation,authorityId,archive,actualHead);
    }
    /**
     * Sole v3 DATA serializer for an already qualified physical read or first SAVE
     * capture. The private physical scope and exact permitted operation are checked
     * by the actual owning Root before and after this call, never by this codec.
     */
    public static ExactRef preservePhysicalRead(PhysicalReadOriginals originals,OperationKey operation,String authorityId,
            ActionPorts.OutcomeArchive archive,WriterContracts.Head actualHead) {
        Objects.requireNonNull(originals);Objects.requireNonNull(operation);StrictJson.text(authorityId);
        Objects.requireNonNull(archive);Objects.requireNonNull(actualHead);
        StrictJson.require(actualHead.state().machineId().equals(originals.frame().identity().machineId()),
                "physical guard originals belong to another writer machine");
        var point=new WriterPoint(actualHead.state().sequence(),actualHead.digest());
        var row=StrictJson.object().put("schema",SCHEMA).put("operation",operation.value()).put("authority_id",authorityId);
        var frames=NativeEffectEvidence.basis(originals.frame());
        row.set("native_frame",frames.nativeFrame().toJson());row.set("driver_facts",frames.driverFacts().toJson());
        row.set("semantic",originals.semantic().semantic().toJson());row.set("driver_stamp",originals.semantic().driverStamp().toJson());
        row.set("original_driver",originals.semantic().originalDriver().toJson());row.set("capabilities",originals.capabilities().toJson());
        row.set("hello",originals.hello().toJson());row.set("heartbeat",originals.heartbeat().toJson());
        if(originals.sourceQualification().isPresent())row.set("source_qualification",originals.sourceQualification().orElseThrow().toJson());
        else row.putNull("source_qualification");
        row.set("writer_point",point.json());
        RawJson actual=EffectJson.raw(row);ExactRef reference=archive.preserveMaterial(actual);
        RootGuardChecks.exact(reference,actual.bytes());
        StrictJson.require(actual.equals(archive.loadMaterial(reference)),"actual guard basis archive changed");
        return reference;
    }
    /** Exact role, never a guessed support reference. This returns data; requireHistory separately qualifies ancestry. */
    public static Optional<ExactRef> sourceQualification(GuardEvidence guard,ActionPorts.OutcomeArchive archive) {
        var value=body(guard,archive).get("source_qualification");
        return value==null||value.isNull()?Optional.empty():Optional.of(ExactRef.fromJson(value));
    }
    /** Named original complete SEM DATA only; no source, history or submission qualification. */
    public static ExactRef semanticReference(GuardEvidence guard,ActionPorts.OutcomeArchive archive) { return ExactRef.fromJson(body(guard,archive).get("semantic")); }
    public record OriginalDriverSource(ExactRef driverRef,ExactRef stampRef) {
        public OriginalDriverSource { Objects.requireNonNull(driverRef); Objects.requireNonNull(stampRef); }
    }
    /** Named physical Driver roles only. Call requireHistory separately before granting current-head qualification. */
    public static OriginalDriverSource originalDriverSource(GuardEvidence guard,ActionPorts.OutcomeArchive archive) {
        var row=body(guard,archive);
        return new OriginalDriverSource(ExactRef.fromJson(row.get("original_driver")),ExactRef.fromJson(row.get("driver_stamp")));
    }
    public static WriterPoint writerPoint(GuardEvidence guard,ActionPorts.OutcomeArchive archive) {
        var row=body(guard,archive);
        StrictJson.require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"legacy guard data has no original writer history point; historical qualification is unavailable");
        return point(row);
    }
    public static void requireHistory(GuardEvidence guard,ActionPorts.OutcomeArchive archive,ContinuityStorePort.Session same) throws IOException {
        var point=writerPoint(guard,archive);
        Objects.requireNonNull(same).requireHistoricalState(point.sequence(),point.digest());
    }
    public static NativeEffectEvidence.FrameBasis frameBasis(GuardEvidence guard,ActionPorts.OutcomeArchive archive) {
        var row=body(guard,archive); return new NativeEffectEvidence.FrameBasis(ExactRef.fromJson(row.get("native_frame")),ExactRef.fromJson(row.get("driver_facts")));
    }
    public static Complete loadFrame(GuardEvidence guard,ActionPorts.OutcomeArchive archive,NativeEffectEvidence.FrameLoader actualLoader) {
        var row=body(guard,archive); var complete=actualLoader.load(frameBasis(guard,archive),archive);
        StrictJson.require(guard.origin() instanceof CommandOrigin.Gameplay && complete.identity().equals(guard.observed())
                && complete.source().equals(guard.source()) && complete.sessionId().equals(guard.sessionId())
                && complete.connectionGeneration().equals(guard.connectionGeneration()) && complete.observedAt().equals(guard.observedAt()),"archived guard originals no longer reconstruct the actual bound frame");
        var semantic=archive.loadFullMaterial(ExactRef.fromJson(row.get("semantic")));
        RootGuardChecks.requireSemanticOriginal(complete,semantic); return complete;
    }
    static ObjectNode body(GuardEvidence guard,ActionPorts.OutcomeArchive archive) {
        StrictJson.require(guard.supportingEvidence().size()==1 || guard.supportingEvidence().size()==2,"actual guard requires one Root basis and at most its one exact typed derived-child locator");
        ExactRef ref=guard.supportingEvidence().getFirst(); RawJson raw=archive.loadMaterial(ref); RootGuardChecks.exact(ref,raw.bytes());
        ObjectNode row=EffectJson.object(EffectJson.parse(raw)); String schema=StrictJson.text(row.get("schema"));
        StrictJson.require(SCHEMA.equals(schema) || READ_ONLY_V2.equals(schema),"unsupported original Root guard schema");
        Set<String> fields=SCHEMA.equals(schema)?V3_FIELDS:V2_FIELDS;
        StrictJson.object(row,row.has("source_qualification")?fields:fields.stream().filter(field->!field.equals("source_qualification")).collect(java.util.stream.Collectors.toUnmodifiableSet()));
        if(SCHEMA.equals(schema)) point(row);
        StrictJson.require(guard.operation().value().equals(StrictJson.text(row.get("operation"))) && guard.authorityId().equals(StrictJson.text(row.get("authority_id")))
                && guard.nativeEvidence().equals(ExactRef.fromJson(row.get("native_frame"))) && guard.capabilityEvidence().equals(ExactRef.fromJson(row.get("hello"))),"original guard basis binding changed");
        // Decode the named reference roles; actual payload consumption belongs to their readers.
        for(String field:List.of("driver_facts","semantic","original_driver","driver_stamp","capabilities","heartbeat"))
            ExactRef.fromJson(row.get(field));
        var qualification=row.get("source_qualification");
        if(qualification!=null&&!qualification.isNull())ExactRef.fromJson(qualification);
        if(guard.supportingEvidence().size()==2) {
            ExactRef childRef=guard.supportingEvidence().getLast();RawJson childRaw=archive.loadMaterial(childRef);
            RootGuardChecks.exact(childRef,childRaw.bytes());
            String childSchema=StrictJson.text(EffectJson.object(EffectJson.parse(childRaw)).get("schema"));
            ExactRef childBeforeNative,childBeforeDriver;
            if(ArmyDerivedAdmissionEvidence.SCHEMA.equals(childSchema)) {
                var derived=ArmyDerivedAdmissionEvidence.requireGuard(guard,archive);
                childBeforeNative=derived.beforeNative();childBeforeDriver=derived.beforeDriver();
            }else if(RootDerivedChildEvidence.SCHEMA.equals(childSchema)) {
                var derived=RootDerivedChildEvidence.requireGuard(guard,archive);
                childBeforeNative=derived.beforeNative();childBeforeDriver=derived.beforeDriver();
            }else if(ParentProof.SCHEMA.equals(childSchema)) {
                ParentProof parent=ParentProof.decode(childRaw.bytes());
                var originalPoint=point(row);
                StrictJson.require(SCHEMA.equals(schema)&&parent.matchesGuard(guard,ExactRef.fromJson(row.get("driver_facts")),childRef)
                        &&parent.writerSequence()==originalPoint.sequence()&&parent.writerDigest().equals(originalPoint.digest()),
                        "public pause parent DATA differs from its exact Root basis/guard/history point");
                childBeforeNative=parent.beforeNative();childBeforeDriver=parent.beforeDriver();
            }else throw new IllegalArgumentException("unregistered exact derived-child locator schema");
            StrictJson.require(childBeforeNative.equals(ExactRef.fromJson(row.get("native_frame")))
                    &&childBeforeDriver.equals(ExactRef.fromJson(row.get("driver_facts"))),
                    "derived child native/Driver locators differ from the actual Root basis");
        }
        return row;
    }
    private static WriterPoint point(ObjectNode row) {
        var n=StrictJson.object(row.get("writer_point"),Set.of("sequence","digest"));
        return new WriterPoint(StrictJson.integer(n.get("sequence"),BigInteger.ZERO,BigInteger.valueOf(9_007_199_254_740_991L)).longValueExact(),StrictJson.text(n.get("digest")));
    }
}
