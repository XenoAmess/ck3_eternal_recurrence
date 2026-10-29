package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Clock;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.checkpoint.CheckpointPair.FileWitness;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityWriter;
import org.xar.ck3.control.continuity.writer.StorageWriteGuardTestSupport;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.runtime.savedproof.WindowsSavedProofIdentityReader;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;

/** Real raw producer/physical reader/consumer boundaries. Fixture ledger setup grants no live Game qualification. */
final class RootColdCheckpointValidatorTest {
    @TempDir Path temporary;
    private static final String PIPE="\\\\.\\pipe\\cold-fixture",SHA="a".repeat(64);
    private static final IntegerValue ONE=number(1),DATE=number(-1234),CHARACTER=new IntegerValue(new BigInteger("9007199254740993"));

    @Test void fullRawDriverRoundTripPreservesUnknownTailFloatsExtensionsAndNormalizesOnlyTheAnchor() {
        Obj payload=payload().with("opaque_original",new Text("x".repeat(2<<20))).with("native_fraction",new DecimalValue("1.25"));
        byte[] packet=DriverJson.encode(payload);assertTrue(packet.length>1<<20);
        Obj decoded=DriverJson.object(packet,RootColdCheckpointValidator.MAXIMUM_DRIVER_BYTES);assertEquals(payload,decoded);
        Obj anchor=normalize(decoded);assertEquals(new Text("xar_checkpoint.ck3"),anchor.get("name"));
        assertEquals(new Text("xar_checkpoint"),anchor.get("load_save_name"));assertEquals(DATE,anchor.get("saved_date_raw"));
        assertEquals(Nil.INSTANCE,anchor.get("succession_lifecycle"));assertEquals(2,((Arr)decoded.get("command_history")).items().size());
        assertEquals("unknown-original-result",((Text)((Obj)((Arr)decoded.get("command_history")).items().get(1)).get("status")).value());
        assertEquals(payload,decoded,"the canonical validator must never truncate or rewrite complete original history");
        assertArrayEquals(DriverJson.encode(decoded),DriverJson.encode(DriverJson.object(DriverJson.encode(decoded),RootColdCheckpointValidator.MAXIMUM_DRIVER_BYTES)));
    }
    @Test void originalIntegerBooleanPipeAndHistoryGuardsRejectWrongTypesAndWrongAnchor() {
        Obj original=payload();Obj checkpoint=(Obj)original.get("last_checkpoint");
        for(Value bad:List.of(new Bool(true),new DecimalValue("2.0"),new Text("2"),Nil.INSTANCE))assertThrows(IllegalArgumentException.class,()->normalize(original.with("format_version",bad)));
        assertThrows(IllegalArgumentException.class,()->RootColdCheckpointValidator.normalizePayload(original,"wrong-pipe",temporary,witness()));
        for(String field:List.of("size","date_raw","history_index","episode_character_id")) {
            assertThrows(IllegalArgumentException.class,()->normalize(original.with("last_checkpoint",checkpoint.with(field,new Bool(true)))));
            assertThrows(IllegalArgumentException.class,()->normalize(original.with("last_checkpoint",checkpoint.with(field,new DecimalValue("1.0")))));
        }
        assertThrows(IllegalArgumentException.class,()->normalize(original.with("last_checkpoint",checkpoint.with("history_index",number(3)))));
        assertThrows(IllegalArgumentException.class,()->normalize(original.with("last_checkpoint",checkpoint.with("episode_run_id",new Text("other")))));
        assertThrows(IllegalArgumentException.class,()->normalize(original.with("last_checkpoint",checkpoint.with("sha256",new Text(SHA.toUpperCase(java.util.Locale.ROOT))))));
        Arr history=(Arr)original.get("command_history");Obj row=(Obj)history.items().getFirst();
        for(Value ok:List.of(new IntegerValue(BigInteger.ONE),new Text("true"),Nil.INSTANCE,new Bool(false)))assertThrows(IllegalArgumentException.class,()->normalize(original.with("command_history",new Arr(List.of(row.with("ok",ok),history.items().getLast())))));
        assertThrows(IllegalArgumentException.class,()->normalize(original.with("command_history",new Arr(List.of(row.with("command",new Text("take-snapshot")))))));
        byte[] duplicate="{\"format_version\":2,\"format_version\":2}".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class,()->DriverJson.object(duplicate,RootColdCheckpointValidator.MAXIMUM_DRIVER_BYTES));
    }
    @Test void lifecycleUsesTheExistingSingleCodecAndMissingNullOrInconsistentProfilesReject() {
        Obj lifecycle=DriverJson.object(SuccessionLifecycleCodec.encode(SuccessionLifecycleBinding.legacyRogue()),SuccessionLifecycleCodec.MAX_BYTES);
        Obj bound=withLifecycle(payload(),lifecycle);assertEquals(lifecycle,normalize(bound).get("succession_lifecycle"));
        assertThrows(IllegalArgumentException.class,()->normalize(payload().with("succession_lifecycle",Nil.INSTANCE)));
        assertThrows(IllegalArgumentException.class,()->normalize(bound.with("succession_lifecycle",lifecycle.with("source",new Text("different-source")))));
        Obj ordinary=lifecycle.with("lifecycle",new Text("ordinary_campaign_succession")).with("xar_enabled",new Text("xar_off"))
                .with("pact_contract",new Text("absent_by_fresh_campaign_xar_off_contract"));
        assertThrows(IllegalArgumentException.class,()->normalize(withLifecycle(payload(),ordinary)));
        Obj unknown=DriverJson.object(SuccessionLifecycleCodec.encode(SuccessionLifecycleBinding.unknown()),SuccessionLifecycleCodec.MAX_BYTES);
        assertEquals(unknown,normalize(withLifecycle(payload(),unknown)).get("succession_lifecycle")); // preserved UNKNOWN is not recovery authority
    }
    @Test void realPhysicalFactoryMintsPrivateSameScopeTicketAndRechecksDigestDespiteRestoredMtime()throws Exception {
        Path profile=temporary.resolve("physical-profile");Files.createDirectories(profile.resolve("save games"));
        Path save=profile.resolve("save games").resolve(RootColdCheckpointValidator.CHECKPOINT_FILENAME);Files.write(save,new byte[]{1,2,3});
        ExactRef saveRef=ref(save);Obj raw=replaceSave(payload(),saveRef);raw=raw.with("large_complete_payload",new Text("x".repeat(2<<20)));
        Path driver=temporary.resolve("physical-driver.json");Files.write(driver,DriverJson.encode(raw));ExactRef driverRef=ref(driver);
        var nativeIdentities=new WindowsSavedProofIdentityReader();FileStatIdentity driverId=nativeIdentities.stat(driver),saveId=nativeIdentities.stat(save);
        Obj normalized=RootColdCheckpointValidator.normalizePayload(raw,PIPE,profile,new FileWitness(saveRef,saveId));
        var expected=new RootColdCheckpointValidator.Expected(driverRef,driverId,saveRef,saveId,PIPE,profile,(Obj)raw.get("last_checkpoint"),normalized,2);
        ContinuityWriter writer=writer(temporary.resolve("ledger"),driverRef);RootColdCheckpointValidator actual=new RootColdCheckpointValidator(writer);
        AtomicReference<RootColdCheckpointValidator.Verified> escaped=new AtomicReference<>();Obj complete=raw;
        writer.locked(same->{
            var ticket=actual.verifyLegacy(same,expected);escaped.set(ticket);assertEquals(complete,ticket.driverPayload());assertEquals(normalized,ticket.normalizedAnchor());
            assertEquals(driverId,ticket.driverWitness().identity());assertEquals(saveId,ticket.saveWitness().identity());
            byte[] callerCopy=ticket.driverBytes();callerCopy[0]='!';assertArrayEquals(Files.readAllBytes(driver),ticket.driverBytes());
            actual.requireCurrentLegacy(same,ticket);assertEquals(0,same.head().state().sequence());
            var oldTime=Files.getLastModifiedTime(save);Files.write(save,new byte[]{7,8,9});Files.setLastModifiedTime(save,oldTime);
            assertThrows(IOException.class,()->actual.requireCurrentLegacy(same,ticket));return null;
        });
        writer.locked(same->{assertThrows(IOException.class,()->actual.requireCurrentLegacy(same,escaped.get()));return null;});
    }
    @Test void sameBytesRecreatedSaveHasDifferentFileIdAndCannotReusePrivateTicket()throws Exception {
        var physical=physical("replacement");var actual=new RootColdCheckpointValidator(physical.writer());
        physical.writer().locked(same->{
            var ticket=actual.verify(same,physical.expected());
            Path original=Path.of(physical.expected().saveRef().path()),retained=original.resolveSibling("old-save-retained.ck3");
            var oldTime=Files.getLastModifiedTime(original);Files.move(original,retained);Files.write(original,Files.readAllBytes(retained));Files.setLastModifiedTime(original,oldTime);
            assertNotEquals(new WindowsSavedProofIdentityReader().stat(original).fileId(),ticket.saveWitness().identity().fileId());
            assertThrows(IOException.class,()->actual.requireCurrentLegacy(same,ticket));assertEquals(0,same.head().state().sequence());return null;
        });
    }
    @Test void physicalInputMissingSourceAndForeignWriterScopeRejectWithoutGrantingTicket()throws Exception {
        var first=physical("foreign-first");var second=physical("foreign-second");var actual=new RootColdCheckpointValidator(first.writer());
        second.writer().locked(same->{assertThrows(IOException.class,()->actual.verify(same,first.expected()));return null;});
        Files.delete(Path.of(first.expected().saveRef().path()));
        first.writer().locked(same->{assertThrows(IOException.class,()->actual.verify(same,first.expected()));assertEquals(0,same.head().state().sequence());return null;});
    }
    @Test void explicitP37MaterialConsumerRechecksWholePhysicalPairAndRetainsItsBranch()throws Exception {
        var input=physical("consumer");var consumer=new RootSavedCheckpointMaterials(input.writer());
        input.writer().locked(same->{
            var verified=consumer.verify(same,new RootSavedCheckpointMaterials.OriginalP37(input.expected()));
            assertEquals(RootSavedCheckpointMaterials.Branch.ORIGINAL_P37,verified.branch());
            assertThrows(IOException.class,verified::requireJavaSavedMaterial);assertThrows(IOException.class,verified::requireFirstJavaSavedMaterial);
            consumer.requireCurrent(same,verified);
            byte[] bytes=Files.readAllBytes(Path.of(input.expected().driverRef().path()));bytes[bytes.length-1]='!';Files.write(Path.of(input.expected().driverRef().path()),bytes);
            assertThrows(IOException.class,()->consumer.requireCurrent(same,verified));return null;
        });
    }
    private record Physical(ContinuityWriter writer,RootColdCheckpointValidator.Expected expected){ }
    private Physical physical(String name)throws IOException {
        Path directory=temporary.resolve(name);Files.createDirectory(directory);Path profile=directory.resolve("profile");Files.createDirectories(profile.resolve("save games"));
        Path save=profile.resolve("save games/xar_checkpoint.ck3");Files.write(save,new byte[]{1,2,3});ExactRef saveRef=ref(save);
        Obj raw=replaceSave(payload(),saveRef);Path driver=directory.resolve("driver.json");Files.write(driver,DriverJson.encode(raw));
        var reader=new WindowsSavedProofIdentityReader();ExactRef driverRef=ref(driver);var driverId=reader.stat(driver);var saveId=reader.stat(save);
        Obj anchor=RootColdCheckpointValidator.normalizePayload(raw,PIPE,profile,new FileWitness(saveRef,saveId));
        var expected=new RootColdCheckpointValidator.Expected(driverRef,driverId,saveRef,saveId,PIPE,profile,(Obj)raw.get("last_checkpoint"),anchor,2);
        return new Physical(writer(directory.resolve("ledger"),driverRef),expected);
    }
    private Obj normalize(Obj raw){return RootColdCheckpointValidator.normalizeLegacyPayload(raw,PIPE,temporary,witness());}
    private FileWitness witness(){return new FileWitness(new ExactRef(temporary.resolve("save games").resolve("xar_checkpoint.ck3").toString(),3,SHA),new FileStatIdentity(BigInteger.valueOf(3),"9007199254740993","1700000000000000100"));}
    @org.junit.jupiter.api.Test void physicalCheckpointAnchorCannotBypassTheCompleteCanonicalResumeConsumer() {
        Obj raw=payload();
        for(Obj malformed:java.util.List.of(raw.with("bridge_pid",new Bool(true)),raw.with("succession_expectation",new Obj(java.util.Map.of())),
                raw.with("campaign_goal",new Obj(java.util.Map.of()))))
            assertThrows(IllegalArgumentException.class,()->normalize(malformed));
    }
    private static Obj payload() {
        Obj saved=new Obj(Map.of("size",number(3),"sha256",new Text(SHA),"date_raw",DATE));
        Obj checkpoint=new Obj(Map.of("name",new Text("xar_checkpoint.ck3"),"size",number(3),"sha256",new Text(SHA),"date_raw",DATE,"history_index",ONE,"episode_character_id",CHARACTER,"episode_run_id",new Text("original-run")));
        Obj row=new Obj(Map.of("index",ONE,"command",new Text("save-checkpoint"),"ok",new Bool(true),"result",new Obj(Map.of("checkpoint",saved))));
        Obj tail=new Obj(Map.of("index",number(2),"command",new Text("unknown-original"),"ok",new Bool(false),"status",new Text("unknown-original-result"),"result",Nil.INSTANCE));
        return new Obj(Map.of("format_version",number(2),"pipe_name",new Text(PIPE),"bridge_pid",number(42),"episode_character_id",CHARACTER,"episode_run_id",new Text("original-run"),"last_checkpoint",checkpoint,"command_history",new Arr(List.of(row,tail))));
    }
    private static Obj withLifecycle(Obj raw,Obj lifecycle) {
        Obj checkpoint=((Obj)raw.get("last_checkpoint")).with("succession_lifecycle",lifecycle);Arr history=(Arr)raw.get("command_history");Obj row=(Obj)history.items().getFirst(),result=(Obj)row.get("result"),saved=(Obj)result.get("checkpoint");
        return raw.with("succession_lifecycle",lifecycle).with("last_checkpoint",checkpoint).with("command_history",new Arr(List.of(row.with("result",result.with("checkpoint",saved.with("succession_lifecycle",lifecycle))),history.items().getLast())));
    }
    private static Obj replaceSave(Obj raw,ExactRef actual) {
        Obj checkpoint=((Obj)raw.get("last_checkpoint")).with("size",number(actual.bytes())).with("sha256",new Text(actual.sha256()));
        Arr rows=(Arr)raw.get("command_history");Obj row=(Obj)rows.items().getFirst(),result=(Obj)row.get("result"),saved=((Obj)result.get("checkpoint")).with("size",number(actual.bytes())).with("sha256",new Text(actual.sha256()));
        return raw.with("last_checkpoint",checkpoint).with("command_history",new Arr(List.of(row.with("result",result.with("checkpoint",saved)),rows.items().getLast())));
    }
    private static IntegerValue number(long value){return new IntegerValue(BigInteger.valueOf(value));}
    private static ExactRef ref(Path path)throws IOException {byte[] bytes=Files.readAllBytes(path);return new ExactRef(path.toString(),bytes.length,DriverJson.sha256(bytes));}
    private static ContinuityWriter writer(Path root,ExactRef originalDriver)throws IOException {
        Files.createDirectory(root);Path source=root.resolve("source.java");Files.writeString(source,"finite cold validator fixture producer");
        var seed=StrictJson.object();seed.put("schema","root.ck3.continuity-window/v1");seed.put("machine_id","cold-validator-fixture");seed.put("sequence",0);seed.put("window_id",1);seed.put("status","running");
        seed.put("target_days",10958);seed.put("target_years",30);seed.put("calendar_year_days",365.25);seed.put("start_date_raw",1000);seed.put("target_date_raw",263992);seed.put("last_settled_date_raw",1000);
        seed.put("last_settled_cycles",0);seed.put("manual_repair_count",0);seed.put("automatic_recovery_count",0);seed.put("binding_lineage_count",0);seed.putObject("game_binding").put("pid",42).put("creation_date","2026-10-24T00:00:00Z");
        seed.putNull("latest_binding");seed.putNull("pending_cycle");seed.put("NEXT",1);seed.set("java_driver_history_baseline",originalDriver.toJson());
        byte[] bytes=ContinuityJson.canonical(seed);Path snapshot=root.resolve("ROOT-CONTINUITY-WINDOW.json"),anchor=root.resolve("anchor.json");Files.write(snapshot,bytes);Files.write(anchor,bytes);
        Files.write(root.resolve("ROOT-CONTINUITY-WINDOW.lock"),new byte[0]);Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));
        var layout=new Layout(snapshot,ref(anchor),"cold-validator-fixture");
        var storage=StorageWriteGuardTestSupport.create(layout);
        return new ContinuityWriter(layout,List.of(ref(source)),new TransitionAuthority(){
            @Override public String revalidate(ContinuityState old,Request request){throw new AssertionError("physical validation cannot commit");}
            @Override public ContinuityState reduce(ContinuityState old,Request request){throw new AssertionError("physical validation cannot reduce");}
        },Clock.systemUTC(),storage);
    }
}
