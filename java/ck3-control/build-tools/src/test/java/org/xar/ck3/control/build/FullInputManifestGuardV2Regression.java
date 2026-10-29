package org.xar.ck3.control.build;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Persistent software regression entry, also called by default CI. It never creates a Native build qualification. */
public final class FullInputManifestGuardV2Regression {
    private FullInputManifestGuardV2Regression() { }
    public record Case(String name, String outcome, FileRef terminal, FileRef originalChild) { }
    public record Actual(String schema, String machineId, String observedAtUtc, String scope, List<Case> cases) {
        public Actual { cases=List.copyOf(cases); }
    }
    private static void require(boolean condition, String message) throws IOException {
        if (!condition) throw new IOException(message);
    }
    private static FileRef write(Path path, byte[] bytes) throws IOException {
        Files.write(path, bytes, StandardOpenOption.CREATE_NEW);return FileRef.measure(path);
    }
    private static void rejected(Throwing action, String message) throws Exception {
        try { action.run(); } catch (IOException expected) { return; }
        throw new IOException(message);
    }
    @FunctionalInterface private interface Throwing { void run() throws Exception; }
    private static final class Fixture implements AutoCloseable {
        final Path base, scope, output;
        final ObjectNode request;
        final FileRef original;
        final String oldTemporary,oldJna;
        Fixture(Path parent,String name,boolean mutate)throws Exception {
            base=Files.createDirectory(parent.resolve(name));
            Path inputs=Files.createDirectory(base.resolve("inputs"));
            scope=Files.createDirectory(base.resolve("scope"));
            Path temporary=Files.createDirectory(scope.resolve("tmp"));output=Files.createDirectory(scope.resolve("guard"));
            original=write(inputs.resolve("original.txt"),"original immutable input".getBytes(java.nio.charset.StandardCharsets.UTF_8));
            var mapper=ControlBuild.strictMapper();
            FileRef javaExecutable=FileRef.measure(Path.of(System.getProperty("java.home"),"bin/java.exe"));
            List<FileRef> sources=new ArrayList<>(List.of(javaExecutable,original));
            List<String> arguments=new ArrayList<>(List.of("-Xms16m","-Xmx128m","-XX:+UseSerialGC","-XX:ActiveProcessorCount=2",
                    "-Djava.io.tmpdir="+temporary));
            if(mutate){
                byte[] body=("import java.nio.file.*; class GuardOwnedMutator { public static void main(String[] a) throws Exception {"
                        +"Files.writeString(Path.of(a[0]),\"changed by the owned negative fixture\");} }").getBytes(java.nio.charset.StandardCharsets.UTF_8);
                FileRef mutator=write(inputs.resolve("GuardOwnedMutator.java"),body);sources.add(mutator);
                arguments.add(mutator.path());arguments.add(original.path());
            }else arguments.add("-version");
            ObjectNode manifest=mapper.createObjectNode();manifest.put("schema","xar.full-input-files/v1");
            manifest.put("machine_id",WindowsJobProcess.currentMachineId());manifest.put("observed_at_utc",Instant.now().toString());
            manifest.set("files",mapper.valueToTree(sources));
            FileRef manifestRef=write(inputs.resolve("manifest.json"),mapper.writeValueAsBytes(manifest));
            var policy=write(inputs.resolve("software-only-policy.json"),"""
                    {"schema":"xar-storage-retention-policy-v1","policy_version":"1.0.0","capacity":{
                    "safety_floor_bytes":1,"safety_ceiling_bytes":1,"safety_volume_fraction":0.00000001,
                    "default_project_quota_ceiling_bytes":1000000000000,"default_project_quota_volume_fraction":0.99,
                    "quota_override_max_hours":168}}
                    """.getBytes(java.nio.charset.StandardCharsets.UTF_8));
            Instant start=Instant.now().minusSeconds(1),deadline=Instant.now().plusSeconds(90);
            var store=Files.getFileStore(scope);
            var volume=CiBootstrap.calculate(CiBootstrap.readPolicy(Files.readAllBytes(Path.of(policy.path()))),store.getTotalSpace(),store.getUsableSpace(),
                    64L<<20,0,1,65536,null,start,deadline);
            // This is owned software DATA for the policy/guard branches, never an actual issuer release or Native-ready credential.
            var capacity=new ControlBuild.CapacityRelease("xar.java-control.capacity-release/v1",WindowsJobProcess.currentMachineId(),
                    start.toString(),deadline.toString(),"RELEASED","/root/reference_main",policy,List.of(scope.toString()),temporary.toString(),
                    Map.of("artifacts",64L<<20),Map.of(scope.getRoot().toString(),volume),Map.of(),512L<<20,32L<<20);
            FileRef capacityRef=write(inputs.resolve("software-only-capacity-data.json"),mapper.writeValueAsBytes(capacity));
            var limits=new NativeBridgeRootGate.Limits("/root/reference_main",capacityRef,deadline,384L<<20,64L<<20,45);
            request=mapper.createObjectNode();request.put("schema","xar.full-input-manifest-guard-request/v2");
            request.put("machine_id",capacity.machineId());request.set("manifest_ref",mapper.valueToTree(manifestRef));
            request.put("manifest_schema","xar.full-input-files/v1");request.putArray("additional_inputs");request.put("output_root",output.toString());
            request.set("authority",RootNativePlanJson.mapper().valueToTree(limits));request.putNull("runtime_inventory_ref");
            ObjectNode allocation=request.putArray("output_scopes").addObject();allocation.put("part","artifacts");allocation.put("root",scope.toString());allocation.put("allocation_limit_bytes",64L<<20);
            ObjectNode command=request.putObject("command");command.set("executable",mapper.valueToTree(javaExecutable));command.set("arguments",mapper.valueToTree(arguments));
            command.put("cwd",scope.toString());command.putObject("environment");command.put("memory_limit_bytes",384L<<20);command.put("timeout_seconds",45);
            oldTemporary=System.getProperty("java.io.tmpdir");oldJna=System.getProperty("jna.tmpdir");
            System.setProperty("java.io.tmpdir",temporary.toString());System.setProperty("jna.tmpdir",temporary.toString());
        }
        FileRef pin()throws IOException{return write(base.resolve("request.json"),ControlBuild.strictMapper().writeValueAsBytes(request));}
        @Override public void close(){restore("java.io.tmpdir",oldTemporary);restore("jna.tmpdir",oldJna);}
        private static void restore(String key,String value){if(value==null)System.clearProperty(key);else System.setProperty(key,value);}
    }
    public static Actual run(Path newRoot)throws Exception {
        require(newRoot.isAbsolute()&&!Files.exists(newRoot),"fresh absolute software regression root required");Files.createDirectory(newRoot);
        List<Case> cases=new ArrayList<>();
        try(var f=new Fixture(newRoot,"natural",false)){
            var terminal=FullInputManifestGuard.execute(f.pin());
            require(terminal.status()==FullInputManifestGuard.State.PASS&&terminal.childStarted()&&terminal.child()!=null&&terminal.child().passed(),"actual version2 owned Java child did not pass");
            require(terminal.child().accounting().memoryLimitBytes()==384L<<20,"actual inner Job limit changed");
            require(terminal.verifiedBefore()==terminal.guardedFiles()&&terminal.verifiedAfter()==terminal.guardedFiles(),"complete source pre/post witnesses omitted");
            FileRef raw=FileRef.measure(f.output.resolve("command-result.json"));
            var original=ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(raw.path())),WindowsJobProcess.CommandResult.class);
            require(original.equals(terminal.child()),"raw actual child receipt changed during serialization");f.original.verify();
            cases.add(new Case("actual-v2-natural-child-full-prepost-and-raw-terminal","PASS",FileRef.measure(f.output.resolve("manifest-terminal.json")),raw));
        }
        try(var f=new Fixture(newRoot,"mutation",true)){
            var terminal=FullInputManifestGuard.execute(f.pin());
            require(terminal.status()==FullInputManifestGuard.State.RED&&terminal.childStarted()&&terminal.child()!=null&&terminal.child().passed(),
                    "actual source mutation must retain natural child0 while making whole guard RED");
            require(terminal.error()!=null&&terminal.verifiedAfter()<terminal.guardedFiles(),"source mutation was not caught by real postcheck");
            cases.add(new Case("actual-source-mutation-natural-child0-is-not-guard-pass","PASS",FileRef.measure(f.output.resolve("manifest-terminal.json")),FileRef.measure(f.output.resolve("command-result.json"))));
        }
        try(var f=new Fixture(newRoot,"legacy-bound",false)){
            f.request.put("schema","xar.full-input-manifest-guard-request/v1");f.request.remove(List.of("authority","output_scopes","runtime_inventory_ref"));
            ((ObjectNode)f.request.get("command")).put("memory_limit_bytes",1L<<30);
            rejected(()->FullInputManifestGuard.parse(f.request),"legacy640MiB bound was widened");
            ((ObjectNode)f.request.get("command")).put("memory_limit_bytes",192L<<20);((ObjectNode)f.request.get("command")).put("timeout_seconds",300);
            rejected(()->FullInputManifestGuard.parse(f.request),"legacy170s bound was widened");
            cases.add(new Case("legacy-memory-and-time-ceilings-retained","PASS",null,null));
        }
        try(var f=new Fixture(newRoot,"authority",false)){
            f.request.putNull("authority");rejected(()->FullInputManifestGuard.parse(f.request),"version2 accepted missing real authority");
            cases.add(new Case("version2-authority-mandatory","PASS",null,null));
        }
        try(var f=new Fixture(newRoot,"partition",false)){
            ((ObjectNode)f.request.get("output_scopes").get(0)).put("part","unadmitted");
            rejected(()->FullInputManifestGuard.execute(f.pin()),"unadmitted financial partition accepted");
            require(!Files.exists(f.output.resolve("manifest-witnesses.json.gz")),"denied capacity wrote source witnesses");
            cases.add(new Case("exact-financial-partition-refused-before-child","PASS",null,null));
        }
        try(var f=new Fixture(newRoot,"unknown",false)){
            FileRef unknown=write(f.output.resolve("INTENT-original.json"),"unknown original".getBytes(java.nio.charset.StandardCharsets.UTF_8));
            rejected(()->FullInputManifestGuard.execute(f.pin()),"existing unknown guard output replayed");unknown.verify();
            require(!Files.exists(f.output.resolve("command-result.json")),"rejected replay launched another child");
            cases.add(new Case("unknown-output-never-replayed","PASS",null,null));
        }
        Actual actual=new Actual("xar.full-input-v2-software-regression/v1",WindowsJobProcess.currentMachineId(),Instant.now().toString(),
                "OWNED_SOFTWARE_FIXTURE_DATA_NOT_FINANCIAL_RELEASE_NOT_NATIVE_BUILD_READY",cases);
        write(newRoot.resolve("regression-actual.json"),ControlBuild.strictMapper().writeValueAsBytes(actual));return actual;
    }
    private static void legacy(Fixture fixture) {
        fixture.request.put("schema","xar.full-input-manifest-guard-request/v1");
        fixture.request.remove(List.of("authority","output_scopes","runtime_inventory_ref"));
    }
    private static Actual runLegacy(Path root)throws Exception {
        Files.createDirectory(root);var cases=new ArrayList<Case>();var mapper=ControlBuild.strictMapper();
        try(var f=new Fixture(root,"alias",false)){
            legacy(f);ObjectNode alias=((ObjectNode)f.request.get("command").get("executable")).deepCopy();
            String original=alias.path("path").textValue();String upper=original.toUpperCase(java.util.Locale.ROOT);
            require(!original.equals(upper),"regression must use distinct Windows path spelling");alias.put("path",upper);
            ((com.fasterxml.jackson.databind.node.ArrayNode)f.request.get("additional_inputs")).add(alias);
            var terminal=FullInputManifestGuard.execute(f.pin());
            require(terminal.status()==FullInputManifestGuard.State.PASS&&terminal.child()!=null&&terminal.child().passed(),"original same-native-file alias failed");
            FullInputManifestGuard.Snapshot snapshot;
            try(var stream=new java.util.zip.GZIPInputStream(Files.newInputStream(Path.of(terminal.snapshotRef().path())))){
                snapshot=mapper.readValue(stream,FullInputManifestGuard.Snapshot.class);
            }
            var aliases=snapshot.witnesses().stream().filter(value->value.source().path().equalsIgnoreCase(original)).toList();
            require(aliases.size()==2&&!aliases.get(0).source().path().equals(aliases.get(1).source().path())
                    &&aliases.get(0).nativeFile().equals(aliases.get(1).nativeFile()),"both Windows spellings must retain the same actual native identity");
            cases.add(new Case("legacy-actual-case-alias-retains-both-native-witnesses","PASS",FileRef.measure(f.output.resolve("manifest-terminal.json")),null));
        }
        try(var f=new Fixture(root,"conflicting-alias",false)){
            legacy(f);ObjectNode alias=((ObjectNode)f.request.get("command").get("executable")).deepCopy();
            alias.put("path",alias.path("path").textValue().toUpperCase(java.util.Locale.ROOT));alias.put("sha256","0".repeat(64));
            ((com.fasterxml.jackson.databind.node.ArrayNode)f.request.get("additional_inputs")).add(alias);
            var terminal=FullInputManifestGuard.execute(f.pin());
            require(terminal.status()==FullInputManifestGuard.State.REJECTED&&!terminal.childStarted()&&terminal.child()==null
                    &&terminal.error().contains("conflicting duplicate input"),"conflicting alias was not rejected before child");
            cases.add(new Case("legacy-conflicting-digest-before-child","PASS",FileRef.measure(f.output.resolve("manifest-terminal.json")),null));
        }
        try(var f=new Fixture(root,"boolean",false)){
            legacy(f);Path prior=Path.of(f.request.get("manifest_ref").path("path").textValue());
            ObjectNode malformed=(ObjectNode)mapper.readTree(Files.readAllBytes(prior));
            ((ObjectNode)malformed.get("files").get(0)).put("bytes",true);
            FileRef replacement=write(f.base.resolve("boolean-manifest.json"),mapper.writeValueAsBytes(malformed));
            f.request.set("manifest_ref",mapper.valueToTree(replacement));var terminal=FullInputManifestGuard.execute(f.pin());
            require(terminal.status()==FullInputManifestGuard.State.REJECTED&&!terminal.childStarted()&&terminal.child()==null
                    &&terminal.error().contains("integer required: bytes"),"boolean file size was not rejected by actual parser");
            cases.add(new Case("legacy-boolean-bytes-before-child","PASS",FileRef.measure(f.output.resolve("manifest-terminal.json")),null));
        }
        return new Actual("xar.full-input-v2-software-regression/v1",WindowsJobProcess.currentMachineId(),Instant.now().toString(),
                "OWNED_SOFTWARE_FIXTURE_DATA_NOT_FINANCIAL_RELEASE_NOT_NATIVE_BUILD_READY",cases);
    }
    public static Actual runAll(Path root)throws Exception {
        require(root.isAbsolute()&&!Files.exists(root),"fresh absolute complete regression root required");Files.createDirectory(root);
        var cases=new ArrayList<>(run(root.resolve("version2")).cases());cases.addAll(runLegacy(root.resolve("legacy")).cases());
        Actual actual=new Actual("xar.full-input-v2-software-regression/v1",WindowsJobProcess.currentMachineId(),Instant.now().toString(),
                "OWNED_SOFTWARE_FIXTURE_DATA_NOT_FINANCIAL_RELEASE_NOT_NATIVE_BUILD_READY",cases);
        write(root.resolve("regression-all-actual.json"),ControlBuild.strictMapper().writeValueAsBytes(actual));return actual;
    }
    public static void main(String[] args)throws Exception {
        require(args.length==2&&args[1].equals(WindowsJobProcess.currentMachineId()),"fresh output root and actual machine ID required");
        System.out.println(ControlBuild.strictMapper().writeValueAsString(runAll(Path.of(args[0]))));
    }
}
