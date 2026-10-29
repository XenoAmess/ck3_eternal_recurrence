package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes;
import org.xar.ck3.control.service.mcp.PublicPlanningCodec;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** Source-owned public mapper/formatter regressions. Controlled numeric DATA never grants Root/Game qualification. */
final class RootArmyPublicStepProductsTest {
    private static final BigInteger WIDE=new BigInteger("18446744073709551615");
    private static final Obj EMPTY=new Obj(Map.of());
    private static IntegerValue number(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static IntegerValue number(BigInteger value){return new IntegerValue(value);}
    private static RawJson raw(Obj value){return new RawJson(DriverJson.encode(value));}
    private static Obj parsed(RawJson value){return DriverJson.object(value.bytes(),DriverJson.MAX_NATIVE_BYTES);}
    private static OperationKey step(String value){return new OperationKey(value);}
    private static ArmyTypes.Context context(){
        var source=new G2Source("software-army-step",Instant.EPOCH.toString(),"controlled-data",new ExactRef("software-source",1,"a".repeat(64)));
        var identity=new ObservationIdentity(source.machineId(),new GameGeneration(42,new PythonOnlyUInt64(BigInteger.ONE)),
                new ProposalFrame(new Frame(BigInteger.valueOf(7),BigInteger.valueOf(11),BigInteger.valueOf(53238336)),
                        "native:11",BigInteger.valueOf(7),"software-episode"),1);
        return new ArmyTypes.Context(identity,source,"software-session",Instant.EPOCH.plusSeconds(60));
    }
    private static Obj nativeResult(String selected){return new Obj(Map.of("step",new Text(selected),"accepted",new Bool(true),
            "status",new Text("submitted"),"original_native_extra",new Obj(Map.of("missing_is_distinct",Nil.INSTANCE))));}
    private static Obj army(int id,boolean controllable){return new Obj(Map.of("army_id",number(id),"owner_character_id",number(7),
            "current_province_id",Nil.INSTANCE,"route_province_ids",new Arr(List.of()),"controllable",new Bool(controllable),
            "in_combat",new Bool(false),"retreating",new Bool(false)));}
    private static Obj after(List<Obj> armies){return new Obj(Map.of("player_armies",new Arr(armies.stream().map(value->(Value)value).toList()),
            "snapshot_id",new Text("native:12"),"revision",number(WIDE),"native_revision",number(12),"paused",new Bool(true)));}
    private static Obj material(String selected,Obj action){return new Obj(Map.of("step",new Text(selected),"war_action",action,
            "snapshot_id",new Text("native:12"),"revision",number(WIDE),"original_outbound_sha256",new Text("b".repeat(64))));}
    private static PublicPlanningCodec.ExecuteRequest caller(String selected){return new PublicPlanningCodec.ExecuteRequest(step(selected),
            new PublicPlanningCodec.RevisionMissing(),new PublicPlanningCodec.FrameMissing());}

    @Test void originalTypedSelectorsKeepCUnitZeroAndExcludeOtherOwnersAndMalformedIds(){
        for(String selected:List.of("raise-troops-default","disband-army-0","disband-army-2147483647",
                "assign-army-commander-v1-army-0-to-character-0","assign-army-commander-v1-army-2147483647-to-character-2147483647"))
            assertTrue(RootArmyPublicStepProducts.classify(step(selected)).isPresent(),selected);
        for(String unrelated:List.of("move-army-0-to-1","start-assault-0","stop-assault-1","enforce-demands-0",
                "declare-war-1-2--1","hire-mercenary-v1","query-army-strengths","disband-army-01","disband-army--1",
                "disband-army-2147483648","assign-army-commander-v1-army-00-to-character-1",
                "assign-army-commander-v1-army-2147483648-to-character-1"))
            assertTrue(RootArmyPublicStepProducts.classify(step(unrelated)).isEmpty(),unrelated);
    }

    @Test void raiseOriginalPrimitiveAndObservedFullRosterProduceTheCompleteOriginalShapeAndPublicSerde(){
        String selected="raise-troops-default";
        Obj action=new Obj(Map.of("status",new Text("raised"),"raised_army_ids",new Arr(List.of(number(0),number(9))),"postcondition_verified",new Bool(true)));
        Obj frame=after(List.of(army(0,true),army(9,true)));
        RawJson numeric=RootArmyPublicStepProducts.formatNumeric(RootArmyPublicStepProducts.Kind.RAISE,step(selected),raw(nativeResult(selected)),
                Optional.of(raw(material(selected,action))),Optional.of(frame));
        Obj expected=nativeResult(selected).with("backend_id",new Text("native-headless")).with("war_action",new Obj(Map.of(
                "status",new Text("raised"),"raised_army_ids",new Arr(List.of(number(0),number(9))))))
                .with("player_armies",frame.get("player_armies")).with("snapshot_id",frame.get("snapshot_id")).with("revision",number(WIDE));
        assertEquals(expected,parsed(numeric));assertFalse(((Obj)parsed(numeric).get("war_action")).members().containsKey("postcondition_verified"));
        Obj publicResult=parsed(RootArmyPublicStepProducts.encodeOriginal(numeric,context()));
        assertEquals(new Text(WIDE.toString()),publicResult.get("revision"));
        assertEquals(frame.get("player_armies"),publicResult.get("player_armies"));
        assertEquals(publicResult,parsed(raw(publicResult)));assertFalse(publicResult.members().containsKey("schema"));
        assertFalse(publicResult.members().containsKey("action_id"));assertFalse(publicResult.members().containsKey("queried_revision"));
    }

    @Test void disbandKeepsTheActualEmptyRosterAndExactSelectedCUnit(){
        String selected="disband-army-0";Obj action=new Obj(Map.of("status",new Text("disbanded"),"army_id",number(0)));
        Obj result=parsed(RootArmyPublicStepProducts.formatNumeric(RootArmyPublicStepProducts.Kind.DISBAND,step(selected),raw(nativeResult(selected)),
                Optional.of(raw(material(selected,action))),Optional.of(after(List.of()))));
        assertEquals(new Arr(List.of()),result.get("player_armies"));assertEquals(action,result.get("war_action"));
        Obj wrong=action.with("army_id",number(1));
        assertThrows(IllegalArgumentException.class,()->RootArmyPublicStepProducts.formatNumeric(RootArmyPublicStepProducts.Kind.DISBAND,
                step(selected),raw(nativeResult(selected)),Optional.of(raw(material(selected,wrong))),Optional.of(after(List.of()))));
    }

    @Test void commanderOriginalReturnPreservesRejectedDataNullAndUndeclaredFieldsWithoutAddingAnAppliedClaim(){
        String selected="assign-army-commander-v1-army-0-to-character-0";
        Obj original=nativeResult(selected).with("accepted",new Bool(false)).with("snapshot_revision",number(WIDE))
                .with("army_commander_assignment",new Obj(Map.of("status",new Text("rejected"),"prior_commander_character_id",Nil.INSTANCE)));
        RawJson numeric=RootArmyPublicStepProducts.formatNumeric(RootArmyPublicStepProducts.Kind.COMMANDER,step(selected),raw(original),Optional.empty(),Optional.empty());
        assertEquals(original.with("backend_id",new Text("native-headless")),parsed(numeric));
        Obj publicResult=parsed(RootArmyPublicStepProducts.encodeOriginal(numeric,context()));
        assertEquals(new Text(WIDE.toString()),publicResult.get("snapshot_revision"));assertEquals(new Bool(false),publicResult.get("accepted"));
        assertFalse(publicResult.members().containsKey("world_effect_verified"));assertFalse(publicResult.members().containsKey("war_action"));
        assertEquals(publicResult,parsed(raw(publicResult)));
    }

    @Test void aCanonicalSummaryOrMismatchedFrameCannotSubstituteForTheFullOriginalResult(){
        String selected="raise-troops-default";Obj action=new Obj(Map.of("status",new Text("raised"),"raised_army_ids",new Arr(List.of(number(0)))));
        RawJson nativeBody=raw(nativeResult(selected)),basis=raw(material(selected,action));Obj frame=after(List.of(army(0,true)));
        assertThrows(IllegalArgumentException.class,()->RootArmyPublicStepProducts.formatNumeric(RootArmyPublicStepProducts.Kind.RAISE,step(selected),nativeBody,Optional.empty(),Optional.of(frame)));
        assertThrows(IllegalArgumentException.class,()->RootArmyPublicStepProducts.formatNumeric(RootArmyPublicStepProducts.Kind.RAISE,step(selected),nativeBody,Optional.of(basis),Optional.empty()));
        assertThrows(IllegalArgumentException.class,()->RootArmyPublicStepProducts.formatNumeric(RootArmyPublicStepProducts.Kind.RAISE,step(selected),nativeBody,Optional.of(basis),Optional.of(frame.with("revision",number(1)))));
        assertThrows(IllegalArgumentException.class,()->RootArmyPublicStepProducts.formatNumeric(RootArmyPublicStepProducts.Kind.RAISE,step(selected),raw(nativeResult(selected).with("accepted",number(1))),Optional.of(basis),Optional.of(frame)));
        assertThrows(IllegalArgumentException.class,()->RootArmyPublicStepProducts.formatNumeric(RootArmyPublicStepProducts.Kind.RAISE,step(selected),raw(nativeResult(selected).with("accepted",new Bool(false))),Optional.of(basis),Optional.of(frame)));
        assertThrows(IllegalArgumentException.class,()->RootArmyPublicStepProducts.formatNumeric(RootArmyPublicStepProducts.Kind.RAISE,step(selected),nativeBody,
                Optional.of(raw(material("disband-army-0",action))),Optional.of(frame)));
    }

    @Test void raisedCUnitArrayCannotCoerceBooleanFloatingNullDuplicateOrEmptyValues(){
        String selected="raise-troops-default";Obj frame=after(List.of(army(0,true)));
        for(Value bad:List.of(new Arr(List.of()),new Arr(List.of(new Bool(true))),new Arr(List.of(new DecimalValue("0.0"))),
                new Arr(List.of(Nil.INSTANCE)),new Arr(List.of(number(0),number(0))),new Arr(List.of(number(-1))),new Arr(List.of(number(2147483648L))))){
            Obj action=new Obj(Map.of("status",new Text("raised"),"raised_army_ids",bad));
            assertThrows(IllegalArgumentException.class,()->RootArmyPublicStepProducts.formatNumeric(RootArmyPublicStepProducts.Kind.RAISE,
                    step(selected),raw(nativeResult(selected)),Optional.of(raw(material(selected,action))),Optional.of(frame)));
        }
    }

    @Test void currentCommanderScopeUsesTheOriginalSingleControllableIntegerCUnitWithoutCandidatePolicy(){
        Obj selected=army(0,true);Obj snapshot=new Obj(Map.of("paused",new Bool(true),"player_armies",new Arr(List.of(selected,army(0,false)))));
        assertSame(selected,RootArmyPublicStepProducts.currentCommanderScope(snapshot,0));
        Obj duplicate=snapshot.with("player_armies",new Arr(List.of(selected,selected)));
        assertEquals(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,assertThrows(PublicServiceFailure.class,
                ()->RootArmyPublicStepProducts.currentCommanderScope(duplicate,0)).kind());
        for(Value invalid:List.of(new Bool(true),new DecimalValue("0.0"),new Text("0"),Nil.INSTANCE)){
            Obj changed=selected.with("army_id",invalid);
            assertThrows(PublicServiceFailure.class,()->RootArmyPublicStepProducts.currentCommanderScope(snapshot.with("player_armies",new Arr(List.of(changed))),0));
        }
        assertThrows(PublicServiceFailure.class,()->RootArmyPublicStepProducts.currentCommanderScope(snapshot.with("paused",new Bool(false)),0));
        assertThrows(PublicServiceFailure.class,()->RootArmyPublicStepProducts.currentCommanderScope(snapshot.with("player_armies",Nil.INSTANCE),0));
        assertFalse(selected.members().containsKey("native_carmy_id")); // that private parent must come from the actual typed query
    }

    @Test void explicitCallerSelectionRetainsPresenceAndNeverInvokesTheOrdinaryChooser(){
        var c=context();
        var frame = c.before().frame();
        var snapshot = new Obj(Map.of(
            "paused", new Bool(true),
            "map_ready", new Bool(true),
            "revision", new IntegerValue(frame.revision()),
            "native_revision", new IntegerValue(frame.identity().nativeRevision()),
            "date_raw", new IntegerValue(frame.identity().dateRaw()),
            "snapshot_id", new Text(frame.snapshotId()),
            "episode_run_id", new Text(frame.episodeRunId()),
            "played_character", new Obj(Map.of("character_id", new IntegerValue(frame.identity().player()))),
            "active_wars", new Arr(List.of()),
            "player_armies", new Arr(List.of())
        ));
        var request=new PlanningRequest(c.before(),c.source(),c.sessionId(),c.deadline(),new PlanningObservation(snapshot,List.of(),Set.of(),Set.of(),
                Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false));
        var publicCaller=caller("raise-troops-default");var selection=RootArmyPublicStepProducts.selection(request,publicCaller);
        assertEquals(EMPTY,selection.arguments());assertEquals(publicCaller.step(),selection.operation());
        assertEquals(parsed(PublicPlanningCodec.encodeExecute(publicCaller)),selection.detail().get("original_public_call"));
        assertEquals(selection.detail(),parsed(raw(selection.detail())));
        assertThrows(IllegalArgumentException.class,()->RootArmyPublicStepProducts.selection(request,caller("move-army-0-to-1")));
    }

    @Test void originalNativeRejectionPreservesTheClosedOriginalClassMessageAndEvidence(){
        var original=new ExactRef("software-original-native-rejection",3,"c".repeat(64));
        var failure=RootArmyPublicStepProducts.nativeFailure(new Obj(Map.of("error",new Text("CK3 command validation failed"))),Optional.of(original));
        assertEquals(PublicServiceFailure.Kind.NATIVE_COMMAND_REJECTED,failure.kind());
        assertEquals("_NativeCommandRejectedError",failure.kind().pythonClassName());
        assertEquals("native gameplay step failed: CK3 command validation failed",failure.getMessage());
        assertEquals(Optional.of(original),failure.originalCandidate());
        assertEquals("native gameplay step failed: unknown error",RootArmyPublicStepProducts.nativeFailure(EMPTY,Optional.empty()).getMessage());
    }

    @Test void unknownRetainsItsOriginalEvidenceAndBeforeWriteRefusalKeepsTheActualDiagnostic(){
        var evidence=new ExactRef("software-original-unknown-dispatch",3,"d".repeat(64));
        var unknown=new NativeActionPort.Unknown("software-request","reply was not observed",new byte[]{1},Optional.empty());
        var failure=RootArmyPublicStepProducts.dispatchFailure(step("disband-army-0"),unknown,Optional.of(evidence));
        assertEquals(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,failure.kind());
        assertEquals("native command_result timed out for gameplay step disband-army-0",failure.getMessage());
        assertEquals(Optional.of(evidence),failure.originalCandidate());
        var beforeWrite=new NativeActionPort.RejectedBeforeDispatch("software-request",new NativeActionPort.ZeroDispatchProof(
                NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,0,"actual transport refused before the first byte",Optional.empty()));
        assertEquals("actual transport refused before the first byte",RootArmyPublicStepProducts.dispatchFailure(
                step("disband-army-0"),beforeWrite,Optional.of(evidence)).getMessage());
        assertEquals(0,beforeWrite.proof().requestBytesWritten());
        // These are source-shaped DATA; no Root or second submission callback exists in this test.
    }
    @Test void originalCommanderRevisionValidationIsNonnegativeAndPreservesMissingAndNullErrors(){
        String selected="assign-army-commander-v1-army-0-to-character-0";
        for(BigInteger value:List.of(BigInteger.ZERO,BigInteger.valueOf(7)))
            assertDoesNotThrow(()->RootArmyPublicStepProducts.requireCommanderRevision(new PublicPlanningCodec.ExecuteRequest(step(selected),
                    new PublicPlanningCodec.RevisionValue(value),new PublicPlanningCodec.FrameMissing())));
        for(PublicPlanningCodec.Revision missing:List.of(new PublicPlanningCodec.RevisionMissing(),new PublicPlanningCodec.RevisionNull())){
            var failure=assertThrows(PublicServiceFailure.class,()->RootArmyPublicStepProducts.requireCommanderRevision(
                    new PublicPlanningCodec.ExecuteRequest(step(selected),missing,new PublicPlanningCodec.FrameMissing())));
            assertEquals(PublicServiceFailure.Kind.VALUE_ERROR,failure.kind());
            assertEquals("expected_revision must be a non-negative integer",failure.getMessage());
        }
    }

}
