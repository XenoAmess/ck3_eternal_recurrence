package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Base64;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.EventMaterialQuerySource;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyStrengths.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;

/** Same canonical Army family, complete native service projections, and immutable original selection preimages. */
public final class ArmyStrengthsMaterialQuery implements EventMaterialQuerySource<Read> {
    public static final String CONTEXT_SCHEMA="xar.army-event-material-selection-original/v1";
    private static final int MAXIMUM_CONTEXT_BYTES=16*1024*1024;
    private final ArmyStrengthsContracts contracts;
    private final ArmyStrengthsPipeline pipeline;
    private final ArmyStrengthsService.Current current;
    private final Supplier<RootReadContractCatalog> catalog;
    /** Root binds this only to its original writer/archive; native-transport cannot depend on the service/storage adapters. */
    @FunctionalInterface public interface SelectionOriginals { ExactRef preserve(byte[] original,int maximumBytes)throws IOException; }
    private final SelectionOriginals originals;
    public ArmyStrengthsMaterialQuery(ArmyStrengthsContracts sameContracts,ArmyStrengthsPipeline sameCompletePipeline,
            ArmyStrengthsService.Current sameCurrent,Supplier<RootReadContractCatalog> sameInstalledCatalog,
            SelectionOriginals sameOriginals) {
        contracts=Objects.requireNonNull(sameContracts);pipeline=Objects.requireNonNull(sameCompletePipeline);
        current=Objects.requireNonNull(sameCurrent);catalog=Objects.requireNonNull(sameInstalledCatalog);
        originals=Objects.requireNonNull(sameOriginals);
    }
    @Override public OperationKey operation() { return new OperationKey(STEP); }
    @Override public Resolved<Read> resolve(Frame frame) {
        Objects.requireNonNull(frame);contracts.requireCompleteRich();pipeline.requireComplete();
        ArmyStrengthsService.CurrentFrame held=Objects.requireNonNull(current.current());
        Snapshot snapshot=boundSnapshot(frame,held.snapshot());
        Query query=new Query(Profile.ORDINARY_CORE_V1,Mode.EXPLICIT_RICH,new Missing<>(),EntryMode.OBSERVED_PREPARED,EntryMode.OBSERVED_PREPARED);
        var selection=new ArmyStrengthsContracts.Selection(snapshot,query,held.originalHello(),new Missing<>());
        ReadContract<Read> contract=contracts.issue(Objects.requireNonNull(catalog.get()),selection);PlanningReadRequest request=contracts.request(selection);
        require(contract.hasPureReplay(),"the actual canonical Army family must explicitly install pure original replay");
        try {
            byte[] body=encodeContext(frame,selection,contract.contractId());
            ExactRef original=originals.preserve(body,MAXIMUM_CONTEXT_BYTES);
            require(original.bytes()==body.length&&original.sha256().equals(digest(body)),"the actual original archive must return the exact selection preimage bytes");
            var resolved=new Resolved<>(contract,request,value->encode(selection,value),Optional.of(original));resolved.requireFrame(frame,operation());return resolved;
        }catch(IOException failure) { throw new UncheckedIOException("actual Army material selection original could not be preserved",failure); }
    }
    @Override public Resolved<Read> restore(Frame originalFrame,PlanningReadReceipt original,Optional<ExactRef> replayContext,ActionPorts.OutcomeArchive actualArchive) {
        Objects.requireNonNull(originalFrame);Objects.requireNonNull(original);Objects.requireNonNull(actualArchive);
        ExactRef ref=Objects.requireNonNull(replayContext).orElseThrow(()->new IllegalArgumentException("actual original Army selection sidecar required"));
        require(ref.bytes()>0&&ref.bytes()<=MAXIMUM_CONTEXT_BYTES,"bounded original Army selection required");
        RawJson originalBytes=actualArchive.loadMaterial(ref);require(originalBytes.bytes().length==ref.bytes()&&digest(originalBytes.bytes()).equals(ref.sha256()),"Army selection sidecar differs from its archived exact bytes");
        ObjectNode sidecar=StrictJson.object(StrictJson.parse(originalBytes.bytes(),MAXIMUM_CONTEXT_BYTES),Set.of("schema","before","source","session_id","deadline","contract_id","snapshot_base64","snapshot_sha256","hello_base64","hello_sha256"));
        require(CONTEXT_SCHEMA.equals(StrictJson.text(sidecar.get("schema")))&&sidecar.get("before").equals(ProposalLifecycleCodec.observation(originalFrame.before()))
                &&sidecar.get("source").equals(source(originalFrame))&&StrictJson.text(sidecar.get("session_id")).equals(originalFrame.sessionId())
                &&StrictJson.text(sidecar.get("deadline")).equals(originalFrame.deadline().toString())
                &&StrictJson.text(sidecar.get("contract_id")).equals(original.contractId()),"original Army selection crossed its source/frame/session/deadline/contract");
        require(original.request().before().equals(originalFrame.before())&&original.request().source().equals(originalFrame.source())
                &&original.request().sessionId().equals(originalFrame.sessionId())&&original.request().deadline().equals(originalFrame.deadline()),"Army material restore must use the original read deadline and identity");
        byte[] snapshotBytes=blob(sidecar,"snapshot"),helloBytes=blob(sidecar,"hello");
        Context context=new Context(originalFrame.before(),originalFrame.source(),originalFrame.sessionId(),originalFrame.deadline());
        Snapshot snapshot=ArmyStrengthsCodec.snapshot(context,new RawJson(snapshotBytes));
        require(OpportunityJson.object(OpportunityJson.parse(snapshot.original().bytes()),"Army original snapshot").equals(originalFrame.semantic()),"Army original snapshot differs from the independently retained material frame");
        NativeWire.Hello hello;
        try { var packet=NativeWire.decode(helloBytes);require(packet instanceof NativeWire.Hello,"Army original HELLO packet required");hello=(NativeWire.Hello)packet; }
        catch(IOException invalid) { throw new UncheckedIOException("original Army HELLO cannot be decoded",invalid); }
        var selection=new ArmyStrengthsContracts.Selection(snapshot,query(original.request().arguments()),hello,new Missing<>());
        ReadContract<Read> contract=contracts.issue(Objects.requireNonNull(catalog.get()),selection);PlanningReadRequest request=contracts.request(selection);
        require(contract.hasPureReplay(),"the restored canonical Army family must explicitly install pure original replay");
        require(contract.contractId().equals(original.contractId())&&request.equals(original.request()),"original Army canonical request or family selection identity changed");
        var resolved=new Resolved<>(contract,request,value->encode(selection,value),Optional.of(ref));resolved.requireFrame(originalFrame,operation());return resolved;
    }
    private RawJson encode(ArmyStrengthsContracts.Selection selection,Read original) {
        require(original.original().request().equals(contracts.request(selection)),"complete Army material must be the actual selected read");
        List<Row> rows=original.rows();if(selection.query().requestedArmies() instanceof Present<List<PublicUnitId>> selected)rows=selected.value().stream().map(id->original.rows().stream().filter(row->row.core().army().equals(id)).findFirst().orElseThrow()).toList();
        var projected=pipeline.project(new ArmyStrengthsPipeline.Input(selection.snapshot(),original,selection.query(),rows,Optional.of(selection.originalHello())));
        return nativeJson(selection,original,rows,projected);
    }
    private static Snapshot boundSnapshot(Frame frame,Snapshot actual) {
        Context observed=actual.context();require(observed.before().equals(frame.before())&&observed.source().equals(frame.source())&&observed.sessionId().equals(frame.sessionId()),"Army material current provider moved from the independent requested frame");
        require(OpportunityJson.object(OpportunityJson.parse(actual.original().bytes()),"Army actual snapshot").equals(frame.semantic()),"Army material requires the original complete snapshot bytes, not a reconstructed field subset");
        // The read-only observation window is the actual caller's deadline; it grants no new submission authority.
        Context read=new Context(frame.before(),frame.source(),frame.sessionId(),frame.deadline());return new Snapshot(read,actual.binding(),actual.scope(),actual.original());
    }
    private static byte[] encodeContext(Frame frame,ArmyStrengthsContracts.Selection selected,String contractId) {
        byte[] snapshot=selected.snapshot().original().bytes(),hello=selected.originalHello().packet().value();ObjectNode n=StrictJson.object().put("schema",CONTEXT_SCHEMA);
        n.set("before",ProposalLifecycleCodec.observation(frame.before()));n.set("source",source(frame));n.put("session_id",frame.sessionId());n.put("deadline",frame.deadline().toString());n.put("contract_id",contractId);
        n.put("snapshot_base64",Base64.getEncoder().encodeToString(snapshot));n.put("snapshot_sha256",digest(snapshot));n.put("hello_base64",Base64.getEncoder().encodeToString(hello));n.put("hello_sha256",digest(hello));return StrictJson.canonical(n,MAXIMUM_CONTEXT_BYTES);
    }
    private static ObjectNode source(Frame frame) { var s=frame.source();ObjectNode n=StrictJson.object().put("machine_id",s.machineId()).put("observed_at_utc",s.observedAtUtc()).put("exact_build",s.exactBuild());n.set("source_ref",s.sourceRef().toJson());return n; }
    private static byte[] blob(ObjectNode context,String name) {
        String text=StrictJson.text(context.get(name+"_base64"));byte[] bytes=Base64.getDecoder().decode(text);require(Base64.getEncoder().encodeToString(bytes).equals(text)&&digest(bytes).equals(StrictJson.text(context.get(name+"_sha256"))),"original Army selection blob changed");return bytes;
    }
    private static Query query(OpportunityJson.Obj original) {
        Set<String> fields=new HashSet<>(Set.of("profile","mode","ordered_refill_entry_mode","ordered_besieging_entry_mode"));if(original.get("army_ids")!=null)fields.add("army_ids");require(fields.equals(original.members().keySet()),"original Army material query fields differ");
        Field<List<PublicUnitId>> armies=new Missing<>();if(original.get("army_ids") instanceof OpportunityJson.Arr rows) { List<PublicUnitId> ids=new ArrayList<>();for(var row:rows.items())ids.add(new PublicUnitId(OpportunityJson.integer(row,"Army ID").intValueExact()));armies=new Present<>(List.copyOf(ids)); }else require(original.get("army_ids")==null,"Army ID list must be a present ordered array or missing");
        return new Query(Profile.valueOf(OpportunityJson.text(original.get("profile"),"profile").toUpperCase(Locale.ROOT)),Mode.valueOf(OpportunityJson.text(original.get("mode"),"mode")),armies,
                EntryMode.valueOf(OpportunityJson.text(original.get("ordered_refill_entry_mode"),"refill entry").toUpperCase(Locale.ROOT)),EntryMode.valueOf(OpportunityJson.text(original.get("ordered_besieging_entry_mode"),"besieging entry").toUpperCase(Locale.ROOT)));
    }
    /** Sole native numeric complete service envelope for internal event materials; public/v2 remains separately encoded. */
    public static RawJson nativeJson(ArmyStrengthsContracts.Selection selection,Read original,List<Row> rows,ArmyStrengthsPipeline.Results projections) {
        Objects.requireNonNull(selection);Objects.requireNonNull(original);rows=List.copyOf(rows);Objects.requireNonNull(projections);Binding frame=selection.snapshot().binding();
        ObjectNode out=ArmyJson.object(ArmyStrengthsCodec.parseValue(original.original().original().originalResultToken().orElseThrow())).deepCopy();
        out.put("schema_version",1);out.put("status",ArmyStrengthsCodec.wire(ArmyStrengths.status(rows)));Status scope=original.publishedScopeStatus() instanceof Present<Status> p?p.value():original.status();out.put("scope_status",ArmyStrengthsCodec.wire(scope));out.put("scope","player-and-active-war-participants");
        out.put("queried_snapshot_id",frame.snapshotId());out.put("queried_revision",frame.publicRevision());out.put("queried_native_revision",frame.nativeRevision());out.put("queried_date_raw",frame.dateRaw());out.put("queried_connection_generation",frame.connectionGeneration());frame.episodeRunId().ifPresentOrElse(id->out.put("queried_episode_run_id",id),()->out.putNull("queried_episode_run_id"));
        out.put("army_strengths_profile",original.profile().wire());out.put("army_observed_phase_coverage",original.profile().coverage());out.put("ordered_refill_entry_mode",ArmyStrengthsCodec.wire(selection.query().refillEntryMode()));out.put("ordered_besieging_entry_mode",ArmyStrengthsCodec.wire(selection.query().besiegingEntryMode()));
        var requested=out.putArray("army_ids");rows.forEach(row->requested.add(row.core().army().value()));var scopeIds=out.putArray("scope_army_ids");selection.snapshot().scope().forEach(row->scopeIds.add(row.army().value()));var encodedRows=out.putArray("army_strengths");rows.forEach(row->encodedRows.add(projections.rowJson(row)));out.setAll(projections.topLevelJson());
        ObjectNode source=out.putObject("source").put("snapshot_id",frame.snapshotId()).put("revision",frame.publicRevision()).put("native_revision",frame.nativeRevision()).put("date_raw",frame.dateRaw()).put("paused",true).put("executable_sha256",selection.originalHello().gameSha256());
        try {
            byte[] hello=selection.originalHello().packet().value();ObjectNode raw=NativeWire.object(NativeWire.parse(Arrays.copyOfRange(hello,4,hello.length)));
            JsonNode version=raw.has("expected_ck3_version")?raw.get("expected_ck3_version"):raw.get("game_version");
            if(version==null||version.isNull())source.putNull("game_version");else source.put("game_version",ArmyJson.nonempty(version));
        }catch(IOException invalid){throw new UncheckedIOException("actual original Army HELLO cannot be decoded",invalid);}
        JsonNode backend=ArmyJson.parse(selection.snapshot().original().bytes()).get("backend_id");if(backend==null||backend.isNull())source.putNull("backend_id");else source.put("backend_id",ArmyJson.nonempty(backend));
        return new RawJson(ArmyJson.bytes(out));
    }
    private static String digest(byte[] bytes) { try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }catch(NoSuchAlgorithmException unavailable) { throw new IllegalStateException(unavailable); } }
}
