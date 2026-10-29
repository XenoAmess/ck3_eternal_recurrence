package org.xar.ck3.control.wave2.runtime.closedadoption;
import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
final class RootNativeMapMaterializerTest {
 @TempDir Path temporary;
 private static ExactRef ref(Path path) throws IOException { FileRef r=FileRef.measure(path); return new ExactRef(r.path(),r.bytes(),r.sha256()); }
 private record Fixture(RootNativeMapMaterializer writer, OriginalColdConsumerSession.ComposedBundle bundle,
                        Path runtime, Path quote, Path source, AtomicInteger guards) {}
 private Fixture fixture(String mode,boolean omit) throws IOException {
  Path source=Files.write(temporary.resolve("source"),"immutable".getBytes(StandardCharsets.UTF_8));
  ExactRef pin=ref(source); Path runtime=temporary.resolve("runtime"), quote=temporary.resolve("quote.json");
  Instant deadline=Instant.now().plusSeconds(90); String machine=WindowsJobProcess.currentMachineId();
  ObjectNode plan=StrictJson.object(); plan.put("machine_id",machine);plan.put("runtime_root",runtime.toString());
  plan.put("review_at_utc",deadline.toString());for(String f:List.of("basis_ref","validation_ref","producer_ref"))plan.set(f,pin.toJson());
  Path planPath=Files.write(temporary.resolve("plan.json"),StrictJson.canonical(plan));ExactRef planRef=ref(planPath);
  ObjectNode q=StrictJson.object();q.put("schema","xar.current-saved-cold-quote/v5");q.put("machine_id",machine);
  q.put("observed_at_utc",Instant.now().toString());q.set("plan_ref",planRef.toJson());
  for(String f:List.of("basis_ref","validation_ref","producer_ref"))q.set(f,pin.toJson());
  q.put("runtime_root",runtime.toString());q.put("canonical_entry_limit",8);q.put("ordinary_cycle_credit",0);
  q.put("game_day_credit",0);q.put("original_actions_replayed",false);
  q.putArray("canonical_entry_paths");q.putArray("closure_entry_paths");q.putArray("import_roots");
  q.put("logical_bytes",pin.bytes());q.put("allocation_upper","hardlink".equals(mode)?0:4096);
  q.put("prepare_peak_upper",135177);q.putNull("native32_current_sdk_override");q.putNull("renderer_override_ref");
  q.put("artifact_cap_bytes",134217728);ObjectNode junction=StrictJson.object();junction.put("path",runtime.resolve("campaign-score").toString());
  Path target=Files.createDirectory(temporary.resolve("score-target"));
  ExactRef anchor=ref(Files.writeString(target.resolve("CAMPAIGN-ANCHOR.json"),"{\"synthetic_source_only\":true}"));
  junction.put("exact_target",target.toString());junction.put("must_verify_same_FileID",true);
  junction.put("target_file_id","18446744073709551615");junction.put("target_device","0");junction.set("anchor_ref",anchor.toJson());
  q.set("campaign_score_junction",junction);ObjectNode row=StrictJson.object();row.put("path",runtime.resolve("module.py").toString());
  row.put("relative_path","module.py");row.put("bytes",pin.bytes());row.put("sha256",pin.sha256());row.put("mode",mode);
  if("hardlink".equals(mode))row.set("source_ref",pin.toJson());else row.putNull("source_ref");q.putArray("files").add(row);
  AtomicInteger guards=new AtomicInteger();var permit=new RootNativeMapMaterializer.Permit(machine,planRef,runtime,quote,List.of(),deadline,2_097_152,pin);
  RootColdResumeSession.Workflow continuation=session->{throw new IOException("no Native workflow in file-materialization tests");};
  var writer=new RootNativeMapMaterializer(permit,continuation,guards::incrementAndGet);
  var files=omit?List.<OriginalColdConsumerSession.ComposedFile>of(new OriginalColdConsumerSession.ComposedFile(temporary.resolve("wrong").toString(),Files.readAllBytes(source)))
   :List.of(new OriginalColdConsumerSession.ComposedFile(runtime.resolve("module.py").toString(),Files.readAllBytes(source)));
  return new Fixture(writer,new OriginalColdConsumerSession.ComposedBundle(planRef,StrictJson.canonical(q),files),runtime,quote,source,guards);
 }
 @Test void exactCreateOnlyFilesAndQuoteAreActuallyWrittenWithoutPreparedOrJunction() throws Exception {
  Fixture f=fixture("create-only",false);var scope=f.writer().materialize(f.bundle());ExactRef result=scope.quoteRef();
  assertEquals(ref(f.quote()),result);assertArrayEquals(Files.readAllBytes(f.source()),Files.readAllBytes(f.runtime().resolve("module.py")));
  assertFalse(Files.exists(f.runtime().resolve("campaign-score")));assertTrue(f.guards().get()>=3);
 }
 @Test void issuedScopeCannotCrossTheMaterializingRootThread() throws Exception {
  Fixture f=fixture("create-only",false);var scope=f.writer().materialize(f.bundle());
  try(var executor=java.util.concurrent.Executors.newSingleThreadExecutor()) {
   var pending=executor.submit(scope::quoteRef);
   var failure=assertThrows(java.util.concurrent.ExecutionException.class,()->pending.get(5,java.util.concurrent.TimeUnit.SECONDS));
   assertInstanceOf(org.xar.ck3.control.contracts.ContractViolationException.class,failure.getCause());
  }
  assertFalse(Files.exists(f.runtime().resolve("campaign-score")));
 }
 @Test void issuedScopeRejectsChangedActualQuoteBytes() throws Exception {
  Fixture f=fixture("create-only",false);var scope=f.writer().materialize(f.bundle());
  Files.writeString(f.quote(),"{}");
  assertThrows(IOException.class,scope::quoteRef);assertFalse(Files.exists(f.runtime().resolve("campaign-score")));
 }
 @Test void malformedJunctionWireFailsBeforeFileMaterialization() throws Exception {
  Fixture f=fixture("create-only",false);
  ObjectNode quote=(ObjectNode)StrictJson.parse(f.bundle().quote(),1_048_576);
  ((ObjectNode)quote.get("campaign_score_junction")).put("must_verify_same_FileID",1);
  var bad=new OriginalColdConsumerSession.ComposedBundle(f.bundle().plan(),StrictJson.canonical(quote),f.bundle().files());
  assertThrows(org.xar.ck3.control.contracts.ContractViolationException.class,()->f.writer().materialize(bad));
  assertFalse(Files.exists(f.runtime()));assertFalse(Files.exists(f.quote()));
 }
 @Test void quotedHardlinkPreservesActualNativeFileIdentity() throws Exception {
  Fixture f=fixture("hardlink",false);f.writer().materialize(f.bundle());assertTrue(Files.isSameFile(f.source(),f.runtime().resolve("module.py")));
 }
 @Test void incompleteBundleIsRejectedBeforeAnyOutputDirectoryExists() throws Exception {
  Fixture f=fixture("create-only",true);assertThrows(IOException.class,()->f.writer().materialize(f.bundle()));
  assertFalse(Files.exists(f.runtime()));assertFalse(Files.exists(f.quote()));
 }
 @Test void existingOutputAndASecondAttemptAreBothRejected() throws Exception {
  Fixture f=fixture("create-only",false);Files.createDirectory(f.runtime());
  assertThrows(IOException.class,()->f.writer().materialize(f.bundle()));
  assertThrows(IOException.class,()->f.writer().materialize(f.bundle()));assertFalse(Files.exists(f.quote()));
 }
}

