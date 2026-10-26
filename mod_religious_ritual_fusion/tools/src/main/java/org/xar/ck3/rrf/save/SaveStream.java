package org.xar.ck3.rrf.save;

import java.io.IOException;
import java.io.Reader;
import java.util.List;
import org.xar.ck3.rrf.save.SaveContracts.*;

/** Explicit v2 adapter. Parsing and bounded selection live exclusively in ck3-save-core. */
public final class SaveStream {
    private final org.xar.ck3.save.SaveStream stream;
    public SaveStream(Reader reader, Request request) {
        stream = new org.xar.ck3.save.SaveStream(reader, selection(request));
    }
    public record Projection(List<Inventory> inventories, List<Scope> scopes, List<String> rootKeys,
                             List<Entry> rootScalars, long tokens, int selectedTokenBytes) { }
    public Projection read() throws IOException { return fromShared(stream.read()); }
    public static org.xar.ck3.save.SaveContracts.Selection selection(Request request) {
        return new org.xar.ck3.save.SaveContracts.Selection(List.of(
                table(org.xar.ck3.save.SaveContracts.ScopeKind.ACTOR, request.layout().actorTable(), List.of(request.selection().actorId())),
                table(org.xar.ck3.save.SaveContracts.ScopeKind.RITE, request.layout().riteTable(), request.selection().riteIds()),
                table(org.xar.ck3.save.SaveContracts.ScopeKind.FAITH, request.layout().faithTable(), request.selection().faithIds()),
                table(org.xar.ck3.save.SaveContracts.ScopeKind.RELIGION, request.layout().religionTable(), request.selection().religionIds())),
                List.of(), true, false, List.of());
    }
    private static org.xar.ck3.save.SaveContracts.TableSelection table(org.xar.ck3.save.SaveContracts.ScopeKind kind, List<String> path, List<NativeId> ids) {
        return new org.xar.ck3.save.SaveContracts.TableSelection(kind, path,
                ids.stream().map(id -> new org.xar.ck3.save.SaveContracts.NativeId(id.value())).toList(), true);
    }
    public static Projection fromShared(org.xar.ck3.save.SaveContracts.Projection projection) {
        return new Projection(projection.inventories().stream()
                .filter(i -> i.availability() == org.xar.ck3.save.SaveContracts.Availability.OBSERVED && i.kind() != org.xar.ck3.save.SaveContracts.ScopeKind.ACTOR)
                .map(i -> new Inventory(ScopeKind.valueOf(i.kind().name()), i.path(), i.ids().stream().map(id -> new NativeId(id.value())).toList())).toList(),
                projection.scopes().stream().map(s -> new Scope(ScopeKind.valueOf(s.kind().name()), Coverage.valueOf(s.coverage().name()), s.path(), s.canonicalTokenSha256(), fromShared(s.ast()))).toList(),
                projection.rootKeys(), projection.rootScalars().stream().map(SaveStream::fromShared).toList(), projection.tokens(), projection.selectedTokenBytes());
    }
    private static Entry fromShared(org.xar.ck3.save.Clausewitz.Entry entry) {
        return new Entry(entry.key(), entry.operator(), entry.value() instanceof org.xar.ck3.save.Clausewitz.Block block
                ? fromShared(block) : new Atom(((org.xar.ck3.save.Clausewitz.Atom) entry.value()).token()));
    }
    private static Block fromShared(org.xar.ck3.save.Clausewitz.Block block) {
        return new Block(block.entries().stream().map(SaveStream::fromShared).toList());
    }
}
