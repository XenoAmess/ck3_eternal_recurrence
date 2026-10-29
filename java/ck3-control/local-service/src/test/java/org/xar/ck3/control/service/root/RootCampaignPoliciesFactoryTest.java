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
}
