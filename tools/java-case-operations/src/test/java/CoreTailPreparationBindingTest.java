import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.lang.reflect.Constructor;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.xar.ck3.save.SaveContracts.Pin;

/** Persistent producer/consumer codec and original Native shape regression. No dispatch/collector. */
public final class CoreTailPreparationBindingTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static int checks;
    private CoreTailPreparationBindingTest() { }
    private static void yes(boolean value) { checks++; if (!value) throw new AssertionError("binding contract"); }
    @FunctionalInterface private interface Checked { void run() throws Exception; }
    private static void reject(Checked value) throws Exception {
        checks++; try { value.run(); throw new AssertionError("wrong typed binding accepted"); }
        catch (java.io.IOException | IllegalArgumentException | NullPointerException expected) { }
    }
    private static Pin pin(Path p) throws Exception {
        byte[] b = Files.readAllBytes(p);
        return new Pin(p.toString(), b.length, java.util.HexFormat.of().formatHex(
                java.security.MessageDigest.getInstance("SHA-256").digest(b)));
    }
    private static CoreTailPreparation pure(CoreTailPreparation.Binding binding) throws Exception {
        Constructor<CoreTailPreparation> c = CoreTailPreparation.class.getDeclaredConstructor(CoreTailPreparation.Binding.class);
        c.setAccessible(true); return c.newInstance(binding);
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 3 || !args[2].matches("[A-Za-z0-9-]+")) throw new IllegalArgumentException("actual base, own, unused test leaf required");
        Path base=Path.of(args[0]), own=Path.of(args[1]).resolve(args[2]), admin=base.resolve("resume-product-a20/core-a30-administration");
        Files.createDirectory(own);
        Path runtime=base.resolve("resume-product-a20/runtime-a20/retest-source99-a01");
        JsonNode actual=JSON.readTree(Files.readAllBytes(runtime.resolve("runtime.json")));
        Path facts=admin.resolve("source99-build-admission-a01/FACTS-a04.actual.json");
        JsonNode fact=JSON.readTree(Files.readAllBytes(facts));
        var binding=new CoreTailPreparation.Binding(1,actual.path("machine_id").textValue(),
                fact.path("source_HEAD").textValue(),base,runtime,own,
                pin(admin.resolve("C35S98I200K.json")),pin(facts));
        Path produced=own.resolve("BINDING-ACTUAL-RT99-CODEC-ONLY.json");
        Files.write(produced, JSON.writerWithDefaultPrettyPrinter().writeValueAsBytes(binding),
                java.nio.file.StandardOpenOption.CREATE_NEW);
        var consumed=CoreTailPreparation.readBinding(produced);
        yes(consumed.equals(binding));
        Path round=own.resolve("BINDING-ROUNDTRIP.json");
        Files.write(round,JSON.writeValueAsBytes(consumed),java.nio.file.StandardOpenOption.CREATE_NEW);
        yes(CoreTailPreparation.readBinding(round).equals(binding));
        // Actual old authority remains Source98: it MUST NOT admit the Source99 record.
        reject(()->CoreTailPreparation.open(produced));
        ObjectNode wire=(ObjectNode)JSON.valueToTree(binding);
        for(String name:List.of("schemaVersion","machineId","sourceHead","base","runtimeRoot","ownRoot","sourceAuthority","sourceFacts")){
            ObjectNode missing=wire.deepCopy();missing.remove(name);
            Path p=own.resolve("negative-"+checks+".json");Files.write(p,JSON.writeValueAsBytes(missing));
            reject(()->CoreTailPreparation.readBinding(p));
            ObjectNode nil=wire.deepCopy();nil.putNull(name);Path np=own.resolve("negative-"+checks+".json");
            Files.write(np,JSON.writeValueAsBytes(nil));reject(()->CoreTailPreparation.readBinding(np));
        }
        for(String raw:List.of("true","1.0","\"1\"")){
            ObjectNode wrong=wire.deepCopy();wrong.set("schemaVersion",JSON.readTree(raw));
            Path p=own.resolve("negative-"+checks+".json");Files.write(p,JSON.writeValueAsBytes(wrong));
            reject(()->CoreTailPreparation.readBinding(p));
        }
        for(String name:List.of("machineId","sourceHead","base","runtimeRoot","ownRoot")){
            ObjectNode wrong=wire.deepCopy();wrong.put(name,true);
            Path p=own.resolve("negative-"+checks+".json");Files.write(p,JSON.writeValueAsBytes(wrong));
            reject(()->CoreTailPreparation.readBinding(p));
        }
        ObjectNode extra=wire.deepCopy().put("alias_source_HEAD","no");
        Path extraPath=own.resolve("negative-extra.json");Files.write(extraPath,JSON.writeValueAsBytes(extra));
        reject(()->CoreTailPreparation.readBinding(extraPath));
        Path dup=own.resolve("negative-duplicate.json");
        Files.writeString(dup,JSON.writeValueAsString(wire).replaceFirst("\\{","{\"schemaVersion\":1,"));
        reject(()->CoreTailPreparation.readBinding(dup));
        CoreTailPreparation engine=pure(binding);
        String path=admin.resolve("C35S98I200K.json").toString(),sha="0".repeat(64);
        for(long size:new long[]{0,19118,Integer.MAX_VALUE,(long)Integer.MAX_VALUE+1,Long.MAX_VALUE}){
            Pin expected=new Pin(path,size,sha);
            yes(CoreTailPreparation.capacityAuthority(JSON.valueToTree(expected)).equals(expected));
            yes(CoreTailPreparation.capacityAuthority(JSON.readTree(JSON.writeValueAsBytes(expected))).equals(expected));
        }
        for(JsonNode size:List.of(JSON.getNodeFactory().booleanNode(false),JSON.getNodeFactory().numberNode(1.0),JSON.getNodeFactory().textNode("1"))){
            ObjectNode p=JSON.createObjectNode().put("path",path).put("sha256",sha);p.set("bytes",size);
            reject(()->CoreTailPreparation.capacityAuthority(p));
        }
        // Consume original managed-run snapshot verbatim; no episode or frame is synthesized.
        Path nativeFile=base.resolve("resume-product-a20/runtime-a20/retest-f15-a01/runs/desktop-3fevhd2-1c74096080--dynastic-esotericism--R0035/operator-evidence/r35-cancel-open-a01.actual.json");
        JsonNode nativeReport=JSON.readTree(Files.readAllBytes(nativeFile)),steps=nativeReport.path("steps");
        JsonNode snapshot=steps.get(steps.size()-1).path("after_snapshot");
        var frame=engine.actualFrame(snapshot);
        yes(frame.managedRunId().equals(snapshot.path("managed_campaign_run_binding").path("run_id").textValue()));
        yes(frame.actorId()==snapshot.path("played_character").path("character_id").longValue());
        // Catalog and emitted record identity are bound to data, not old compilation constants.
        Method catalog=CoreTailPreparation.class.getDeclaredMethod("catalog");catalog.setAccessible(true);
        JsonNode first=JSON.valueToTree(catalog.invoke(engine));
        yes(first.path("source_HEAD").textValue().equals(binding.sourceHead()));
        var secondBinding=new CoreTailPreparation.Binding(1,binding.machineId(),"1".repeat(40),base,runtime,own,binding.sourceAuthority(),binding.sourceFacts());
        JsonNode second=JSON.valueToTree(catalog.invoke(pure(secondBinding)));
        yes(second.path("source_HEAD").textValue().equals("1".repeat(40)));
        System.out.println("BINDING_CONTRACT_OK checks="+checks+"; actual RT99 producer->codec and roundtrip; actual C35 mismatch rejected; real Native shape; no admission/Game/Native/Save/decoder/collector");
    }
}
