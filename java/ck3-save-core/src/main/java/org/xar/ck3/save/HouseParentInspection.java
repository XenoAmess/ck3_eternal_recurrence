package org.xar.ck3.save;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;
import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.io.Reader;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.save.SaveContracts.*;

/** Complete House parent references without retaining every House AST. Never grants gameplay acceptance. */
public final class HouseParentInspection {
    private static final Comparator<NativeId> ORDER =
            Comparator.comparingInt((NativeId id) -> id.value().length()).thenComparing(NativeId::value);
    private HouseParentInspection() { }

    public record Selection(List<String> houseTablePath, List<String> dynastyTablePath) {
        public Selection {
            houseTablePath = SaveContracts.checkedPath(houseTablePath);
            dynastyTablePath = SaveContracts.checkedPath(dynastyTablePath);
            if (houseTablePath.equals(dynastyTablePath)) throw new IllegalArgumentException("distinct explicit House and Dynasty tables required");
        }
        SaveContracts.Selection streamSelection() {
            return new SaveContracts.Selection(List.of(
                    new TableSelection(ScopeKind.HOUSE, houseTablePath, List.of(), true),
                    new TableSelection(ScopeKind.DYNASTY, dynastyTablePath, List.of(), true)),
                    List.of(), false, false, List.of());
        }
    }
    public record Request(int schemaVersion, String machineId, String repository, Pin save, Pin decoder, Selection selection) {
        public Request {
            if (schemaVersion != 1 || machineId == null || !machineId.matches("[a-z0-9][a-z0-9-]{2,95}")
                    || repository == null || !Path.of(repository).isAbsolute())
                throw new IllegalArgumentException("version1, machine and absolute repository required");
            Objects.requireNonNull(save); Objects.requireNonNull(decoder); Objects.requireNonNull(selection);
        }
    }
    /** Wire is exactly [HouseID, DynastyID], both canonical strings; there is no object/number alias. */
    public record HouseParentLink(NativeId houseId, NativeId dynastyId) {
        public HouseParentLink { Objects.requireNonNull(houseId); Objects.requireNonNull(dynastyId); }
        @JsonCreator(mode = JsonCreator.Mode.DELEGATING)
        public static HouseParentLink fromJson(JsonNode node) {
            if (node == null || !node.isArray() || node.size() != 2)
                throw new IllegalArgumentException("exact two-string House/Dynasty row required");
            return new HouseParentLink(NativeId.fromJson(node.get(0)), NativeId.fromJson(node.get(1)));
        }
        @JsonValue public List<NativeId> toJson() { return List.of(houseId, dynastyId); }
    }
    public enum Coverage { COMPLETE_FULL_HOUSE_RECORD_PARENTS }
    public record Projection(List<Inventory> inventories, List<HouseParentLink> houseParents, long tokens, Coverage coverage) {
        public Projection {
            inventories = List.copyOf(inventories); houseParents = List.copyOf(houseParents);
            if (inventories.size() != 2 || houseParents.size() > 200000 || tokens < 1
                    || coverage != Coverage.COMPLETE_FULL_HOUSE_RECORD_PARENTS)
                throw new IllegalArgumentException("bounded complete House-parent projection required");
        }
        public List<NativeId> housesInDynasty(NativeId dynastyId) {
            Objects.requireNonNull(dynastyId);
            if (!inventory(this, ScopeKind.DYNASTY).ids().contains(dynastyId))
                throw new IllegalArgumentException("requested Dynasty absent from complete inventory");
            return houseParents.stream().filter(row -> row.dynastyId().equals(dynastyId)).map(HouseParentLink::houseId).toList();
        }
    }
    public record Report(String schema, String machineId, String observedAtUtc, Request request, Projection projection,
                         SaveDecoder.ReadEvidence decoder, ProducerSources.Binding producerBefore, ProducerSources.Binding producerAfter,
                         Inspection.BusinessAssessment businessAssessment, boolean gameStarted) {
        public Report {
            if (!"ck3-save-house-parents-v1".equals(schema) || request == null || projection == null || decoder == null
                    || !request.machineId().equals(machineId) || !request.save().equals(decoder.save()) || !request.decoder().equals(decoder.decoder())
                    || producerBefore == null || !producerBefore.equals(producerAfter)
                    || businessAssessment != Inspection.BusinessAssessment.NOT_ASSESSED || gameStarted)
                throw new IllegalArgumentException("complete offline House-parent report required");
            Instant.parse(observedAtUtc);
            if (projection.tokens() > Long.parseLong(decoder.streamBytes())) throw new IllegalArgumentException("tokens exceed complete stream bytes");
            validate(request.selection(), projection);
        }
    }
    public static Report inspect(Request request) throws IOException { return inspect(request, SaveDecoder::launch); }
    /** Caller must retain its own SDK/custody and OS-held input checks; these are not replaced by this API. */
    public static Report inspect(Request request, SaveDecoder.Launcher launcher) throws IOException {
        ProducerSources.Binding before = ProducerSources.verify(Path.of(request.repository()));
        SaveDecoder.StreamDecoded<Projection> decoded = SaveDecoder.decode(request.save(), request.decoder(), DecoderLimits.standard(), launcher,
                reader -> read(reader, request.selection()));
        ProducerSources.Binding after = ProducerSources.verify(Path.of(request.repository()));
        return InspectionFiles.bounded(new Report("ck3-save-house-parents-v1", request.machineId(), Instant.now().toString(), request,
                decoded.value(), decoded.evidence(), before, after, Inspection.BusinessAssessment.NOT_ASSESSED, false));
    }
    static Projection read(Reader reader, Selection selection) throws IOException {
        Collector collector = new Collector(selection);
        SaveContracts.Projection census = new SaveStream(reader, selection.streamSelection(), collector).read();
        return collector.finish(census);
    }
    private static Inventory inventory(Projection projection, ScopeKind kind) {
        List<Inventory> found = projection.inventories().stream().filter(i -> i.kind() == kind).toList();
        if (found.size() != 1) throw new IllegalArgumentException("exact House and Dynasty inventories required");
        return found.getFirst();
    }
    private static void validate(Selection selection, Projection projection) {
        Inventory houses = inventory(projection, ScopeKind.HOUSE), dynasties = inventory(projection, ScopeKind.DYNASTY);
        for (Inventory inventory : projection.inventories()) {
            List<String> expected = inventory.kind() == ScopeKind.HOUSE ? selection.houseTablePath() : selection.dynastyTablePath();
            if (inventory.availability() != Availability.OBSERVED || !inventory.path().equals(expected) || inventory.ids().size() > 200000
                    || new HashSet<>(inventory.ids()).size() != inventory.ids().size()
                    || !inventory.ids().equals(inventory.ids().stream().sorted(ORDER).toList()))
                throw new IllegalArgumentException("observed unique sorted complete inventories required");
        }
        if (projection.houseParents().size() != houses.ids().size())
            throw new IllegalArgumentException("all full House inventory IDs require one parent");
        HashSet<NativeId> dynastyIds = new HashSet<>(dynasties.ids());
        for (int i = 0; i < houses.ids().size(); i++) {
            HouseParentLink row = projection.houseParents().get(i);
            if (!row.houseId().equals(houses.ids().get(i)) || !dynastyIds.contains(row.dynastyId()))
                throw new IllegalArgumentException("House-parent coverage/order or Dynasty reference mismatch");
        }
    }
    /** Receives only events from the same full SaveStream grammar walk and its independently collected inventories. */
    static final class Collector {
        private final Selection selection;
        private final List<HouseParentLink> rows = new ArrayList<>();
        private List<String> currentPath;
        private NativeId currentId;
        private NativeId parent;
        Collector(Selection selection) { this.selection = selection; }
        void enter(List<String> path) throws IOException {
            if (directChild(path, selection.dynastyTablePath())) id(path.getLast());
            if (!directChild(path, selection.houseTablePath())) return;
            if (currentPath != null) throw new IOException("overlapping full House records");
            currentId = id(path.getLast()); currentPath = path; parent = null;
        }
        void field(List<String> path, String key, String value) throws IOException {
            if (!path.equals(currentPath) || !key.equals("dynasty")) return;
            if (parent != null) throw new IOException("duplicate direct House dynasty field");
            parent = id(value);
        }
        void unassigned(List<String> path, String atom) throws IOException {
            if (path.equals(currentPath) && atom.equals("dynasty")) throw new IOException("unassigned House dynasty field");
        }
        void leave(List<String> path) throws IOException {
            if (!path.equals(currentPath)) return;
            if (parent == null) throw new IOException("full House record lacks its direct dynasty field");
            rows.add(new HouseParentLink(currentId, parent));
            if (rows.size() > 200000) throw new IOException("House-parent identity cap exceeded");
            currentPath = null; currentId = null; parent = null;
        }
        Projection finish(SaveContracts.Projection census) throws IOException {
            if (currentPath != null) throw new IOException("incomplete House record");
            Projection result = new Projection(census.inventories().stream()
                    .filter(i -> i.kind() == ScopeKind.HOUSE || i.kind() == ScopeKind.DYNASTY).toList(),
                    rows.stream().sorted(Comparator.comparing(HouseParentLink::houseId, ORDER)).toList(),
                    census.tokens(), Coverage.COMPLETE_FULL_HOUSE_RECORD_PARENTS);
            try { validate(selection, result); } catch (IllegalArgumentException invalid) { throw new IOException("invalid complete House-parent inventory", invalid); }
            return result;
        }
        private static boolean directChild(List<String> path, List<String> table) {
            return path.size() == table.size() + 1 && path.subList(0, table.size()).equals(table);
        }
        private static NativeId id(String value) throws IOException {
            try { return new NativeId(value); }
            catch (IllegalArgumentException invalid) { throw new IOException("canonical direct House/Dynasty ID required", invalid); }
        }
    }
    public static int run(String[] args, SaveDecoder.Launcher launcher) {
        return InspectionFiles.run(args, Request.class, request -> inspect(request, launcher));
    }
    public static Report readReport(byte[] bytes) throws IOException { return InspectionFiles.readReport(bytes, Report.class); }
}
