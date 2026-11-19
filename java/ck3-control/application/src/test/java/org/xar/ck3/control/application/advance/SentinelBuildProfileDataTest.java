package org.xar.ck3.control.application.advance;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Request/expected-postcondition DATA only; no Root, lease, ACK custody or fresh query is minted. */
@org.junit.jupiter.api.condition.EnabledIfSystemProperty(named="xar.sentinel148.inputs",matches=".+")
final class SentinelBuildProfileDataTest {
    private ActionCommand original()throws Exception {
        var index=StrictJson.parse(Files.readAllBytes(Path.of(System.getProperty("xar.sentinel148.inputs"))));
        var ref=ExactRef.fromJson(index.path("command25"));byte[] raw=Files.readAllBytes(Path.of(ref.path()));
        assertEquals(ref.bytes(),raw.length);assertEquals(ref.sha256(),ActionCodec.sha256(raw));
        return ActionCodec.decodeCommand(raw);
    }
    private static String step(ActionCommand original){
        BigInteger start=original.before().frame().identity().dateRaw();
        return FullSnapshotDateSentinelArm.PREFIX+start+"-to-"+start.add(BigInteger.valueOf(168))+"-speed-5-mode-terminal-a-0";
    }
    private static ActionCommand command(ActionCommand original,G2Source source,String step){
        var op=new OperationKey(step);var args=new OpportunityJson.Obj(Map.of());
        return new ActionCommand("software-bb3-sentinel-data",original.before(),source,original.sessionId(),op,args,
                AdvancePrimitives.expected(original.before(),source,op,args),original.claims(),original.deadline());
    }
    @Test void explicitBb3ClaimPreservesOriginalFrameDeadlineAndLegacyDefault()throws Exception {
        var original=original();var frame=original.before().frame();String step=step(original);
        var bb3=FullSnapshotDateSentinelArm.request(ExactCk3Build.CK3_1210_STEAM_26757580,step,frame.snapshotId(),frame.identity().nativeRevision(),original.deadline());
        var claim=StrictJson.parse(bb3.additionalFields().bytes()).path("date_sentinel_arm");
        assertEquals("ck3_1210_date_sentinel_arm_v1",claim.path("schema").textValue());
        assertEquals(ExactCk3Build.CK3_1210_STEAM_26757580.executableSha256().toUpperCase(java.util.Locale.ROOT),claim.path("executable_sha256").textValue());
        assertEquals("ck3-1.21.0-26757580-msvc-x64",claim.path("adapter_id").textValue());
        assertEquals(frame.snapshotId(),claim.path("snapshot_id").textValue());assertEquals(frame.identity().nativeRevision(),claim.path("native_revision").bigIntegerValue());
        assertEquals(original.deadline().toEpochMilli(),claim.path("deadline_unix_ms").longValue());
        var legacy=FullSnapshotDateSentinelArm.request(step,frame.snapshotId(),frame.identity().nativeRevision(),original.deadline());
        assertEquals(ExactCk3Build.CK3_1210.executableSha256().toUpperCase(java.util.Locale.ROOT),StrictJson.parse(legacy.additionalFields().bytes()).path("date_sentinel_arm").path("executable_sha256").textValue());
        assertThrows(RuntimeException.class,()->FullSnapshotDateSentinelArm.request(null,step,frame.snapshotId(),frame.identity().nativeRevision(),original.deadline()));
        assertThrows(RuntimeException.class,()->FullSnapshotDateSentinelArm.request(ExactCk3Build.CK3_1210_STEAM_26757580,step,"native:999",frame.identity().nativeRevision(),original.deadline()));
        assertThrows(RuntimeException.class,()->FullSnapshotDateSentinelArm.request(ExactCk3Build.CK3_1210_STEAM_26757580,step.replace("terminal-a-0","decision-a-0"),frame.snapshotId(),frame.identity().nativeRevision(),original.deadline()));
    }
    @Test void centralArmPreparationSelectsExactBuildAndRejectsChangedDateOrArguments()throws Exception {
        var original=original();var arm=command(original,original.source(),step(original));
        var actual=AdvancePrimitives.prepareRequest(arm);
        assertEquals(FullSnapshotDateSentinelArm.request(ExactCk3Build.CK3_1210_STEAM_26757580,arm.operation().value(),arm.before().frame().snapshotId(),arm.before().frame().identity().nativeRevision(),arm.deadline()).additionalFields(),actual.additionalFields());
        var unknown=new G2Source(original.source().machineId(),original.source().observedAtUtc(),"unqualified-software-build",original.source().sourceRef());
        assertEquals("{}",new String(AdvancePrimitives.prepareRequest(command(original,unknown,step(original))).additionalFields().bytes(),java.nio.charset.StandardCharsets.UTF_8));
        var bad=new ActionCommand(arm.actionId(),arm.before(),arm.source(),arm.sessionId(),new OperationKey(step(original).replace("-speed-5", "-speed-4")),
                new OpportunityJson.Obj(Map.of("external_actor",new OpportunityJson.IntegerValue(BigInteger.ONE))),arm.expected(),arm.claims(),arm.deadline());
        assertThrows(RuntimeException.class,()->AdvancePrimitives.prepareRequest(bad));
    }
    @Test void bb3CancellationSelectsCompleteOriginalProofWhileUnknownAndLegacyRemainDistinct()throws Exception {
        var original=original();var bb3=command(original,original.source(),ClockStatusRead.CANCEL_PREFIX+"19");
        assertTrue(FullSnapshotSentinelCancellation.supports(bb3));
        assertEquals(FullSnapshotSentinelCancellation.expected(bb3.operation().value()),bb3.expected().values());
        assertTrue(bb3.expected().values().stream().anyMatch(v->v instanceof ExpectedBoolean value&&value.field().value().equals("sentinel.cancel_confirmed")&&value.value()));
        var old=new G2Source(original.source().machineId(),original.source().observedAtUtc(),ExactCk3Build.CK3_1210.executableSha256(),original.source().sourceRef());
        assertTrue(FullSnapshotSentinelCancellation.supports(command(original,old,bb3.operation().value())));
        var unknown=new G2Source(original.source().machineId(),original.source().observedAtUtc(),"unqualified-software-build",original.source().sourceRef());
        var generic=command(original,unknown,bb3.operation().value());assertFalse(FullSnapshotSentinelCancellation.supports(generic));
        assertNotEquals(bb3.expected().values(),generic.expected().values());
        assertTrue(AdvancePrimitives.prepareRequest(bb3).preparationEvidence().isEmpty());
    }
}
