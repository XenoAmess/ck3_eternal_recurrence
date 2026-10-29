package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadGuard;
import org.xar.ck3.control.application.action.PlanningReadReceipt;
import org.xar.ck3.control.application.action.PlanningReadRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ReadContract;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityCodec;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.RequestContext;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.Snapshot;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeWire;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Currency;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * Production private READ callback over the coordinator's original ACK and archived guard frames.
 * The returned contract must be installed by the existing Root source/permission authority.
 * Constructing this factory supplies neither that authority nor Root startup inputs.
 */
public final class CrownAuthorityNativeRead {
    public static final String STEP="query-realm-law-crown-action-v1-private";
    public static final String CONTRACT_ID="realm-law-crown-native-read-v1";
    public static final String PERMISSION_KEY="realm-law-crown-formal-private";
    private CrownAuthorityNativeRead() { }

    /** No mutable current provider, action grant, cross-request reuse or historical replay is registered here. */
    public static ReadContract<CrownAuthorityCodec.Request> contract(ExactRef actualDefinition,
            boolean privateLawEnabled,ActionPorts.OutcomeArchive archive,NativeEffectEvidence.FrameLoader originalFrames) {
        Objects.requireNonNull(archive);Objects.requireNonNull(originalFrames);
        return new ReadContract<>(CONTRACT_ID,new OperationKey(STEP),Optional.empty(),PERMISSION_KEY,
                ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.G2_PRIVATE_QUERY,
                ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,actualDefinition,
                (PlanningReadRequest request,String requestId)->prepare(request,privateLawEnabled),
                receipt->returned(receipt,privateLawEnabled,archive,originalFrames));
    }
    /** The shared coordinator owns request_id and expected_revision; native fields retain their original spelling. */
    public static NativeRequest prepare(PlanningReadRequest request,boolean privateLawEnabled) {
        StrictJson.require(privateLawEnabled,"private native crown law READ is disabled");
        StrictJson.require(request.operation().equals(new OperationKey(STEP)),"wrong native crown operation");
        reserves(request);
        var frame=request.before().frame().identity();
        ObjectNode fields=StrictJson.object();
        fields.put("expected_date_raw",frame.dateRaw());fields.put("expected_player_character_id",frame.player());
        return new NativeRequest(STEP,Optional.empty(),new RawJson(StrictJson.canonical(fields)));
    }
    /** Existing ReadContract.decode calls this only after its exact receipt/operation/source checks. */
    public static CrownAuthorityCodec.Request returned(PlanningReadReceipt receipt,boolean privateLawEnabled,
            ActionPorts.OutcomeArchive archive,NativeEffectEvidence.FrameLoader originalFrames) {
        StrictJson.require(receipt.contractId().equals(CONTRACT_ID)&&receipt.request().operation().equals(new OperationKey(STEP))
                &&receipt.original().nativeOk(),"wrong successful native crown callback");
        var beforeComplete=RootGuardEvidence.loadFrame(receipt.before().binding(),archive,originalFrames);
        var afterComplete=RootGuardEvidence.loadFrame(receipt.after().binding(),archive,originalFrames);
        StrictJson.require(beforeComplete.identity().equals(receipt.request().before()),
                "native crown callback before original differs from the actual query request frame");
        Snapshot before=snapshot(beforeComplete,receipt.before());
        Snapshot after=snapshot(afterComplete,receipt.after());
        var context=new RequestContext(receipt.requestId(),receipt.request().before().frame().revision(),privateLawEnabled,before);
        RawJson original=receipt.original().originalResultToken().orElseThrow(
                ()->new IllegalArgumentException("missing unchanged original native crown RESULT"));
        var nativeResult=CrownAuthorityNativeWire.decodeResult(receipt.original().requestId(),original.bytes());
        return CrownAuthorityNativeQuery.consumerRequest(context,nativeResult,after,reserves(receipt.request()));
    }
    public static CrownAuthorityPolicy.Choice project(CrownAuthorityCodec.Request returned) {
        return CrownAuthorityPolicy.choose(returned.readback(),returned.reservesRaw());
    }
    private static Snapshot snapshot(org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete actual,
            PlanningReadGuard guard) {
        StrictJson.require(guard.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,"native crown query requires gameplay originals");
        ObjectNode row=object(OpportunityJson.toNode(actual.semantic()));
        ObjectNode hello=object(object(row.get("diagnostics")).get("hello"));
        var source=new CrownAuthorityNativeWire.Source(text(hello,"expected_ck3_version"),text(hello,"expected_ck3_sha256"));
        StrictJson.require(source.gameVersion().equals(actual.source().exactBuild()),"native hello and actual source build differ");
        var actor=CrownAuthorityNativeQuery.Actor.fromOriginal(row.get("played_character"));
        var frame=actual.identity().frame();var identity=frame.identity();
        String snapshotId=text(row,"snapshot_id");BigInteger revision=number(row,"revision");
        BigInteger nativeRevision=number(row,"native_revision");BigInteger date=number(row,"date_raw");
        boolean paused=bool(row,"paused"),mapReady=bool(row,"map_ready");
        StrictJson.require(snapshotId.equals(frame.snapshotId())&&revision.equals(frame.revision())
                &&nativeRevision.equals(identity.nativeRevision())&&date.equals(identity.dateRaw())
                &&actor.characterId().equals(identity.player()),"actual native crown semantic/projection binding differs");
        StrictJson.require(paused==guard.paused()&&mapReady==guard.mapReady()&&actor.alive()==guard.playerAlive(),
                "actual native crown guard readiness differs from its original semantic");
        return new Snapshot(source,Optional.of(snapshotId),revision,nativeRevision,date,actor,paused,mapReady);
    }
    /** Sole typed producer of the Java query/selector arguments; native submission fields remain coordinator-owned. */
    public static OpportunityJson.Obj arguments(Map<Currency,BigInteger> reservesRaw) {
        ObjectNode row=StrictJson.object();row.set("reserves_raw",StrictJson.parse(CrownAuthorityCodec.encodeReserves(reservesRaw)));
        return OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(row)),"Crown query arguments");
    }
    private static Map<Currency,BigInteger> reserves(PlanningReadRequest request) {return decodeArguments(request.arguments());}
    public static Map<Currency,BigInteger> decodeArguments(OpportunityJson.Obj actual) {
        ObjectNode row=StrictJson.object(OpportunityJson.toNode(actual),Set.of("reserves_raw"));
        return CrownAuthorityCodec.decodeReserves(StrictJson.canonical(row.get("reserves_raw")));
    }

    private static ObjectNode object(JsonNode value){StrictJson.require(value instanceof ObjectNode,"original object required");return (ObjectNode)value;}
    private static String text(ObjectNode row,String field){return StrictJson.text(row.get(field));}
    private static BigInteger number(ObjectNode row,String field){
        JsonNode value=row.get(field);StrictJson.require(value!=null&&value.isIntegralNumber(),"actual integer required: "+field);return value.bigIntegerValue();
    }
    private static boolean bool(ObjectNode row,String field){
        JsonNode value=row.get(field);StrictJson.require(value!=null&&value.isBoolean(),"actual boolean required: "+field);return value.booleanValue();
    }
}
