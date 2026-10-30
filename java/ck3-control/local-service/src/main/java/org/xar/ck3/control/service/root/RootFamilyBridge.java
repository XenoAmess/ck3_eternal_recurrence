package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatterBuilder;
import java.time.temporal.ChronoField;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.family.*;
import org.xar.ck3.control.application.readiness.ReadinessAuthority.LeaseSnapshot;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Bridge birth is tied to the actual original native/Driver join and the measured Game generation. */
public final class RootFamilyBridge implements FamilyDomainSource.CurrentBridge {
    public static final String SCHEMA="xar.java.family-bridge-original/v1";
    private static final int MAX=DriverJson.MAX_NATIVE_BYTES;
    private static final int MANIFEST_MAX=StrictJson.INPUT_MAX_BYTES;
    private final RootRuntimeContext context;
    public RootFamilyBridge(RootRuntimeContext context) {this.context=java.util.Objects.requireNonNull(context);}
    public record Evidence(FamilyDomainSource.BridgeObservation observation,Complete frame,ExactRef semantic) { }
    @Override public Optional<FamilyDomainSource.BridgeObservation> observe(PlanningRequest request) {
        try {
            context.requireCurrent(request.deadline());var same=context.borrowedSession();
            return Optional.of(context.collector().currentPlanning(same,request,request.deadline(),(original,lease)->current(same,lease).observation()));
        } catch(IOException|IllegalArgumentException unavailable) {throw observationUnavailable(unavailable);}
    }
    static IllegalArgumentException observationUnavailable(Exception original) {
        return new IllegalArgumentException("actual family Bridge observation unavailable: "
                +original.getClass().getSimpleName()+": "+original.getMessage(),original);
    }
    /** Native preparation already owns this lease; publishing the identity manifest performs no new query. */
    public Evidence current(Session same,LeaseSnapshot lease)throws IOException {
        context.writer().requireSession(same);var frame=lease.frame();
        StrictJson.require(frame.identity().game().equals(context.game().generation()) && frame.source().equals(context.source())
                && frame.sessionId().equals(context.game().sessionId()),"family Bridge crossed the current physical Game");
        var diagnostics=OpportunityJson.object(frame.semantic().get("diagnostics"),"actual native diagnostics");
        StrictJson.require(OpportunityJson.integer(diagnostics.get("bridge_pid"),"bridge_pid").equals(BigInteger.valueOf(frame.identity().game().pid()))
                && OpportunityJson.integer(diagnostics.get("connection_generation"),"connection_generation").equals(frame.connectionGeneration()),"actual native bridge identity/connection differs from the held source");
        var basis=NativeEffectEvidence.basis(frame);
        StrictJson.require(basis.nativeFrame().equals(lease.semantic().originalNativePacket()),"actual complete frame and held native packet differ");
        byte[] encoded=encodeManifest(frame,lease.semantic().semantic());
        var reference=context.archive().preserveArtifact(same,encoded,MANIFEST_MAX);
        context.writer().requireSession(same);return replay(same,reference);
    }
    public FamilyNativePreparation.VerifiedBasis verified(Session same,LeaseSnapshot lease,ActionCommand command)throws IOException {
        context.writer().requireSession(same);context.requireCurrent(command.deadline());
        StrictJson.require(ActionCommandScope.current().filter(command::equals).isPresent(),"family preparation requires the actual coordinator command scope");
        var frame=lease.frame();
        StrictJson.require(frame.identity().equals(command.before()) && frame.source().equals(command.source()) && frame.sessionId().equals(command.sessionId()),
                "family preparation lease differs from immutable command before/source/session");
        FamilyNativePreparation.requireCommandFrame(command,frame.semantic());
        var actual=current(same,lease);return new FamilyNativePreparation.VerifiedBasis(actual.frame().semantic(),actual.observation().identity(),actual.semantic(),actual.observation().evidence());
    }
    public Evidence replay(Session same,ExactRef original)throws IOException {
        context.writer().requireSession(same);byte[] bytes=context.archive().readArtifact(same,original,MANIFEST_MAX);
        var body=decodeManifest(bytes);
        var basis=new NativeEffectEvidence.FrameBasis(ExactRef.fromJson(body.get("native_frame")),ExactRef.fromJson(body.get("driver_facts")));
        var frame=context.frameLoader().load(basis,context.archive().withSession(same));ExactRef semantic=ExactRef.fromJson(body.get("semantic"));
        StrictJson.require(matchesSemantic(frame,context.archive().readArtifact(same,semantic,MAX))
                && matchesPersistedGame(body.get("game"), frame.identity().game()) && StrictJson.text(body.get("machine_id")).equals(frame.identity().machineId())
                && StrictJson.text(body.get("session_id")).equals(frame.sessionId()),"original Bridge native/Driver/semantic source drift");
        long pid=StrictJson.integer(body.get("bridge_pid"),1,0xffff_ffffL);String birth=StrictJson.text(body.get("bridge_creation_date"));
        StrictJson.require(pid==frame.identity().game().pid() && birth.equals(creationToken(frame.identity().game())),"Bridge identity is not the exact derived actual process birth");
        var diagnostic=OpportunityJson.object(frame.semantic().get("diagnostics"),"retained native diagnostics");
        StrictJson.require(OpportunityJson.integer(diagnostic.get("bridge_pid"),"bridge_pid").equals(BigInteger.valueOf(pid))
                && OpportunityJson.integer(diagnostic.get("connection_generation"),"connection_generation").equals(frame.connectionGeneration()),"retained native bridge lacks its actual process/connection binding");
        return new Evidence(new FamilyDomainSource.BridgeObservation(new FamilyPorts.BridgeIdentity(pid,birth),original),frame,semantic);
    }
    @Override public boolean verifyRetained(PlanningReadReceipt read,FamilyDomainSource.BridgeObservation observed) {
        try {
            var same=context.borrowedSession();var original=replay(same,observed.evidence());var frame=original.frame();
            StrictJson.require(original.observation().equals(observed),"retained Bridge observation identity differs");
            for(var guard:java.util.List.of(read.before(),read.after()))StrictJson.require(guard.binding().observed().equals(frame.identity())
                    && guard.binding().source().equals(frame.source()) && guard.binding().sessionId().equals(frame.sessionId())
                    && guard.binding().connectionGeneration().equals(frame.connectionGeneration()) && guard.originalBindingSha256().equals(frame.fullBindingSha256()),"family read and Bridge are not the same original complete frame");
            context.writer().requireSession(same);return true;
        } catch(IOException|RuntimeException unavailable) {return false;}
    }

    /** Pure original encoding only; the caller retains the actual held-source checks. */
    static byte[] encodeManifest(Complete frame,ExactRef semantic) {
        java.util.Objects.requireNonNull(frame);java.util.Objects.requireNonNull(semantic);
        var body=StrictJson.object().put("schema",SCHEMA).put("machine_id",frame.identity().machineId()).put("session_id",frame.sessionId());
        body.set("game",frame.identity().game().toJson());
        body.put("bridge_pid",frame.identity().game().pid()).put("bridge_creation_date",creationToken(frame.identity().game()));
        var basis=NativeEffectEvidence.basis(frame);
        body.set("native_frame",basis.nativeFrame().toJson());body.set("driver_facts",basis.driverFacts().toJson());body.set("semantic",semantic.toJson());
        return StrictJson.canonical(body,MANIFEST_MAX);
    }
    static ObjectNode decodeManifest(byte[] original) {
        var body=StrictJson.object(StrictJson.parse(original,MANIFEST_MAX),Set.of("schema","machine_id","session_id","game",
                "bridge_pid","bridge_creation_date","native_frame","driver_facts","semantic"));
        StrictJson.require(SCHEMA.equals(StrictJson.text(body.get("schema"))),"original family Bridge schema differs");
        return body;
    }
    static boolean matchesSemantic(Complete frame,byte[] original) {
        return frame.semantic().equals(DriverJson.object(original,MAX));
    }
    static boolean matchesPersistedGame(JsonNode persisted, GameGeneration expected) {
        try {
            return GameGeneration.fromJson(persisted).equals(expected);
        } catch (ContractViolationException invalid) {
            return false;
        }
    }

    /** Seven fraction digits retain every FILETIME tick; no JavaScript Number or microsecond rounding participates. */
    public static String creationToken(GameGeneration game) {
        var parts=game.creationFiletime().value().divideAndRemainder(BigInteger.valueOf(10_000_000));
        Instant actual=Instant.ofEpochSecond(parts[0].subtract(new BigInteger("11644473600")).longValueExact(),parts[1].longValueExact()*100L);
        return new DateTimeFormatterBuilder().appendPattern("uuuu-MM-dd'T'HH:mm:ss").appendFraction(ChronoField.NANO_OF_SECOND,7,7,true)
                .appendLiteral('Z').toFormatter(java.util.Locale.ROOT).withZone(ZoneOffset.UTC).format(actual);
    }
}
