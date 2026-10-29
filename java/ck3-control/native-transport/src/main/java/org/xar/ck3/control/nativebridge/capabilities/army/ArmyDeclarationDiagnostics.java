package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.time.Duration;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Read-only projection of the sole original UNKNOWN custody, never a new Native query or an assumed empty state. */
public final class ArmyDeclarationDiagnostics {
    private ArmyDeclarationDiagnostics() { }
    public record Binding(String snapshotId, BigInteger publicRevision, BigInteger nativeRevision, String episode,
            int dateRaw, boolean paused, boolean mapReady, int playerCharacterId, long bridgePid, BigInteger connectionGeneration) {
        public Binding {
            Objects.requireNonNull(snapshotId);Objects.requireNonNull(publicRevision);Objects.requireNonNull(nativeRevision);Objects.requireNonNull(episode);Objects.requireNonNull(connectionGeneration);
            require(!snapshotId.isEmpty()&&!episode.isEmpty()&&publicRevision.signum()>=0&&paused&&mapReady&&playerCharacterId!=-1&&bridgePid>0&&bridgePid<=4294967295L,"actual original declaration binding required");
            UInt64.positive(nativeRevision);UInt64.positive(connectionGeneration);
        }
        public Obj encode() {
            return DriverJson.object(bytes(empty().put("snapshot_id",snapshotId).put("revision",publicRevision).put("native_revision",nativeRevision)
                    .put("episode_run_id",episode).put("date_raw",dateRaw).put("paused",paused).put("map_ready",mapReady)
                    .put("player_character_id",playerCharacterId).put("bridge_pid",bridgePid).put("connection_generation",connectionGeneration)),DriverJson.MAX_NATIVE_BYTES);
        }
    }
    public record Pending(String requestId, OperationKey step, Binding binding, Duration originalTimeout, Obj originalDiagnostic) {
        public Pending {Objects.requireNonNull(requestId);Objects.requireNonNull(step);Objects.requireNonNull(binding);Objects.requireNonNull(originalTimeout);Objects.requireNonNull(originalDiagnostic);}
    }
    public static final class Capture {
        private final ArmyWarReads owner;
        private final Optional<ArmyWarReads.PendingDeclaration> custody;
        private final Optional<Pending> pending;
        private Capture(ArmyWarReads owner,Optional<ArmyWarReads.PendingDeclaration> custody,Optional<Pending> pending){this.owner=owner;this.custody=custody;this.pending=pending;}
        public Optional<ArmyWarReads.PendingDeclaration> originalCustody(){return custody;}
        public Optional<Pending> pending(){return pending;}
        public Optional<Obj> field(){return pending.map(Pending::originalDiagnostic);}
        public void requireCurrent(ArmyWarReads actualOwner,PlanningReadPort actualRootReads){require(owner==actualOwner,"pending diagnostics crossed its actual owner object");owner.requirePendingDeclarationUnchanged(actualRootReads,custody);}
    }
    public static Capture capture(ArmyWarReads actual,PlanningReadPort actualRootReads)throws IOException {
        Objects.requireNonNull(actual);var custody=actual.pendingDeclaration(actualRootReads);
        Optional<Pending> pending=custody.isPresent()?Optional.of(project(custody.orElseThrow())):Optional.empty();
        Capture result=new Capture(actual,custody,pending);result.requireCurrent(actual,actualRootReads);return result;
    }
    private static Pending project(ArmyWarReads.PendingDeclaration pending)throws IOException {
        var selected=pending.selection();var c=selected.context();var request=pending.request();var unknown=pending.originalUnknown();
        require(selected.input().method()==PublicMethod.QUERY_DECLARABLE_WARS&&request.equals(new PlanningReadRequest(c.before(),c.source(),c.sessionId(),pending.contract().operation(),ArmyWarReads.arguments(selected.input()),c.deadline())),"pending diagnostic crossed original request/selection");
        require(pending.contract().wireProfile()==ReadContract.WireProfile.EXECUTE_STEP,"actual declaration wire profile differs");
        var sent=NativeWire.decodeExecuteRequest(unknown.originalRequestPacket());
        var prepared=pending.contract().prepare(request,unknown.requestId());
        require(sent.requestId().equals(unknown.requestId())&&sent.step().equals("query-declarable-wars")&&sent.step().equals(request.operation().value())
                &&sent.expectedRevision().filter(c.nativeRevision()::equals).isPresent()&&sent.expectedSnapshotRevision().isEmpty()
                &&parse(sent.normalizedAdditionalFields().value()).equals(parse(prepared.additionalFields().bytes())),"pending diagnostic differs from its original sent packet");
        Binding binding=binding(pending);BigDecimal seconds=BigDecimal.valueOf(pending.originalTimeout().getSeconds()).add(BigDecimal.valueOf(pending.originalTimeout().getNano(),9)).stripTrailingZeros();
        if(seconds.scale()<1)seconds=seconds.setScale(1);
        ObjectNode n=empty().put("request_id",unknown.requestId()).put("step",request.operation().value()).put("status","pending").put("timeout_seconds",seconds);
        n.set("binding",OpportunityJson.toNode(binding.encode()));
        return new Pending(unknown.requestId(),request.operation(),binding,pending.originalTimeout(),DriverJson.object(bytes(n),DriverJson.MAX_NATIVE_BYTES));
    }
    private static Binding binding(ArmyWarReads.PendingDeclaration pending) {
        var selected=pending.selection();var c=selected.context();var actual=selected.frame().actual();
        ObjectNode n=object(OpportunityJson.toNode(actual.semantic()));ObjectNode played=object(get(n,"played_character"));ObjectNode diagnostic=object(get(n,"diagnostics"));
        String snapshot=nonempty(get(n,"snapshot_id")),episode=nonempty(get(n,"episode_run_id"));
        BigInteger revision=integer(get(n,"revision")),nativeRevision=positive(get(n,"native_revision")).value(),connection=positive(get(diagnostic,"connection_generation")).value();
        int date=i32(get(n,"date_raw")),actor=i32(get(played,"character_id"));long pid=i64(get(diagnostic,"bridge_pid"));
        boolean paused=bool(get(n,"paused")),mapReady=bool(get(n,"map_ready"));require(paused&&mapReady,"original pending declaration was not a paused map");
        require(snapshot.equals(c.before().frame().snapshotId())&&revision.equals(c.before().frame().revision())&&nativeRevision.equals(c.nativeRevision())
                &&episode.equals(c.before().frame().episodeRunId())&&BigInteger.valueOf(date).equals(c.dateRaw())&&BigInteger.valueOf(actor).equals(c.playerId())
                &&pid==c.before().game().pid()&&connection.equals(actual.connectionGeneration())&&actual.identity().equals(c.before())
                &&actual.source().equals(c.source())&&actual.sessionId().equals(c.sessionId()),"pending diagnostic binding differs from its original complete Driver source");
        return new Binding(snapshot,revision,nativeRevision,episode,date,paused,mapReady,actor,pid,connection);
    }
}
