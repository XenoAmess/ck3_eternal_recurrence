package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadlineCodec;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m7.schedule.OrdinaryCampaignSchedule;

/** Required configuration and registration DATA only; no managed Game, writer or policy execution is fabricated. */
final class RootCampaignPoliciesFactoryTest {
    private static final CampaignDeadline.Configuration CONFIG=CampaignDeadline.configure(
            new CampaignDeadline.Founding("software-campaign","1066.9.15",BigInteger.valueOf(
                    org.xar.ck3.control.planning.campaigncadence.CampaignCalendar.dateToRaw("1066.9.15")),360),
            OrdinaryCampaignSchedule::calendar,Optional.empty());
    @Test void actualDeadlineCodecAndExactSourceAreMandatoryAndDefensivelyCopied(){
        byte[] raw=CampaignDeadlineCodec.encodeConfiguration(CONFIG);var ref=ref("deadline.json",raw);
        var bound=new RootCampaignPoliciesFactory.BoundDeadline(ref,raw);raw[0]=0;
        assertEquals(CONFIG,bound.configuration());byte[] returned=bound.bytes();returned[0]=0;assertEquals(CONFIG,bound.configuration());
        assertThrows(IllegalArgumentException.class,()->new RootCampaignPoliciesFactory.BoundDeadline(ref,new byte[]{123,125}));
        var missing=assertInstanceOf(ObjectNode.class,StrictJson.parse(bound.bytes()));missing.remove("boundary_raws");
        byte[] missingBytes=StrictJson.canonical(missing);assertThrows(IllegalArgumentException.class,()->new RootCampaignPoliciesFactory.BoundDeadline(ref("missing.json",missingBytes),missingBytes));
        var wrong=assertInstanceOf(ObjectNode.class,StrictJson.parse(bound.bytes()));wrong.put("months",true);
        byte[] wrongBytes=StrictJson.canonical(wrong);assertThrows(IllegalArgumentException.class,()->new RootCampaignPoliciesFactory.BoundDeadline(ref("wrong.json",wrongBytes),wrongBytes));
        assertThrows(NullPointerException.class,()->new RootCampaignPoliciesFactory.Sources(ref("factory.java",new byte[]{1}),ref("policy.java",new byte[]{1}),null));
    }
    @Test void repeatedPreparedRegistrationRetainsTheIdenticalOriginalVerifierObject(){
        var sources=Arrays.stream(RootCrossRunPlanning.ProducerRole.values()).map(role->ref(role.fileName(),new byte[]{1})).toList();
        var prepared=new RootCrossRunPlanning.Prepared(new RootCrossRunPlanning.Sources(new NativeCheckpointFiles(),
                java.nio.file.Path.of("D:/software-fixtures/strategy/one-life-history.json"),sources));
        assertSame(prepared.registrations(),prepared.registrations());
        assertSame(prepared.registrations().getFirst(),prepared.registrations().getFirst());
        assertSame(prepared.domain(),prepared.registrations().getFirst().verifier());
    }
    @Test void typedProducerRolesUseActualLoadedMetadataAndDeduplicateInEnumOrder()throws Exception {
        var cache=new java.util.HashMap<java.nio.file.Path,ExactRef>();
        var roles=new java.util.LinkedHashMap<RootCrossRunPlanning.ProducerRole,ExactRef>();
        var values=RootCrossRunPlanning.ProducerRole.values();
        for(int i=values.length-1;i>=0;i--) {
            Class<?> type=switch(values[i]) {
                case CORE_PRODUCER->RootCrossRunPlanning.class;
                case DOMAIN->org.xar.ck3.control.application.planning.campaign.CrossRunPlanningDomain.class;
                case STRATEGY_SOURCE->org.xar.ck3.control.application.planning.campaign.CrossRunStrategySource.class;
                case STRATEGY_REDUCER->org.xar.ck3.control.application.planning.campaign.CrossRunPlanning.class;
                case LIFECYCLE_REDUCER->org.xar.ck3.control.application.lifecycle.LifecycleReducer.class;
                case TERMINAL_JOIN->TerminalLifecycleDecisionProducer.class;
            };
            roles.put(values[i],actualClassRef(type,cache));
        }
        var expected=new java.util.LinkedHashSet<ExactRef>();for(var role:values)expected.add(roles.get(role));
        var sources=new RootCrossRunPlanning.Sources(new NativeCheckpointFiles(),java.nio.file.Path.of("D:/software-fixtures/strategy/one-life-history.json"),roles);
        roles.clear();
        assertEquals(values.length,sources.roleProducers().size());assertEquals(List.copyOf(expected),sources.producers());
        assertThrows(UnsupportedOperationException.class,()->sources.roleProducers().clear());
        var prepared=new RootCrossRunPlanning.Prepared(sources);
        assertEquals(sources.producers(),prepared.registrations().getFirst().producerSources());
        ExactRef shared=actualClassRef(org.junit.jupiter.api.Test.class,cache);
        var sharedRoles=new java.util.EnumMap<RootCrossRunPlanning.ProducerRole,ExactRef>(RootCrossRunPlanning.ProducerRole.class);
        for(var role:values)sharedRoles.put(role,shared);
        var sharedSources=new RootCrossRunPlanning.Sources(new NativeCheckpointFiles(),java.nio.file.Path.of("D:/software-fixtures/strategy/one-life-history.json"),sharedRoles);
        assertEquals(values.length,sharedSources.roleProducers().size());assertEquals(List.of(shared),sharedSources.producers());
        assertEquals(List.of(shared),new RootCrossRunPlanning.Prepared(sharedSources).registrations().getFirst().producerSources());
    }
    @Test void explicitRolesRejectIncompleteDataWhileTheLegacyJavaConstructorRemainsStrict()throws Exception {
        var files=new NativeCheckpointFiles();var history=java.nio.file.Path.of("D:/software-fixtures/strategy/one-life-history.json");
        var cache=new java.util.HashMap<java.nio.file.Path,ExactRef>();ExactRef actual=actualClassRef(RootCrossRunPlanning.class,cache);
        assertThrows(IllegalArgumentException.class,()->new RootCrossRunPlanning.Sources(files,history,java.util.Map.<RootCrossRunPlanning.ProducerRole,ExactRef>of()));
        var missing=new java.util.EnumMap<RootCrossRunPlanning.ProducerRole,ExactRef>(RootCrossRunPlanning.ProducerRole.class);
        for(var role:RootCrossRunPlanning.ProducerRole.values())missing.put(role,actual);
        missing.remove(RootCrossRunPlanning.ProducerRole.TERMINAL_JOIN);
        assertThrows(IllegalArgumentException.class,()->new RootCrossRunPlanning.Sources(files,history,missing));
        var nullRef=new java.util.EnumMap<RootCrossRunPlanning.ProducerRole,ExactRef>(RootCrossRunPlanning.ProducerRole.class);
        for(var role:RootCrossRunPlanning.ProducerRole.values())nullRef.put(role,actual);
        nullRef.put(RootCrossRunPlanning.ProducerRole.DOMAIN,null);
        assertThrows(NullPointerException.class,()->new RootCrossRunPlanning.Sources(files,history,nullRef));
        var legacy=Arrays.stream(RootCrossRunPlanning.ProducerRole.values()).map(role->ref(role.fileName(),new byte[]{1})).toList();
        assertEquals(legacy,new RootCrossRunPlanning.Sources(files,history,legacy).producers());
        assertThrows(IllegalArgumentException.class,()->new RootCrossRunPlanning.Sources(files,history,legacy.subList(0,legacy.size()-1)));
        var duplicate=new java.util.ArrayList<>(legacy);duplicate.add(legacy.getFirst());
        assertThrows(IllegalArgumentException.class,()->new RootCrossRunPlanning.Sources(files,history,duplicate));
        assertThrows(IllegalArgumentException.class,()->new RootCrossRunPlanning.Sources(files,history,List.of(actual)));
    }
    private static ExactRef actualClassRef(Class<?> type,java.util.Map<java.nio.file.Path,ExactRef> cache)throws Exception {
        var location=type.getProtectionDomain().getCodeSource().getLocation();
        java.nio.file.Path path=java.nio.file.Path.of(location.toURI()).toAbsolutePath().normalize();
        if(java.nio.file.Files.isDirectory(path))path=path.resolve(type.getName().replace('.','/')+".class").normalize();
        ExactRef existing=cache.get(path);if(existing!=null)return existing;
        byte[] bytes=java.nio.file.Files.readAllBytes(path);ExactRef actual=new ExactRef(path.toString(),bytes.length,ActionCodec.sha256(bytes));
        cache.put(path,actual);return actual;
    }
    private static ExactRef ref(String name,byte[] raw){return new ExactRef("D:/software-fixtures/"+name,raw.length,ActionCodec.sha256(raw));}
    @Test void ordinarySupplierWithoutHistoricalMetadataReachesTheRealM7Consumer() {
        var request=ordinaryGoalRequest(new BigInteger("18446744073709551615"),"ordinary-current-frame");
        var original=ordinaryFocus(request);
        var policy=new org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.CampaignAdvancePolicy(
                ref("policy",new byte[]{1}),ignored->Optional.empty(),
                (r,old,step,cap)->{throw new AssertionError("FOCUS is not an advance rewrite");},
                r->RootCampaignPoliciesFactory.Installed.goal(r,Optional.empty()));
        var changed=assertInstanceOf(org.xar.ck3.control.application.planning.OrdinaryPolicy.Replace.class,
                policy.evaluate(request,original)).draft();
        assertSame(original.command().orElseThrow(),changed.command().orElseThrow());
        assertEquals(ActionCodec.bodySha256(original.command().orElseThrow()),ActionCodec.bodySha256(changed.command().orElseThrow()));
        var encoded=org.xar.ck3.control.planning.opportunity.OpportunityJson.encode(changed.detail().get("m7_kernel_plan_consumption"));
        var consumed=org.xar.ck3.control.g2.m7.M7KernelPlanConsumer.decode(encoded);
        assertEquals(Optional.empty(),consumed.observation().sourceEpoch());
        assertEquals(Optional.empty(),consumed.observation().executable());
        assertEquals(request.observations().campaignGoal().orElseThrow(),consumed.observation().goal());
        assertEquals(request.before().game().creationFiletime().value().toString(),consumed.observation().game().creationFiletime());
        assertEquals(request.before().frame().snapshotId(),consumed.observation().snapshotId());
        assertEquals("private-select-player-lifestyle-stock-focus-v1",consumed.selectedStep());
        assertFalse(consumed.gameActionsSubmitted());assertFalse(consumed.coldAuthorityGranted());
        assertFalse(consumed.replayAuthorized());assertEquals(0,consumed.savedDayCredit());
        assertEquals(consumed,org.xar.ck3.control.g2.m7.M7KernelPlanConsumer.decode(
                org.xar.ck3.control.g2.m7.M7KernelPlanConsumer.encode(consumed)));
    }
    @Test void ordinarySupplierCannotPromoteARealProjectionFromAnotherGameBirthOrFrame() {
        var birth=new BigInteger("18446744073709551615");
        var request=ordinaryGoalRequest(birth,"ordinary-current-frame");
        for(var foreign:List.of(ordinaryGoalRequest(birth.subtract(BigInteger.ONE),"ordinary-current-frame"),
                ordinaryGoalRequest(birth,"a-different-current-frame"))) {
            var supplied=RootCampaignPoliciesFactory.Installed.goal(foreign,Optional.empty()).orElseThrow();
            var policy=new org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.CampaignAdvancePolicy(
                    ref("policy",new byte[]{1}),ignored->Optional.empty(),
                    (r,old,step,cap)->{throw new AssertionError("FOCUS is not an advance rewrite");},ignored->Optional.of(supplied));
            assertThrows(IllegalArgumentException.class,()->policy.evaluate(request,ordinaryFocus(request)));
        }
    }
    private static org.xar.ck3.control.application.planning.PlanningRequest ordinaryGoalRequest(BigInteger birth,String snapshotId) {
        var goal=org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal.newGoal("ordinary-software-campaign",31254);
        BigInteger raw=CONFIG.founding().startDateRaw(),nativeRevision=BigInteger.valueOf(224),revision=BigInteger.valueOf(54);
        var snapshot=StrictJson.object();snapshot.put("snapshot_id",snapshotId);snapshot.put("episode_run_id","ordinary-software-episode");
        snapshot.put("revision",revision);snapshot.put("native_revision",nativeRevision);snapshot.put("date_raw",raw);
        snapshot.put("paused",true);snapshot.put("map_ready",true);
        snapshot.putObject("played_character").put("character_id",31254).put("alive",true);
        snapshot.putArray("active_wars");snapshot.putArray("player_armies");
        snapshot.putObject("diagnostics").put("bridge_pid",11).put("connection_generation",1);
        snapshot.set("campaign_goal",StrictJson.parse(org.xar.ck3.control.g2.m7.GoalCodec.encodeGoal(goal)));
        var semantic=org.xar.ck3.control.planning.opportunity.OpportunityJson.object(
                org.xar.ck3.control.planning.opportunity.OpportunityJson.parse(StrictJson.canonical(snapshot)),"software current native DATA");
        var frame=new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.ProposalFrame(
                new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Frame(BigInteger.valueOf(31254),nativeRevision,raw),
                snapshotId,revision,"ordinary-software-episode");
        var before=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity("ordinary-supplier-software",
                new org.xar.ck3.control.contracts.GameGeneration(11,new org.xar.ck3.control.contracts.PythonOnlyUInt64(birth)),frame,3);
        var source=new org.xar.ck3.control.g2.common.G2Source("ordinary-supplier-software","2026-10-30T00:00:00Z",
                "software-only",ref("software-current-source",new byte[]{1}));
        var observation=new org.xar.ck3.control.application.planning.PlanningObservation(semantic,List.of(),java.util.Set.of(),
                java.util.Set.of(),Optional.empty(),List.of(),Optional.of(goal),Optional.empty(),true);
        return new org.xar.ck3.control.application.planning.PlanningRequest(before,source,"ordinary-software-session",
                java.time.Instant.parse("2099-01-01T00:00:00Z"),observation);
    }
    private static org.xar.ck3.control.application.planning.OrdinaryPolicy.Draft ordinaryFocus(
            org.xar.ck3.control.application.planning.PlanningRequest request) {
        var empty=new org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj(java.util.Map.of());
        var expected=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition(1,request.before(),request.source(),"software-only/v1",
                List.of(new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("paused"),true)));
        var command=new org.xar.ck3.control.application.action.ActionCommand("ordinary-existing-focus",request.before(),request.source(),
                request.sessionId(),new org.xar.ck3.control.application.action.OperationKey("private-select-player-lifestyle-stock-focus-v1"),empty,expected,
                new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims(java.util.Set.of(),java.util.Set.of(),java.util.Set.of(),java.util.Set.of()),request.deadline());
        return new org.xar.ck3.control.application.planning.OrdinaryPolicy.Draft("software-existing-focus","focus","same legal FOCUS proposal",
                org.xar.ck3.control.application.planning.OrdinaryPolicy.Kind.OPENING_FOCUS,Optional.of(command),
                org.xar.ck3.control.application.planning.OrdinaryPolicy.Purpose.WORLD_ACTION,Optional.empty(),empty);
    }

}
