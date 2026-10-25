package org.xar.ck3.rrf.save;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.rrf.ExpectedSelection;
import org.xar.ck3.rrf.ExpectedSelection.TenetKey;
import org.xar.ck3.rrf.acceptance.FixtureContracts;
import org.xar.ck3.rrf.acceptance.FrozenFixtureReader.BoundRequest;
import org.xar.ck3.rrf.acceptance.FrozenFixtureReader.PreparedBinding;
import org.xar.ck3.rrf.save.SaveContracts.Atom;
import org.xar.ck3.rrf.save.SaveContracts.Block;
import org.xar.ck3.rrf.save.SaveContracts.Coverage;
import org.xar.ck3.rrf.save.SaveContracts.Entry;
import org.xar.ck3.rrf.save.SaveContracts.NativeId;
import org.xar.ck3.rrf.save.SaveContracts.Pin;
import org.xar.ck3.rrf.save.SaveContracts.Request;
import org.xar.ck3.rrf.save.SaveContracts.Scope;
import org.xar.ck3.rrf.save.SaveContracts.ScopeKind;
import org.xar.ck3.rrf.save.SaveContracts.SelectionVerified;

/** Consumes the existing complete saved AST; never substitutes marker text or native ACKs. */
public final class SavedSelectionComparator {
    private SavedSelectionComparator() { }
    public static SelectionVerified compare(Request request, List<Scope> scopes, BoundRequest fixture, PreparedBinding prepared, NativeId resultId) throws IOException {
        if (fixture.request().kind() == FixtureContracts.CaseKind.UI_REJECTION) throw new IOException("rejection fixture cannot qualify a fusion result");
        Block actor = scope(scopes, ScopeKind.ACTOR, request.selection().actorId());
        NativeId sourceA = reference(block(actor, "alive_data"), "rrfa_source_a", "rite");
        NativeId sourceB = reference(block(actor, "alive_data"), "rrfa_expected_b", "rite");
        if (sourceA.equals(sourceB) || resultId.equals(sourceA) || resultId.equals(sourceB)) throw new IOException("fusion/source Rite identities overlap");
        if (!atom(actor, "rite").equals(resultId.value()) || !reference(block(actor, "alive_data"), "rrf_last_result_rite", "rite").equals(resultId)) throw new IOException("saved actor adoption and last result do not identify the requested same Rite");
        List<TenetKey> a = cores(scope(scopes, ScopeKind.RITE, sourceA));
        List<TenetKey> b = cores(scope(scopes, ScopeKind.RITE, sourceB));
        ExpectedSelection expected = fixture.request().expectedSelection();
        try {
            new ExpectedSelection(FixtureContracts.SOURCE_A).requireExact(a, "saved source A cores");
            new ExpectedSelection(FixtureContracts.SOURCE_B).requireExact(b, "saved source B cores");
            expected.requireSources(a, b);
            Block result = scope(scopes, ScopeKind.RITE, resultId);
            expected.requireExact(cores(result), "saved result cores");
            // The actual R0015 Rite record stores variables beside data; tenets remain inside data.
            expected.requireExact(originCores(result), "saved origin cores");
            if (!reference(result, "rrf_origin_a", "rite").equals(sourceA) || !reference(result, "rrf_origin_b", "rite").equals(sourceB)) throw new IOException("saved immutable source pointers differ");
        } catch (IllegalArgumentException error) { throw new IOException("saved selection comparison failed: " + error.getMessage(), error); }
        return new SelectionVerified(pin(fixture.manifestPin()), pin(fixture.requestPin()), pin(prepared.inventoryPin()), pin(prepared.requestPin()), pin(prepared.caseContractPin()), expected, resultId, sourceA, sourceB);
    }
    private static Pin pin(FixtureContracts.FilePin value) { return new Pin(value.path(), value.bytes(), value.sha256()); }
    private static Block scope(List<Scope> scopes, ScopeKind kind, NativeId id) throws IOException {
        List<Scope> selected = scopes.stream().filter(row -> row.kind() == kind && row.path().getLast().equals(id.value())).toList();
        if (selected.size() != 1 || selected.getFirst().coverage() != Coverage.FULL_RECORD) throw new IOException("complete selected " + kind + " " + id.value() + " required");
        return selected.getFirst().ast();
    }
    private static List<TenetKey> cores(Block rite) throws IOException {
        Block data = block(rite, "data"); List<TenetKey> direct = new ArrayList<>();
        for (Entry entry : data.entries()) if (entry.key().equals("tenet")) direct.add(new TenetKey(text(entry)));
        List<TenetKey> statusCore = new ArrayList<>(), all = new ArrayList<>();
        for (Entry entry : block(data, "tenets").entries()) {
            if (!entry.key().isEmpty() || !(entry.value() instanceof Block row)) throw new IOException("saved tenet status row framing changed");
            TenetKey key = new TenetKey(atom(row, "tenet")); all.add(key);
            String status = atom(row, "status");
            if (!List.of("core", "known", "permitted", "prohibited").contains(status)) throw new IOException("unknown saved tenet status");
            if (status.equals("core")) statusCore.add(key);
        }
        try {
            ExpectedSelection.unique(all, "saved tenet status rows");
            ExpectedSelection.unique(direct, "saved direct core rows");
            if (direct.size() != statusCore.size() || !java.util.Set.copyOf(direct).equals(java.util.Set.copyOf(statusCore))) throw new IOException("saved direct/status core representations disagree");
        } catch (IllegalArgumentException error) { throw new IOException(error.getMessage(), error); }
        return List.copyOf(direct);
    }
    private static NativeId reference(Block owner, String name, String type) throws IOException {
        Block value = variable(owner, name);
        if (!atom(value, "type").equals(type)) throw new IOException("saved reference kind changed: " + name);
        return new NativeId(atom(value, "identity"));
    }
    private static Block variable(Block owner, String name) throws IOException {
        List<Block> matching = new ArrayList<>();
        for (Entry entry : block(block(owner, "variables"), "data").entries()) {
            if (!entry.key().isEmpty() || !(entry.value() instanceof Block row)) throw new IOException("saved variable row framing changed");
            if (atom(row, "flag").equals(name)) matching.add(block(row, "data"));
        }
        if (matching.size() != 1) throw new IOException("saved variable missing or duplicate: " + name);
        return matching.getFirst();
    }
    private static List<TenetKey> originCores(Block owner) throws IOException {
        List<Block> matching = new ArrayList<>();
        for (Entry entry : block(block(owner, "variables"), "list").entries()) {
            if (!entry.key().isEmpty() || !(entry.value() instanceof Block row)) throw new IOException("saved variable-list framing changed");
            if (atom(row, "name").equals("rrf_origin_core_tenets")) matching.add(row);
        }
        if (matching.size() != 1) throw new IOException("saved origin core list missing or duplicate");
        List<TenetKey> result = new ArrayList<>();
        for (Entry entry : matching.getFirst().entries()) if (entry.key().equals("item")) {
            if (!(entry.value() instanceof Block item) || !atom(item, "type").equals("tenet")) throw new IOException("unqualified origin tenet item encoding; retain original AST");
            // R0015's retained completed-create AST has exact type+key entries; native editing was still incomplete.
            if (item.entries().size() != 2 || item.entries().stream().anyMatch(row -> !List.of("type", "key").contains(row.key()))) throw new IOException("unqualified origin item fields");
            result.add(new TenetKey(atom(item, "key")));
        }
        return List.copyOf(result);
    }
    private static Block block(Block parent, String key) throws IOException {
        Entry entry = one(parent, key);
        if (!(entry.value() instanceof Block value)) throw new IOException("saved block required: " + key);
        return value;
    }
    private static String atom(Block parent, String key) throws IOException { return text(one(parent, key)); }
    private static Entry one(Block parent, String key) throws IOException {
        List<Entry> entries = parent.entries().stream().filter(row -> row.key().equals(key)).toList();
        if (entries.size() != 1 || !entries.getFirst().operator().equals("=")) throw new IOException("saved field missing or duplicate: " + key);
        return entries.getFirst();
    }
    private static String text(Entry entry) throws IOException {
        if (!entry.operator().equals("=") || !(entry.value() instanceof Atom value)) throw new IOException("saved assigned atom required: " + entry.key());
        String raw = value.raw();
        if (raw.startsWith("\"") && raw.endsWith("\"") && raw.length() >= 2) raw = raw.substring(1, raw.length() - 1);
        if (raw.isEmpty() || raw.indexOf('\\') >= 0 || raw.indexOf('"') >= 0) throw new IOException("canonical unescaped saved token required");
        return raw;
    }
}
