package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.Arrays;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Complete reducer input in the existing same-writer material archive; JSON references alone grant no read or business authority. */
public record ConstructionMaterialSource(ExactRef input) {
    public static final String SCHEMA = "xar.construction-material-source/v1";
    public static final String BODY_FIELD = "java_construction_material_source_v1";
    // This is the existing ConstructionMaterialReducer input limit, not a larger canonical document/body allowance.
    public static final int MAX_INPUT_BYTES = ConstructionMaterialReducer.MAX_INPUT_BYTES;
    public ConstructionMaterialSource {
        Objects.requireNonNull(input);
        require(input.bytes() > 0 && input.bytes() <= MAX_INPUT_BYTES, "bounded complete original material input required");
    }
    public Obj toJson() {
        return obj("schema", new Text(SCHEMA), "input", object(parse(StrictJson.canonical(input.toJson())), "original material reference"));
    }
    public static ConstructionMaterialSource decode(Obj value) {
        require(value.members().keySet().equals(Set.of("schema", "input")) && new Text(SCHEMA).equals(value.get("schema")), "exact material source contract required");
        return new ConstructionMaterialSource(ExactRef.fromJson(StrictJson.parse(encode(object(value.get("input"), "complete material input reference")))));
    }
    /** Preserve through the shared 64 MiB RawJson material path; original input retains its narrower existing reducer bound. */
    public static ConstructionMaterialSource preserve(ContinuityStorePort.Session same, ActionPorts.OutcomeArchive archive, Obj actualInput) throws IOException {
        Objects.requireNonNull(same); Objects.requireNonNull(archive); Objects.requireNonNull(actualInput);
        byte[] original = encode(actualInput); ConstructionMaterialReducer.decode(original);
        require(original.length <= MAX_INPUT_BYTES, "complete material input exceeds its original reducer bound");
        try {
            var held = archive.withSession(same);
            ExactRef reference = held.preserveMaterial(new RawJson(original));
            var source = new ConstructionMaterialSource(reference);
            byte[] reopened = source.readBytes(same, archive);
            require(Arrays.equals(original, reopened) && held.materialReferenceOf(new RawJson(reopened)).equals(reference), "complete material archive readback changed");
            return source;
        } catch (UncheckedIOException unavailable) { throw unavailable.getCause(); }
    }
    /** Same original writer, committed immutable FileID, digest, length and live captured pin are rechecked on every consume. */
    public ConstructionMaterialReducer.Input load(ContinuityStorePort.Session same, ActionPorts.OutcomeArchive archive) throws IOException {
        return ConstructionMaterialReducer.decode(readBytes(same, archive));
    }
    private byte[] readBytes(ContinuityStorePort.Session same, ActionPorts.OutcomeArchive archive) throws IOException {
        try {
            var held = Objects.requireNonNull(archive).withSession(Objects.requireNonNull(same));
            RawJson raw = held.loadMaterial(input);
            require(raw.bytes().length <= MAX_INPUT_BYTES && held.materialReferenceOf(raw).equals(input), "complete material original identity changed");
            return raw.bytes();
        } catch (UncheckedIOException unavailable) { throw unavailable.getCause(); }
    }
    /** Called after the owning source guards/reducer; the body retains only the typed reference, never the complete input. */
    public Obj retainIn(Obj reduced) {
        Obj result = Objects.requireNonNull(reduced).with(BODY_FIELD, toJson());
        ConstructionLedgerCodec.validateLedger(encode(result)); return result;
    }
}
