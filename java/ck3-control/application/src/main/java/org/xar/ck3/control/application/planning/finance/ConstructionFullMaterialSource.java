package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Arrays;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.action.ActionCodec;
import java.util.Optional;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.application.driver.DriverJson;

/** Complete reducer input in the existing same-writer material archive; JSON references alone grant no read or business authority. */
public record ConstructionFullMaterialSource(ExactRef input) {
    public static final String SCHEMA = "xar.construction-material-source/v2";
    public static final String BODY_FIELD = "java_construction_material_source_v2";
    public static final int MAX_INPUT_BYTES = RawJson.MAXIMUM_BYTES;

    public ConstructionFullMaterialSource {
        Objects.requireNonNull(input);
        require(input.bytes() > 0 && input.bytes() <= MAX_INPUT_BYTES, "bounded complete original material input required");
    }

    public Obj toJson() {
        return obj("schema", new Text(SCHEMA), "input", object(parse(StrictJson.canonical(input.toJson())), "original material reference"));
    }

    public static ConstructionFullMaterialSource decode(Obj value) {
        require(value.members().keySet().equals(Set.of("schema", "input")) && new Text(SCHEMA).equals(value.get("schema")), "exact material source contract required");
        return new ConstructionFullMaterialSource(ExactRef.fromJson(StrictJson.parse(encode(object(value.get("input"), "complete material input reference")))));
    }

    /** Explicit full-input version through the existing same-writer 64 MiB material lane; legacy limits stay separate. */
    public static ConstructionFullMaterialSource preserve(ContinuityStorePort.Session same, ActionPorts.OutcomeArchive archive, Obj actualInput) throws IOException {
        Objects.requireNonNull(same); Objects.requireNonNull(archive); Objects.requireNonNull(actualInput);
        byte[] original = DriverJson.encode(actualInput);
        ConstructionMaterialReducer.decodeFullMaterial(original);
        require(original.length <= MAX_INPUT_BYTES, "complete material input exceeds its original reducer bound");
        try {
            var held = archive.withSession(same);
            ExactRef reference = held.preserveMaterial(RawJson.fullMaterial(original));
            var source = new ConstructionFullMaterialSource(reference);
            byte[] reopened = source.readBytes(same, archive);
            require(Arrays.equals(original, reopened), "complete material archive readback changed");
            return source;
        } catch (UncheckedIOException unavailable) { throw unavailable.getCause(); }
    }

    /** Same original writer, committed immutable FileID, digest, length and live captured pin are rechecked on every consume. */
    public ConstructionMaterialReducer.Input load(ContinuityStorePort.Session same, ActionPorts.OutcomeArchive archive) throws IOException {
        return ConstructionMaterialReducer.decodeFullMaterial(readBytes(same, archive));
    }

    private byte[] readBytes(ContinuityStorePort.Session same, ActionPorts.OutcomeArchive archive) throws IOException {
        try {
            var held = Objects.requireNonNull(archive).withSession(Objects.requireNonNull(same));
            RawJson raw = held.loadFullMaterial(input);
            byte[] original=raw.bytes();
            require(original.length<=MAX_INPUT_BYTES&&input.bytes()==original.length&&input.sha256().equals(ActionCodec.sha256(original)), "complete material original identity changed");
            return original;
        } catch (UncheckedIOException unavailable) { throw unavailable.getCause(); }
    }

    /** Called after the owning source guards/reducer; the body retains only the typed reference, never the complete input. */
    public Obj retainIn(Obj reduced) {
        Objects.requireNonNull(reduced);fromBody(reduced);
        var members=new java.util.LinkedHashMap<>(reduced.members());
        members.remove(ConstructionMaterialSource.BODY_FIELD);members.put(BODY_FIELD,toJson());
        Obj result=new Obj(members);
        ConstructionLedgerCodec.validateLedger(DriverJson.encode(result));
        // Only the new retained DOMAIN BODY uses its existing canonical destination codec; full input/query bytes stay untouched.
        int maximum=ConstructionLedgerCodec.MAX_BYTES;
        return DriverJson.object(ContinuityJson.canonical(ContinuityJson.parseObject(DriverJson.encode(result),maximum),maximum),maximum);
    }
    /** Shape only. Every actual owner must call load with its held writer before consuming a new full source. */
    public static Optional<ConstructionFullMaterialSource> fromBody(Obj body) {
        require(!(body.members().containsKey(BODY_FIELD)&&body.members().containsKey(ConstructionMaterialSource.BODY_FIELD)),
                "mixed active construction material source versions");
        if(body.members().containsKey(ConstructionMaterialSource.BODY_FIELD))
            ConstructionMaterialSource.decode(object(body.get(ConstructionMaterialSource.BODY_FIELD),"legacy construction material source"));
        if(!body.members().containsKey(BODY_FIELD))return Optional.empty();
        return Optional.of(decode(object(body.get(BODY_FIELD),"explicit full construction material source")));
    }
    public static void requireRetained(ContinuityStorePort.Session same,ActionPorts.OutcomeArchive archive,Obj body)throws IOException {
        var full=fromBody(body);
        if(full.isPresent())full.orElseThrow().load(same,archive);
    }
}
