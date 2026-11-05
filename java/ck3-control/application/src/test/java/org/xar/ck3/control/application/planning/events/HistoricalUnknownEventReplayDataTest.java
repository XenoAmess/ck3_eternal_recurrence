package org.xar.ck3.control.application.planning.events;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.TreeSet;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowModels;
import org.xar.ck3.control.nativebridge.capabilities.events.EventWindowService;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewedEventConsumer;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;

/** Public source DATA only: no Session, Root issuer, Native request, dispatch or gameplay authority. */
public final class HistoricalUnknownEventReplayDataTest {
    @TempDir Path temporary;

    @Test void recordedUnknownReplaysTheWholeCommandAfterSourceKnowledgeChanges() throws Exception {
        Path commandPath=input("canonical"), beforePath=input("before"), entryPath=input("entry"), factsPath=input("facts");
        byte[] commandRaw=exact(commandPath,14197,"04eae307534706791689427bcc95b771035f25a735afbcb28829f1fe5d692462");
        byte[] beforeRaw=exact(beforePath,10865,"9a4bd053ea3fca7242c66cea8e3739bfc5e0e64a6f7f6b9ff440200865dce3f5");
        byte[] entryRaw=exact(entryPath,1221,"0a3da165a758a51a16fb333485147a48c789d637e064b5214257be1fe802437a");
        byte[] factsRaw=exact(factsPath,12234,"012931d0fe4a2001ba41f2fcc97e4056f0afd321a0a875a040cdf376e94d5cf9");
        ActionCommand original=ActionCodec.decodeCommand(commandRaw);
        assertArrayEquals(commandRaw,ActionCodec.encodeCommand(original));
        ObjectNode before=(ObjectNode)StrictJson.parse(beforeRaw,32768);
        ObjectNode recorded=before.deepCopy();
        recorded.remove(List.of("incident_id","stage","captured_at_utc","dispatch_attempted"));
        ObjectNode canonicalArguments=(ObjectNode)DriverJson.toNode(original.arguments());
        assertEquals(canonicalArguments.get("unhandled_event_fallback"),recorded);
        ObjectNode snapshot=snapshot(before,canonicalArguments);
        ObjectNode core=(ObjectNode)before.get("original_registry_decision");
        PlanningObservation observation=new PlanningObservation(opportunity(snapshot),List.of(),
                Set.of(original.operation(),new OperationKey(RegisteredEventCore.EVENT_QUERY)),Set.of(),
                Optional.empty(),List.of(),Optional.empty(),Optional.empty(),false);
        PlanningRequest request=new PlanningRequest(original.before(),original.source(),original.sessionId(),original.deadline(),observation);
        OrdinaryPolicy.Draft previous=new OrdinaryPolicy.Draft(core.path("policy").asText(),core.path("phase").asText(),core.path("reason").asText(),
                OrdinaryPolicy.Kind.FOREGROUND,Optional.empty(),OrdinaryPolicy.Purpose.READ_ONLY,Optional.empty(),opportunity(core));
        var validator=EventWindowService.validator(ignored->EventWindowModels.Build.CROZIER4);
        Path state=Files.createDirectory(temporary.resolve("isolated-state"));
        Path stock=Path.of(required("stock_root")).toAbsolutePath().normalize();
        TrustedEventSourceContext trusted=TrustedEventSourceContext.open("xenoamess-full-tower-eb9d2c1186",state,stock);
        Optional<TrustedEventSourceContext> context=Optional.of(trusted);
        exactCommand(original,commandRaw,EventPolicies.replayLegacyFirstDisplayed(request,previous,context,validator,original.expected()));
        exactCommand(original,commandRaw,EventPolicies.replayLegacyFirstDisplayed(request,previous,context,validator,original.expected(),opportunity(recorded)));

        // A declared test namespace projection only; all four frozen originals remain unchanged.
        ObjectNode entry=(ObjectNode)StrictJson.parse(entryRaw,65536);
        String fingerprint=entry.path("fingerprint").textValue();assertNotNull(fingerprint);assertTrue(fingerprint.matches("[0-9a-f]{64}"));
        assertTrue(Path.of(entry.path("source_path").textValue()).normalize().startsWith(stock.resolve("events")));
        Path registry=state.resolve("evidence/event-source-registry");
        Path projectedFacts=Files.createDirectories(registry.resolve("facts")).resolve(fingerprint+".json");
        Files.write(projectedFacts,factsRaw);
        ObjectNode projectedEntry=entry.deepCopy();
        ((ObjectNode)projectedEntry.get("source_facts")).put("path",projectedFacts.toString());
        ObjectNode inverse=projectedEntry.deepCopy();
        ((ObjectNode)inverse.get("source_facts")).put("path",entry.path("source_facts").path("path").textValue());
        assertEquals(entry,inverse,"only fixture facts-path remapping is allowed");
        byte[] projectedEntryRaw=StrictJson.canonical(projectedEntry,65536);
        Files.write(registry.resolve(fingerprint+".json"),projectedEntryRaw);
        var lookup=SourceReviewedEventConsumer.lookup(RetainedJson.object(RetainedJson.parse(OpportunityJson.encode(opportunity(recorded)))),trusted);
        assertTrue(lookup.entry().isPresent(),"actual trusted source/facts reader must validate the fixture entry");
        ActionCommand current=EventPolicies.replayLegacyFirstDisplayed(request,previous,context,validator,original.expected());
        ObjectNode currentArguments=(ObjectNode)DriverJson.toNode(current.arguments());
        assertTrue(currentArguments.path("active_event").path("source_registry_known").booleanValue());
        assertEquals("source_reviewed_known",currentArguments.path("active_event").path("source_knowledge_status").textValue());
        assertFalse(currentArguments.path("event_decision").path("material_effects_verified").booleanValue());
        assertFalse(currentArguments.path("event_decision").path("registry_contract_accepted").booleanValue());
        assertNotEquals(original.arguments(),current.arguments());
        List<String> differences=new ArrayList<>();differences(canonicalArguments,currentArguments,"",differences);
        assertTrue(differences.contains("/active_event/source_knowledge_status"));assertTrue(differences.size()<=64);
        exactCommand(original,commandRaw,EventPolicies.replayLegacyFirstDisplayed(request,previous,context,validator,original.expected(),opportunity(recorded)));
        assertEquals(current.arguments(),EventPolicies.replayLegacyFirstDisplayed(request,previous,context,validator,original.expected()).arguments(),
                "historical replay must leave ordinary current lookup intact");

        ObjectNode malformed=recorded.deepCopy();((ObjectNode)malformed.get("source_knowledge")).put("untrusted_known_flag",true);
        assertThrows(IllegalArgumentException.class,()->EventPolicies.replayLegacyFirstDisplayed(request,previous,context,validator,original.expected(),opportunity(malformed)));
        exactCommand(original,commandRaw,EventPolicies.replayLegacyFirstDisplayed(request,previous,context,validator,original.expected(),opportunity(recorded)));
        assertArrayEquals(commandRaw,Files.readAllBytes(commandPath));assertArrayEquals(beforeRaw,Files.readAllBytes(beforePath));
        assertArrayEquals(entryRaw,Files.readAllBytes(entryPath));assertArrayEquals(factsRaw,Files.readAllBytes(factsPath));
        trusted.verifyCurrentRoots();
        ObjectNode result=StrictJson.object().put("schema","xar.p064-public-producer-data-case/v1")
                .put("canonical_bytes",commandRaw.length).put("canonical_sha256",sha(commandRaw))
                .put("current_lookup_source_known",true).put("historical_whole_command_equal",true)
                .put("ordinary_lookup_preserved",true).put("audit_denials",1).put("restored_positive",true)
                .put("original_inputs_unchanged",true).put("fixture_facts_path_projection_only",true)
                .put("private_root_authority",false).put("native_or_gameplay_calls",0).put("actual_B21_vector",false);
        var changed=result.putArray("public_DATA_changed_fields");differences.forEach(changed::add);
        System.out.write(StrictJson.canonical(result,8192));System.out.write(10);System.out.flush();
    }
    private static ObjectNode snapshot(ObjectNode before,ObjectNode canonicalArguments) {
        ObjectNode binding=(ObjectNode)before.get("binding"),snapshot=StrictJson.object();
        for(String field:List.of("snapshot_id","revision","native_revision","date_raw","episode_run_id","paused","map_ready")) {
            assertNotNull(binding.get(field));snapshot.set(field,binding.get(field));
        }
        snapshot.putObject("played_character").set("character_id",binding.get("actor_character_id"));
        var diagnostics=snapshot.putObject("diagnostics");diagnostics.set("bridge_pid",binding.get("bridge_pid"));
        diagnostics.set("connection_generation",binding.get("connection_generation"));
        ObjectNode summary=((ObjectNode)canonicalArguments.get("active_event")).deepCopy();
        summary.remove(List.of("selected_option_number","selected_native_option_index","selected_rendered_index","semantic_optimal","source_registry_known","source_knowledge_status"));
        snapshot.putArray("active_wars");snapshot.putArray("player_armies");
        snapshot.set("active_event",summary);return snapshot;
    }
    private static OpportunityJson.Obj opportunity(ObjectNode value) {
        return OpportunityJson.object(DriverJson.fromNode(value),"frozen public producer DATA");
    }
    private static void exactCommand(ActionCommand original,byte[] canonical,ActionCommand actual) {
        assertEquals(original.arguments(),actual.arguments());
        var normalized=DriverJson.object(ActionCodec.encodeCommand(actual),ActionCodec.MAX_COMMAND_BYTES)
                .with("action_id",new OpportunityJson.Text(original.actionId()));
        assertArrayEquals(canonical,PublicDataJson.encodeTyped(normalized).bytes());
    }
    private static Path input(String key) {return Path.of(required(key)).toAbsolutePath().normalize();}
    private static String required(String key) {
        String value=System.getProperty("ck3.p064."+key);assertNotNull(value,"explicit frozen DATA/config property required: "+key);return value;
    }
    private static byte[] exact(Path path,int bytes,String hash)throws Exception {
        byte[] raw=Files.readAllBytes(path);assertEquals(bytes,raw.length);assertEquals(hash,sha(raw));return raw;
    }
    private static String sha(byte[] raw)throws Exception {return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));}
    private static void differences(JsonNode left,JsonNode right,String path,List<String> result) {
        if(Objects.equals(left,right))return;
        if(left!=null&&right!=null&&left.isObject()&&right.isObject()) {
            var names=new TreeSet<String>();((ObjectNode)left).properties().forEach(entry->names.add(entry.getKey()));
            ((ObjectNode)right).properties().forEach(entry->names.add(entry.getKey()));
            for(String name:names)differences(left.get(name),right.get(name),path+"/"+name.replace("~","~0").replace("/","~1"),result);
        } else if(left!=null&&right!=null&&left.isArray()&&right.isArray()&&left.size()==right.size()) {
            for(int i=0;i<left.size();i++)differences(left.get(i),right.get(i),path+"/"+i,result);
        } else result.add(path);
    }
}
