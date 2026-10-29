package org.xar.ck3.control.nativebridge.capabilities.aub;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Optional;
import java.util.List;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.aub.AubOperations.*;

/** The complete native mailbox serializers have no existing standalone link-qualified fixture.
 * An exact retained producer capture is mandatory; absent input is FAIL/NOT_RUN, never a green skip. */
final class AubOperationsProducerTest {
    @TempDir Path temporary;
    private int sequence;
    private record Capture(ObjectNode root,ObservationIdentity before,BigInteger generation) { }
    private Capture actual()throws Exception {
        String path=System.getProperty("xar.aub.family.producer.capture");String sha=System.getProperty("xar.aub.family.producer.capture.sha256");
        String executable=System.getProperty("xar.aub.family.native.producer");
        if(executable!=null) {
            String executableSha=System.getProperty("xar.aub.family.native.producer.sha256"),sourceRefs=System.getProperty("xar.aub.family.native.sources");
            if(!Path.of(executable).isAbsolute()||executableSha==null||!executableSha.matches("[a-f0-9]{64}")||sourceRefs==null||!Path.of(sourceRefs).isAbsolute())throw new IllegalStateException("NOT EXECUTED: exact standalone native serializer executable SHA and source-ref array required");
            var executablePin=SharedSourceFiles.observe(Path.of(executable));assertEquals(executableSha,executablePin.source().sha256());
            var refsPin=SharedSourceFiles.observe(Path.of(sourceRefs));Path output=temporary.resolve("producer-"+(++sequence)+".json"),error=temporary.resolve("producer-"+sequence+".stderr");
            Process producer=new ProcessBuilder(executable,"serialization",sourceRefs).redirectOutput(output.toFile()).redirectError(error.toFile()).start();
            if(!producer.waitFor(20,TimeUnit.SECONDS)){producer.destroyForcibly();throw new IOException("actual AUB native serializer timeout");}
            if(producer.exitValue()!=0)throw new IOException("actual AUB native serializer failed: "+Files.readString(error,StandardCharsets.UTF_8));
            SharedSourceFiles.assertUnchanged(executablePin);SharedSourceFiles.assertUnchanged(refsPin);path=output.toString();sha=SharedSourceFiles.observe(output).source().sha256();
        }
        if(path==null||!Path.of(path).isAbsolute()||sha==null||!sha.matches("[a-f0-9]{64}"))throw new IllegalStateException("NOT EXECUTED: actual native family producer executable or exact retained capture required; native business delta's {} decision-model link stub is insufficient");
        var pin=SharedSourceFiles.observe(Path.of(path));assertEquals(sha,pin.source().sha256());ObjectNode root=NativeWire.object(NativeWire.parse(Files.readAllBytes(Path.of(path))));
        assertEquals("xar.aub.actual-native-family-serialization-input/v1",root.path("schema").textValue());
        ObjectNode binding=NativeWire.object(root.get("binding"));assertTrue(binding.path("machine_id").isTextual());
        var before=new ObservationIdentity(binding.get("machine_id").textValue(),new GameGeneration(binding.get("game_pid").bigIntegerValue().longValueExact(),new PythonOnlyUInt64(new BigInteger(binding.get("game_birth_filetime").textValue()))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(binding.get("played_character_id").bigIntegerValue(),binding.get("native_revision").bigIntegerValue(),binding.get("date_raw").bigIntegerValue()),binding.get("snapshot_id").textValue(),new BigInteger(binding.get("public_revision").textValue()),binding.get("episode_run_id").textValue()),1);
        assertTrue(root.get("producer_sources").isArray()&&root.get("producer_sources").size()>=4,"native policy/body/model/Confirm complete source refs required");
        for(var node:root.get("producer_sources")){ExactRef ref=ExactRef.fromJson(node);var source=SharedSourceFiles.observe(Path.of(ref.path()));assertEquals(ref.bytes(),source.source().bytes());assertEquals(ref.sha256(),source.source().sha256());SharedSourceFiles.assertUnchanged(source);}
        SharedSourceFiles.assertUnchanged(pin);return new Capture(root,before,new BigInteger(binding.get("connection_generation").textValue()));
    }
    @Test void actualOptionsSelectConfirmAndIndependentLaterOriginalsRoundTripAcrossAllNativeDecoders()throws Exception {
        Capture c=actual();var first=AubOperations.options(token(c,"options_before"),c.before(),c.generation());
        PolicyKey expected=first.policy().selected().orElseThrow();PolicyKey desired=PolicyKey.parse(c.root().get("desired_key").textValue());Select select=new Select(expected,desired);
        assertTrue(AubOperations.nativeMutation(token(c,"select"),select,c.before(),c.generation()).nativeVerified());
        var after=AubOperations.options(token(c,"options_after"),c.before(),c.generation());assertEquals(AubOperations.expected(select),AubOperations.actual(select,Optional.of(after.policy()),Optional.empty()));
        Confirm confirm=new Confirm(desired);assertTrue(AubOperations.nativeMutation(token(c,"confirm"),confirm,c.before(),c.generation()).nativeVerified());
        var business=AubBusinessStateRead.decodeMaterial(token(c,"business_after"),c.before(),c.generation());assertEquals(AubOperations.expected(confirm),AubOperations.actual(confirm,Optional.empty(),Optional.of(business)));
        assertEquals(after.policy(),AubOperations.options(new RawJson(NativeWire.parse(token(c,"options_after").bytes()).toString().getBytes(StandardCharsets.UTF_8)),c.before(),c.generation()).policy());
        assertFalse(NativeWire.parse(AubOperations.publicOptions(after).bytes()).get("full_product_acceptance_credit").booleanValue());
        assertEquals(NativeWire.UINT64_MAX,c.generation(),"required successor15 native serializer fixture must emit full uint64");
        assertEquals(NativeWire.UINT64_MAX.subtract(BigInteger.ONE),c.before().frame().identity().nativeRevision());
        assertEquals(NativeWire.UINT64_MAX,c.before().frame().revision());
        var selected=AubPublicCodec.select(select,token(c,"select"),c.before(),c.generation(),after,"actual-select-request","actual-select-claim");
        var confirmed=AubPublicCodec.confirm(confirm,token(c,"confirm"),c.before(),c.generation(),business,"actual-confirm-request","actual-confirm-claim");
        var outputs=List.of(new Projection(AubPublicCodec.Operation.BUSINESS,AubBusinessStateRead.normalizedForPublic(business)),
                new Projection(AubPublicCodec.Operation.OPTIONS,AubOperations.publicOptions(after)),
                new Projection(AubPublicCodec.Operation.SELECT,selected),new Projection(AubPublicCodec.Operation.CONFIRM,confirmed));
        for(var output:outputs) {
            var original=NativeWire.parse(output.value().bytes());
            assertEquals(NativeWire.UINT64_MAX.toString(),original.get("queried_revision").textValue());
            assertEquals(original,NativeWire.parse(AubPublicCodec.readPublic(output.operation(),output.value()).bytes()));
            assertFalse(original.get("full_product_acceptance_credit").booleanValue());
        }
        var selectedJson=NativeWire.parse(selected.bytes());
        assertDecimal(selectedJson,"native_revision",c.before().frame().identity().nativeRevision());
        for(String model:List.of("before_actual_model","after_actual_model"))assertDecimal(selectedJson.get(model),"connection_generation",c.generation());
        assertDecimal(selectedJson.get("native_ack").get("after_actual_model"),"native_revision",c.before().frame().identity().nativeRevision());
        assertDecimal(selectedJson.get("later_actual_observation"),"queried_revision",c.before().frame().revision());
        var confirmedJson=NativeWire.parse(confirmed.bytes());
        for(String state:List.of("state_before","state_after")) {
            assertDecimal(confirmedJson.get(state),"connection_generation",c.generation());
            assertDecimal(confirmedJson.get("native_ack").get(state),"native_revision",c.before().frame().identity().nativeRevision());
        }
        assertDecimal(confirmedJson.get("before_actual_model"),"native_revision",c.before().frame().identity().nativeRevision());
        assertDecimal(confirmedJson.get("later_actual_observation"),"connection_generation",c.generation());
        assertTrue(NativeWire.parse(token(c,"select").bytes()).get("connection_generation").isIntegralNumber());
        assertTrue(NativeWire.parse(token(c,"confirm").bytes()).get("state_after").get("native_revision").isIntegralNumber());
    }
    @Test void actualNativeProducerPublicBoundaryRejectsWrongNestedDecimalRolesAndKeepsBusinessIdsBounded()throws Exception {
        Capture c=actual();var options=AubOperations.options(token(c,"options_after"),c.before(),c.generation());
        ObjectNode original=NativeWire.object(NativeWire.parse(token(c,"select").bytes()));
        Select mutation=new Select(PolicyKey.parse(original.get("expected_selected_key").textValue()),PolicyKey.parse(original.get("desired_key").textValue()));
        RawJson selected=AubPublicCodec.select(mutation,token(c,"select"),c.before(),c.generation(),options,"real-request","real-claim");
        ObjectNode publicRow=NativeWire.object(NativeWire.parse(selected.bytes()));
        for(String invalid:List.of("01","+1","1.0","18446744073709551616")) {
            ObjectNode wrong=publicRow.deepCopy();((ObjectNode)wrong.get("native_ack").get("before_actual_model")).put("connection_generation",invalid);
            assertThrows(IllegalArgumentException.class,()->AubPublicCodec.readPublic(AubPublicCodec.Operation.SELECT,raw(wrong)));
        }
        ObjectNode numeric=publicRow.deepCopy();((ObjectNode)numeric.get("native_ack")).put("native_revision",NativeWire.UINT64_MAX);
        assertThrows(IllegalArgumentException.class,()->AubPublicCodec.readPublic(AubPublicCodec.Operation.SELECT,raw(numeric)));
        ObjectNode absent=publicRow.deepCopy();((ObjectNode)absent.get("later_actual_observation")).remove("connection_generation");
        assertThrows(IllegalArgumentException.class,()->AubPublicCodec.readPublic(AubPublicCodec.Operation.SELECT,raw(absent)));
        ObjectNode widened=publicRow.deepCopy();widened.put("played_character_id",new BigInteger("2147483648"));
        assertThrows(IOException.class,()->AubPublicCodec.readPublic(AubPublicCodec.Operation.SELECT,raw(widened)));
        ObjectNode invented=publicRow.deepCopy();invented.put("unregistered_native_revision",NativeWire.UINT64_MAX);
        assertThrows(IllegalArgumentException.class,()->AubPublicCodec.readPublic(AubPublicCodec.Operation.SELECT,raw(invented)),"unknown same-named role must not receive automatic decimal conversion");
        ObjectNode textProof=publicRow.deepCopy();((ObjectNode)textProof.get("after_actual_model")).put("owner_thread_verified","true");
        assertThrows(IllegalArgumentException.class,()->AubPublicCodec.readPublic(AubPublicCodec.Operation.SELECT,raw(textProof)));
        ObjectNode policyType=publicRow.deepCopy();((ObjectNode)policyType.get("before_policy")).put("ready","true");
        assertThrows(IllegalArgumentException.class,()->AubPublicCodec.readPublic(AubPublicCodec.Operation.SELECT,raw(policyType)));
        ObjectNode policyKey=publicRow.deepCopy();((ObjectNode)policyKey.get("after_policy")).put("selected_key",true);
        assertThrows(IllegalArgumentException.class,()->AubPublicCodec.readPublic(AubPublicCodec.Operation.SELECT,raw(policyKey)));
        ObjectNode failed=publicRow.deepCopy();((ObjectNode)failed.get("after_actual_model")).putObject("completion_diagnostics");
        assertThrows(IllegalArgumentException.class,()->AubPublicCodec.readPublic(AubPublicCodec.Operation.SELECT,raw(failed)),"failure-only diagnostic fields cannot qualify a successful .3 model");
        var business=AubBusinessStateRead.decodeMaterial(token(c,"business_after"),c.before(),c.generation());
        ObjectNode businessText=NativeWire.object(NativeWire.parse(AubPublicCodec.business(business).bytes()));businessText.put("detail_effectively_visible","false");
        assertThrows(IllegalArgumentException.class,()->AubPublicCodec.readPublic(AubPublicCodec.Operation.BUSINESS,raw(businessText)));
        ObjectNode flagText=NativeWire.object(NativeWire.parse(AubPublicCodec.business(business).bytes()));((ObjectNode)flagText.withArray("flags").get(0)).put("present","true");
        assertThrows(IllegalArgumentException.class,()->AubPublicCodec.readPublic(AubPublicCodec.Operation.BUSINESS,raw(flagText)));
        assertTrue(publicRow.get("game_pid").isIntegralNumber());assertTrue(publicRow.get("date_raw").isIntegralNumber());
        assertTrue(publicRow.get("after_actual_model").get("detail_actor_reference_key").isIntegralNumber());
    }
    private record Projection(AubPublicCodec.Operation operation,RawJson value) { }
    private static void assertDecimal(com.fasterxml.jackson.databind.JsonNode row,String key,BigInteger expected) {
        assertTrue(row.get(key).isTextual(),key);assertEquals(expected.toString(),row.get(key).textValue());
    }
    @Test void actualProducerMutationsCannotTurnFaultOrMissingCensusOrWrongNumericTypesIntoSuccess()throws Exception {
        Capture c=actual();ObjectNode original=NativeWire.object(NativeWire.parse(token(c,"select").bytes()));
        Select mutation=new Select(PolicyKey.parse(original.get("expected_selected_key").textValue()),PolicyKey.parse(original.get("desired_key").textValue()));
        for(String key:new String[]{"native_revision","connection_generation","game_pid","played_character_id","date_raw"}) {
            ObjectNode wrong=original.deepCopy();wrong.put(key,true);assertThrows(IOException.class,()->AubOperations.nativeMutation(raw(wrong),mutation,c.before(),c.generation()));
            ObjectNode missing=original.deepCopy();missing.remove(key);assertThrows(IOException.class,()->AubOperations.nativeMutation(raw(missing),mutation,c.before(),c.generation()));
        }
        ObjectNode unknown=original.deepCopy();unknown.put("postcondition_verified",false);unknown.put("verification_pending",true);assertThrows(IllegalArgumentException.class,()->AubOperations.nativeMutation(raw(unknown),mutation,c.before(),c.generation()));
        ObjectNode noDetail=original.deepCopy();((ObjectNode)noDetail.get("after_actual_model")).put("detail_actor_binding_verified",false);assertThrows(IllegalArgumentException.class,()->AubOperations.nativeMutation(raw(noDetail),mutation,c.before(),c.generation()));
        ObjectNode wrongBuild=original.deepCopy();wrongBuild.put("game_version","1.20.0.4");assertThrows(IllegalArgumentException.class,()->AubOperations.nativeMutation(raw(wrongBuild),mutation,c.before(),c.generation()));
        // Original Confirm permits pending same-call verification, followed by a genuinely independent successful census.
        ObjectNode confirm=NativeWire.object(NativeWire.parse(token(c,"confirm").bytes()));confirm.set("state_after",confirm.get("state_before").deepCopy());confirm.put("postcondition_verified",false);confirm.put("verification_pending",true);
        Confirm intent=new Confirm(PolicyKey.parse(confirm.get("selected_key").textValue()));assertFalse(AubOperations.nativeMutation(raw(confirm),intent,c.before(),c.generation()).nativeVerified());
        var later=AubBusinessStateRead.decodeMaterial(token(c,"business_after"),c.before(),c.generation());assertEquals(AubOperations.expected(intent),AubOperations.actual(intent,Optional.empty(),Optional.of(later)));
    }
    private static RawJson token(Capture capture,String name){var node=capture.root().get(name);assertNotNull(node,"actual producer original missing: "+name);return new RawJson(node.toString().getBytes(StandardCharsets.UTF_8));}
    private static RawJson raw(ObjectNode row){return new RawJson(row.toString().getBytes(StandardCharsets.UTF_8));}
}
