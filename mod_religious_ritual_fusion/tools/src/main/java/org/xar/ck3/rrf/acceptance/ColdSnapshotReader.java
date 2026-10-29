package org.xar.ck3.rrf.acceptance;

import java.io.IOException;
import java.math.BigDecimal;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import org.xar.ck3.rrf.acceptance.FixtureContracts.CompletedSnapshotSetup;
import org.xar.ck3.rrf.acceptance.FixtureContracts.DivorceRule;
import org.xar.ck3.rrf.acceptance.FixtureContracts.DivorceRules;
import org.xar.ck3.rrf.acceptance.FixtureContracts.FilePin;
import org.xar.ck3.rrf.acceptance.FixtureContracts.PietyAmount;
import org.xar.ck3.rrf.acceptance.FixtureContracts.Request;
import org.xar.ck3.rrf.acceptance.FixtureContracts.SnapshotEvidence;
import org.xar.ck3.save.Clausewitz;
import org.xar.ck3.save.FilePins;
import org.xar.ck3.save.Inspection;
import org.xar.ck3.save.SaveContracts.Coverage;
import org.xar.ck3.save.SaveContracts.NativeId;
import org.xar.ck3.save.SaveContracts.ScopeKind;
import org.xar.ck3.save.SaveJson;

/** Binds existing V4 observations, without decoding a save or granting live business credit. */
public final class ColdSnapshotReader {
    private static final int REPORT_LIMIT = 1024 * 1024;
    private static final BigDecimal RAW_SCALE = BigDecimal.valueOf(100000);
    private ColdSnapshotReader() { }

    /** Actual inputs, separate from repository-only producer sources. */
    public static List<FilePin> inputPins(Request request) {
        if (!(request.setup() instanceof SnapshotEvidence snapshot)) return List.of();
        return List.of(snapshot.sourceSave(), snapshot.sourceInspection(), snapshot.creationHistory().beforeInspection(),
                snapshot.creationHistory().afterInspection()).stream().distinct().toList();
    }

    public static void verify(Request request, String machineId, Path repository) throws IOException {
        verifiedDivorceRules(request, machineId, repository);
    }

    public static DivorceRules verifiedDivorceRules(Request request, String machineId, Path repository) throws IOException {
        if (!(request.setup() instanceof SnapshotEvidence snapshot)) return new DivorceRules(DivorceRule.ALLOWED, DivorceRule.ALLOWED);
        try {
            verifySave(snapshot.sourceSave());
            Inspection.Report current = report(snapshot.sourceInspection(), machineId, repository);
            Inspection.Report before = report(snapshot.creationHistory().beforeInspection(), machineId, repository);
            Inspection.Report after = report(snapshot.creationHistory().afterInspection(), machineId, repository);
            var declared = snapshot.sourceSave(); var observed = current.decoded().save();
            if (!declared.path().equals(observed.path()) || declared.bytes() != observed.bytes() || !declared.sha256().equals(observed.sha256()))
                throw new IOException("cold source save differs from the actual V4 observation");
            String campaign = rootAtom(current, "playthrough_id");
            if (!campaign.equals(rootAtom(before, "playthrough_id")) || !campaign.equals(rootAtom(after, "playthrough_id")))
                throw new IOException("creation history and cold snapshot belong to different campaigns");
            Clausewitz.Block b = actor(before, snapshot.actorId()), a = actor(after, snapshot.actorId()), c = actor(current, snapshot.actorId());
            requireAmount(wallet(b), snapshot.creationHistory().before(), "creation before");
            requireAmount(wallet(a), snapshot.creationHistory().after(), "creation after");
            requireAmount(wallet(c), snapshot.expectedCurrentPiety(), "cold current");
            PietyAmount charge = new PietyAmount(Integer.toString(request.mode().cost()));
            requireAmount(valueVariable(a, "rrf_charged_cost"), charge, "creation charged cost");
            requireAmount(valueVariable(c, "rrf_charged_cost"), charge, "persisted charged cost");
            for (Clausewitz.Block record : List.of(b, a, c))
                requireAmount(valueVariable(record, "rrfa_piety_before"), snapshot.creationHistory().before(), "original fixture wallet");
            if (!variables(b, "rrf_last_result_rite").isEmpty()) throw new IOException("creation-before report already has a fusion result");
            String result = riteReference(a, "rrf_last_result_rite");
            if (!result.equals(a.atom("rite", "")) || !result.equals(c.atom("rite", ""))
                    || !result.equals(riteReference(c, "rrf_last_result_rite")))
                throw new IOException("creation and cold snapshot do not identify the same adopted result");
            DivorceRules rules = new DivorceRules(DivorceRule.ALLOWED, DivorceRule.ALLOWED);
            if (request.setup() instanceof CompletedSnapshotSetup) {
                NativeId id = new NativeId(result);
                Clausewitz.Block originalRite = fullRecord(after, ScopeKind.RITE, id), currentRite = fullRecord(current, ScopeKind.RITE, id);
                List<String> original = originDoctrines(originalRite), retained = originDoctrines(currentRite);
                if (!original.equals(retained)) throw new IOException("completed snapshot changed the ordered creation origin doctrines");
                rules = new DivorceRules(divorceRule(currentDoctrines(currentRite)), divorceRule(original));
            }
            verifySave(snapshot.sourceSave());
            return rules;
        } catch (IllegalArgumentException invalid) {
            throw new IOException("invalid cold snapshot evidence: " + invalid.getMessage(), invalid);
        }
    }

    /** A closed zero-day wallet predicate; it is never applied as a five-day wallet forecast. */
    public static String walletPredicate(Request request) {
        if (request.setup() instanceof SnapshotEvidence snapshot)
            return "piety = " + snapshot.expectedCurrentPiety().value()
                    + "\n    var:rrfa_piety_before = " + snapshot.creationHistory().before().value();
        return "piety = rrfa_expected_post_piety_value";
    }

    private static void verifySave(FilePin expected) throws IOException {
        if (expected.bytes() > 512L * 1024 * 1024) throw new IOException("cold input save exceeds inspection bound");
        var actual = FilePins.pin(Path.of(expected.path()));
        if (!expected.path().equals(actual.path()) || expected.bytes() != actual.bytes() || !expected.sha256().equals(actual.sha256()))
            throw new IOException("cold input save pin changed");
    }

    private static Inspection.Report report(FilePin expected, String machineId, Path repository) throws IOException {
        Path path = Path.of(expected.path());
        if (expected.bytes() > REPORT_LIMIT || !path.toRealPath().toString().equals(expected.path()))
            throw new IOException("bounded canonical V4 report pin required");
        byte[] bytes;
        try (var input = Files.newInputStream(path)) { bytes = input.readNBytes(REPORT_LIMIT + 1); }
        if (bytes.length != expected.bytes() || !FilePins.sha256(bytes).equals(expected.sha256())) throw new IOException("V4 report pin changed");
        Inspection.Report report = SaveJson.read(bytes, Inspection.Report.class);
        if (!report.machineId().equals(machineId) || !Path.of(report.request().repository()).toRealPath().equals(repository.toRealPath()))
            throw new IOException("cold observation machine/repository mismatch");
        return report;
    }

    private static Clausewitz.Block actor(Inspection.Report report, NativeId actorId) throws IOException {
        return fullRecord(report, ScopeKind.ACTOR, actorId);
    }

    private static Clausewitz.Block fullRecord(Inspection.Report report, ScopeKind kind, NativeId id) throws IOException {
        var tables = report.request().selection().tables().stream().filter(t -> t.kind() == kind).toList();
        if (tables.size() != 1 || !tables.getFirst().ids().contains(id)
                || kind == ScopeKind.RITE && !tables.getFirst().required())
            throw new IOException("record was not explicitly selected in the pinned report: " + kind);
        List<String> path = new ArrayList<>(tables.getFirst().path()); path.add(id.value());
        var selected = report.decoded().projection().scopes().stream()
                .filter(s -> s.kind() == kind && s.path().equals(path)).toList();
        if (selected.size() != 1 || selected.getFirst().coverage() != Coverage.FULL_RECORD)
            throw new IOException("one complete observed record required: " + kind);
        var observations = report.decoded().projection().records().stream()
                .filter(o -> o.kind() == kind && o.id().equals(id) && o.path().equals(path)).toList();
        if (observations.size() != 1 || observations.getFirst().status() != org.xar.ck3.save.SaveContracts.RecordStatus.FULL_RECORD)
            throw new IOException("record was not fully observed: " + kind);
        return selected.getFirst().ast();
    }

    private static String doctrineKey(Clausewitz.Value value) throws IOException {
        if (!(value instanceof Clausewitz.Atom atom) || !atom.token().matches("\"[a-z][a-z0-9_]{0,127}\""))
            throw new IOException("canonical observed doctrine key required");
        return atom.token().substring(1, atom.token().length() - 1);
    }

    private static List<String> currentDoctrines(Clausewitz.Block rite) throws IOException {
        List<String> result = new ArrayList<>();
        for (Clausewitz.Entry entry : walletBlock(rite, "data").named("doctrine")) {
            if (!entry.operator().equals("=")) throw new IOException("observed Rite doctrine assignment required");
            result.add(doctrineKey(entry.value()));
        }
        return uniqueDoctrines(result);
    }

    private static List<String> originDoctrines(Clausewitz.Block rite) throws IOException {
        List<Clausewitz.Block> found = new ArrayList<>();
        for (Clausewitz.Entry entry : walletBlock(walletBlock(rite, "variables"), "list").entries()) {
            if (!entry.key().isEmpty() || !entry.operator().isEmpty() || !(entry.value() instanceof Clausewitz.Block row))
                throw new IOException("observed Rite variable-list framing changed");
            if (row.atom("name", "").equals("\"rrf_origin_doctrines\"")) found.add(row);
        }
        if (found.size() != 1) throw new IOException("one complete origin doctrine list required");
        Clausewitz.Block row = found.getFirst(); List<String> result = new ArrayList<>();
        for (Clausewitz.Entry entry : row.entries()) {
            if (!entry.operator().equals("=") || !List.of("name", "item", "duration").contains(entry.key()))
                throw new IOException("origin doctrine list assignment changed");
            if (!entry.key().equals("item")) continue;
            if (!(entry.value() instanceof Clausewitz.Block item) || item.entries().size() != 2
                    || item.entries().stream().anyMatch(field -> !field.operator().equals("="))
                    || !item.atom("type", "").equals("doctrine") || item.named("key").size() != 1)
                throw new IOException("complete typed origin doctrine item required");
            result.add(doctrineKey(item.named("key").getFirst().value()));
        }
        return uniqueDoctrines(result);
    }

    private static List<String> uniqueDoctrines(List<String> values) throws IOException {
        if (values.isEmpty() || values.size() > 256 || new HashSet<>(values).size() != values.size())
            throw new IOException("unique complete bounded doctrine list required");
        return List.copyOf(values);
    }

    private static DivorceRule divorceRule(List<String> doctrines) throws IOException {
        var found = List.of(DivorceRule.ALLOWED, DivorceRule.DISALLOWED).stream()
                .filter(rule -> doctrines.contains(rule.doctrine())).toList();
        if (found.size() != 1) throw new IOException("one explicit observed divorce rule required");
        return found.getFirst();
    }

    private static String rootAtom(Inspection.Report report, String key) throws IOException {
        var found = report.decoded().projection().rootScalars().stream().filter(e -> e.key().equals(key)).toList();
        if (found.size() != 1 || !(found.getFirst().value() instanceof Clausewitz.Atom atom) || atom.token().isBlank())
            throw new IOException("observed campaign identity required");
        return atom.token();
    }

    private static PietyAmount wallet(Clausewitz.Block actor) throws IOException {
        Clausewitz.Block piety = walletBlock(walletBlock(actor, "alive_data"), "piety");
        if (piety.entries().stream().anyMatch(entry -> !entry.operator().equals("=") || !entry.key().matches("[A-Za-z_][A-Za-z0-9_]*")))
            throw new IOException("observed wallet assignment framing changed");
        var currencies = piety.named("currency");
        // CK3 omits a zero currency inside an existing wallet block. The pinned
        // complete V4 AST remains unchanged in inputPins, including that omission.
        if (currencies.isEmpty()) return new PietyAmount("0");
        if (currencies.size() != 1 || !currencies.getFirst().operator().equals("=")
                || !(currencies.getFirst().value() instanceof Clausewitz.Atom currency))
            throw new IOException("one observed wallet currency atom required");
        return new PietyAmount(currency.token());
    }

    private static Clausewitz.Block walletBlock(Clausewitz.Block parent, String name) throws IOException {
        var entries = parent.named(name);
        if (entries.size() != 1 || !entries.getFirst().operator().equals("=")
                || !(entries.getFirst().value() instanceof Clausewitz.Block block))
            throw new IOException("one existing observed wallet block required: " + name);
        return block;
    }

    private static List<Clausewitz.Block> variables(Clausewitz.Block actor, String name) throws IOException {
        List<Clausewitz.Block> found = new ArrayList<>();
        for (Clausewitz.Entry entry : actor.block("alive_data").block("variables").block("data").entries()) {
            if (!entry.key().isEmpty() || !(entry.value() instanceof Clausewitz.Block row)) throw new IOException("saved variable row framing changed");
            if (row.atom("flag", "").equals("\"" + name + "\"")) found.add(row);
        }
        if (found.size() > 1) throw new IOException("duplicate observed wallet/result variable");
        return List.copyOf(found);
    }

    private static Clausewitz.Block variable(Clausewitz.Block actor, String name, String type) throws IOException {
        List<Clausewitz.Block> found = variables(actor, name);
        if (found.size() != 1 || !found.getFirst().block("data").atom("type", "").equals(type))
            throw new IOException("missing or mistyped observed variable: " + name);
        return found.getFirst().block("data");
    }

    private static PietyAmount valueVariable(Clausewitz.Block actor, String name) throws IOException {
        String raw = variable(actor, name, "value").atom("identity", "");
        return new PietyAmount(new BigDecimal(raw).divide(RAW_SCALE).stripTrailingZeros().toPlainString());
    }

    private static String riteReference(Clausewitz.Block actor, String name) throws IOException {
        return new NativeId(variable(actor, name, "rite").atom("identity", "")).value();
    }

    private static void requireAmount(PietyAmount actual, PietyAmount expected, String label) throws IOException {
        if (!actual.equals(expected)) throw new IOException(label + " differs from the pinned actual observation");
    }
}
