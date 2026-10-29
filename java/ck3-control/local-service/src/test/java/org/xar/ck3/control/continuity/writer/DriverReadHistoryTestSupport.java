package org.xar.ck3.control.continuity.writer;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.history.DriverReadHistoryRowProducer;
import org.xar.ck3.control.application.history.DriverSurvivingHistory;
import org.xar.ck3.control.application.planning.military.MilitaryReadObservation;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.nativebridge.capabilities.army.ArmyBattleReadValue;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Shared actual archive/writer/receipt fixture. The decoder is explicit test data and supplies no Game qualification. */
public final class DriverReadHistoryTestSupport {
    private DriverReadHistoryTestSupport() { }
    public static final String MACHINE="xenoamess-full-tower-eb9d2c1186",STEP="preview-move-army-0-to-4",CAP="game.command.preview-move-army-N-to-N";
    public record Fixture(NativeOutcomeArchive archive,ReadContract<MilitaryReadObservation> contract,RootReadContractCatalog catalog,
            PlanningReadResult.Known<MilitaryReadObservation> known,AtomicInteger decodes,AtomicInteger replays) { }

    public static Fixture create(Path temporary,boolean pure) throws Exception {
        return create(archive(Files.createTempDirectory(temporary,"read-writer-")),pure);
    }
    /** Supplies typed read data on an existing actual writer; its application bootstrap and reducer remain caller-owned. */
    public static Fixture create(NativeOutcomeArchive archive,boolean pure) {
        var source=archive.preserveMaterial(new RawJson("{\"fixture_source\":true}".getBytes(StandardCharsets.UTF_8)));
        var operation=new OperationKey(STEP);var frame=frame();var now=Instant.parse("2026-10-23T19:00:00Z");
        var g2=new G2Source(MACHINE,now.toString(),"fixture-build",source);
        var request=new PlanningReadRequest(frame,g2,"session",operation,json("{}"),now.plusSeconds(300));
        var binding=new GuardEvidence(frame,g2,"session",BigInteger.valueOf(4),operation,source,source,"fixture-authority",now,now.plusSeconds(300),List.of(source));
        var guard=new PlanningReadGuard(binding,true,true,true,"a".repeat(64));
        Obj raw=json("{\"step\":\""+STEP+"\",\"accepted\":true,\"status\":\"available\",\"route_preview\":{\"army_id\":0,\"origin_province_id\":1,\"target_province_id\":4,\"status\":\"available\",\"route_province_ids\":[1,4]}}");
        String envelope="{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"original-read\",\"ok\":true,\"result\":"+new String(OpportunityJson.encode(raw),StandardCharsets.UTF_8)+"}";
        byte[] bytes=envelope.getBytes(StandardCharsets.UTF_8),packet=ByteBuffer.allocate(bytes.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(bytes.length).put(bytes).array();
        var ack=new NativeActionPort.AckReceived("original-read",true,Optional.of(new RawJson(OpportunityJson.encode(raw))),new RawJson(bytes),packet);
        var receipt=new PlanningReadReceipt(request,"fixture-public-preview","original-read",guard,guard,ack);var decodes=new AtomicInteger();var replays=new AtomicInteger();
        java.util.function.Function<PlanningReadRequest,NativeRequest> prepare=r->new NativeRequest(STEP,Optional.of(CAP),new RawJson("{}".getBytes(StandardCharsets.UTF_8)));
        java.util.function.Function<PlanningReadReceipt,MilitaryReadObservation> decode=r->{decodes.incrementAndGet();return decodeFixture(r);};
        java.util.function.Function<PlanningReadReceipt,MilitaryReadObservation> replay=r->{replays.incrementAndGet();return decodeFixture(r);};
        ReadContract<MilitaryReadObservation> contract=pure?new ReadContract<>("fixture-public-preview",operation,Optional.of(CAP),CAP,ReadContract.PermissionMode.ADVERTISED_CAPABILITY,
                ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,source,(r,id)->prepare.apply(r),decode,replay):
                new ReadContract<>("fixture-public-preview",operation,Optional.of(CAP),CAP,ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,source,prepare,decode);
        var catalog=new RootReadContractCatalog(List.of(new RootReadContractCatalog.InstalledRead(contract,source)),List.of());
        var known=new PlanningReadResult.Known<>(decodeFixture(receipt),receipt,archive.preserveRead(receipt));return new Fixture(archive,contract,catalog,known,decodes,replays);
    }
    private static MilitaryReadObservation decodeFixture(PlanningReadReceipt receipt) {
        Obj raw=DriverJson.object(receipt.original().originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES);var frame=receipt.request().before().frame();
        Obj result=raw.with("queried_snapshot_id",new Text(frame.snapshotId())).with("queried_revision",new IntegerValue(frame.revision()))
                .with("queried_native_revision",new IntegerValue(frame.identity().nativeRevision())).with("queried_connection_generation",new IntegerValue(receipt.before().binding().connectionGeneration()))
                .with("queried_episode_run_id",new Text(frame.episodeRunId()));return new MilitaryReadObservation(MilitaryReadObservation.Kind.ROUTE_PREVIEW,result);
    }
    public static ObservationIdentity frame() {
        ObjectNode row=StrictJson.object();row.put("machine_id",MACHINE);row.set("game",new GameGeneration(7,new PythonOnlyUInt64(new BigInteger("134373229053165471"))).toJson());row.put("observation_version",1);
        var f=row.putObject("frame");f.put("played_character_id","1");f.put("native_revision","2");f.put("date_raw","1000");f.put("snapshot_id","actual-source-frame");f.put("revision","3");f.put("episode_run_id","ep");
        return ProposalLifecycleCodec.decodeObservation(row);
    }
    private static Obj json(String value){return DriverJson.object(value.getBytes(StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES);}
    public static NativeOutcomeArchive archive(Path root) throws IOException {
        Path snapshot=root.resolve("ROOT-CONTINUITY-WINDOW.json"),anchor=root.resolve("anchor.json");byte[] state=ContinuityJson.canonical(state());Files.write(snapshot,state);Files.write(anchor,state);
        Path lock=root.resolve("ROOT-CONTINUITY-WINDOW.lock");Files.createFile(lock);Files.createDirectory(root.resolve("ROOT-CONTINUITY-WINDOW-EVENTS"));Path source=root.resolve("reviewed-source.txt");Files.writeString(source,"pure read row archive regression fixture");
        Layout layout=new Layout(snapshot,LedgerFiles.read(anchor,65536).pin().reference(),MACHINE);Path artifactRoot=root.resolve("artifacts");Files.createDirectory(artifactRoot);
        var storage=StorageWriteGuardTestSupport.create(layout);var artifacts=new ImmutableArtifactStore(new ImmutableArtifactStore.Config(artifactRoot,lock,1_048_576),storage);
        var writer=new ContinuityWriter(layout,List.of(LedgerFiles.read(source,65536).pin().reference()),new TransitionAuthority(){
            @Override public String revalidate(ContinuityState predecessor,Request request){return ContinuityJson.digest(request.detailsObject());}
            @Override public ContinuityState reduce(ContinuityState predecessor,Request request){return OriginalWindowReducer.reduce(predecessor,request);}
        },Clock.systemUTC(),new ContinuityWriter.Extensions(List.of(),Optional.of(artifacts),Optional.empty()),storage);return new NativeOutcomeArchive(artifacts,writer);
    }
    private static ObjectNode state() {
        ObjectNode row=StrictJson.object();row.put("schema","root.ck3.continuity-window/v1");row.put("machine_id",MACHINE);row.put("sequence",0);row.put("window_id",1);row.put("status","running");row.put("target_days",10958);row.put("target_years",30);row.put("calendar_year_days",365.25);
        row.put("start_date_raw",1000);row.put("target_date_raw",1000+10958*24);row.put("last_settled_date_raw",1000);row.put("last_settled_cycles",1);row.put("manual_repair_count",1);row.put("automatic_recovery_count",0);row.put("binding_lineage_count",0);
        var game=row.putObject("game_binding");game.put("pid",123);game.put("creation_date","2026-10-23T01:00:00Z");row.putNull("latest_binding");row.putObject("pending_cycle").put("stage","auto_unsettled").put("auto_sequence",11558);row.put("NEXT",11559);return row;
    }
}
