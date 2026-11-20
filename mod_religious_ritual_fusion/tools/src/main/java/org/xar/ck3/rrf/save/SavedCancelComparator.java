package org.xar.ck3.rrf.save;

import java.io.IOException;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;
import org.xar.ck3.rrf.ExpectedSelection;
import org.xar.ck3.rrf.acceptance.FixtureContracts;
import org.xar.ck3.rrf.acceptance.FrozenFixtureReader.BoundRequest;
import org.xar.ck3.rrf.acceptance.FrozenFixtureReader.PreparedBinding;
import org.xar.ck3.rrf.save.SaveContracts.*;
import org.xar.ck3.save.Clausewitz;
import org.xar.ck3.save.FilePins;
import org.xar.ck3.save.SaveDecoder;

/** Exact physical snapshot comparison, using existing bounded parser/decoder streaming callbacks.
 * Two streams per Save enumerate both native object tables including none slots. No raw melt file. */
public final class SavedCancelComparator {
    private SavedCancelComparator() { }
    private static final Comparator<NativeId> ORDER = Comparator.comparingInt((NativeId n) -> n.value().length()).thenComparing(NativeId::value);
    private static final Set<String> DRAFT_LISTS = Set.of("rrf_candidate_tenets", "rrf_candidate_doctrines", "rrf_selected_tenets", "rrf_selected_doctrines", "rrf_family_converts");
    private static final Set<String> FORBIDDEN = Set.of("rrf_last_result_rite", "rrf_last_result_faith", "rrf_charged_cost", "rrf_fusion_cooldown", "rrf_result_invalid", "rrf_native_setup_active");
    private static final Set<String> DRAFT_VALUES = Set.of("rrf_source_a", "rrf_source_b", "rrf_source_a_faith", "rrf_source_b_faith", "rrf_mode", "rrf_core_count", "rrf_core_limit",
            "rrf_contribution_a", "rrf_contribution_b", "rrf_selection_checked", "rrf_invalid_selection", "rrf_window_dismissed");
    public record Comparison(org.xar.ck3.save.SaveContracts.Decoded after, CancelVerified assessment) { }
    private record ActorRead(CancelActor value, Map<String, Clausewitz.Block> variables, Map<String, Clausewitz.Block> lists) { }
    private record SideRead(org.xar.ck3.save.SaveContracts.Decoded decoded, CancelSide value, ActorRead actor) { }

    public static Comparison inspect(Request request, CancelUnchanged expected, BoundRequest fixture, PreparedBinding prepared,
                                     SaveDecoder.Launcher launcher) throws IOException {
        try { return inspectBounded(request,expected,fixture,prepared,launcher); }
        catch (IllegalArgumentException invalid) { throw new IOException("invalid saved cancellation field: "+invalid.getMessage(),invalid); }
    }
    private static Comparison inspectBounded(Request request, CancelUnchanged expected, BoundRequest fixture, PreparedBinding prepared,
                                             SaveDecoder.Launcher launcher) throws IOException {
        validateSelection(request, expected);
        if (fixture.request().kind() == FixtureContracts.CaseKind.COLD_RELOAD) throw new IOException("fresh cancellation inputs required");
        Path beforePath = Path.of(expected.beforeSave().path()), afterPath = Path.of(request.save().path());
        if (Files.isSameFile(beforePath, afterPath)) throw new IOException("two distinct immutable physical Saves required");
        PhysicalIdentity b0 = physical(beforePath), a0 = physical(afterPath), d0 = physical(Path.of(request.decoder().path()));
        SideRead before = side(request, expected.beforeSave(), expected, fixture, b0, launcher);
        SideRead after = side(request, request.save(), expected, fixture, a0, launcher);
        if (!root(before.decoded(), "playthrough_id").equals(root(after.decoded(), "playthrough_id"))
                || !root(before.decoded(), "date").equals(root(after.decoded(), "date"))) throw new IOException("cancellation Saves differ in campaign/date");
        metadata(before.decoded(), after.decoded());
        var b = before.value().actor(); var a = after.value().actor();
        if (new BigDecimal(b.piety()).compareTo(new BigDecimal(a.piety())) != 0 || !b.actorId().equals(a.actorId())
                || !b.riteId().equals(a.riteId()) || !b.faithId().equals(a.faithId()) || !b.houseId().equals(a.houseId())
                || !b.dynastyId().equals(a.dynastyId()) || !b.state().equals(a.state())) throw new IOException("persistent actor wallet/identity/state changed");
        compareVariables(before.actor().variables(), after.actor().variables());
        List<DraftDifference> draft = compareLists(before.actor().lists(), after.actor().lists());
        if (!before.value().completeInventories().equals(after.value().completeInventories())) throw new IOException("complete Rite/Faith live or tombstone identity set changed");
        if (!before.value().selectedRecords().equals(after.value().selectedRecords())) throw new IOException("selected source/House/Dynasty records changed");
        verify(expected.beforeSave()); verify(request.save()); verify(request.decoder());
        if (!b0.equals(physical(beforePath)) || !a0.equals(physical(afterPath)) || !d0.equals(physical(Path.of(request.decoder().path()))))
            throw new IOException("physical input identity changed across paired inspection");
        String scope = "Same-actor exact Piety/Rite/Faith/House/Dynasty, no result/cooldown, equal closed state, preserved persistent variables and selected source records; complete Rite/Faith live+none slot snapshots. Explicit empty draft-list differences reported. Not whole-actor/world equality or proof about unobserved transient actions.";
        return new Comparison(after.decoded(), new CancelVerified(expected.fixtureManifest(), expected.preparedProfileInventory(), request.decoder(), before.value(), after.value(), draft, true, scope));
    }
    private static void validateSelection(Request request, CancelUnchanged expected) throws IOException {
        if (expected.beforeSave().equals(request.save())) throw new IOException("distinct before/after physical inputs required");
        for (var table : expected.inspectionSelection().tables()) {
            List<NativeId> ids = table.ids().stream().map(n -> new NativeId(n.value())).toList();
            boolean matches = switch (table.kind()) {
                case ACTOR -> table.path().equals(request.layout().actorTable()) && ids.equals(List.of(request.selection().actorId()));
                case RITE -> table.path().equals(request.layout().riteTable()) && Set.copyOf(ids).equals(Set.copyOf(request.selection().riteIds()));
                case FAITH -> table.path().equals(request.layout().faithTable()) && Set.copyOf(ids).equals(Set.copyOf(request.selection().faithIds()));
                case RELIGION -> table.path().equals(request.layout().religionTable()) && Set.copyOf(ids).equals(Set.copyOf(request.selection().religionIds()));
                case HOUSE, DYNASTY -> ids.size() == 1;
                default -> false;
            };
            if (!matches) throw new IOException("new selection crossed original layout/actor/source identities");
        }
    }
    private static SideRead side(Request request, Pin save, CancelUnchanged expected, BoundRequest fixture,
                                 PhysicalIdentity identity, SaveDecoder.Launcher launcher) throws IOException {
        List<ObjectInventory> inventories = new ArrayList<>(); org.xar.ck3.save.SaveContracts.Decoded first = null;
        for (var kind : List.of(org.xar.ck3.save.SaveContracts.ScopeKind.RITE, org.xar.ck3.save.SaveContracts.ScopeKind.FAITH)) {
            var table = expected.inspectionSelection().tables().stream().filter(t -> t.kind() == kind).findFirst().orElseThrow();
            InventorySink sink = new InventorySink();
            var streaming = new org.xar.ck3.save.SaveContracts.StreamingTable(table.path(), kind == org.xar.ck3.save.SaveContracts.ScopeKind.RITE ? "faith" : "religion",
                    List.of(), 200000, 512 * 1024, 64L * 1024 * 1024, true, org.xar.ck3.save.SaveContracts.MissingDiscriminatorPolicy.CAPTURE_MISSING_BOUNDED);
            var decoded = SaveDecoder.inspect(core(save), core(request.decoder()), expected.inspectionSelection(),
                    org.xar.ck3.save.SaveContracts.DecoderLimits.standard(), launcher, streaming, sink);
            var observed = decoded.projection().inventories().stream().filter(i -> i.kind() == kind).findFirst().orElseThrow();
            if (observed.availability() != org.xar.ck3.save.SaveContracts.Availability.OBSERVED || !observed.path().equals(table.path())
                    || !Set.copyOf(observed.ids().stream().map(n -> new NativeId(n.value())).toList()).equals(Set.copyOf(sink.objects)))
                throw new IOException("normal full object inventory and strict streaming enumeration disagree");
            if (first != null && (!first.streamSha256().equals(decoded.streamSha256()) || !first.streamBytes().equals(decoded.streamBytes()))) throw new IOException("same Save produced inconsistent complete decoder streams");
            if (first == null) first = decoded;
            inventories.add(new ObjectInventory(ScopeKind.valueOf(kind.name()), table.path(), sorted(sink.objects), sorted(sink.tombstones)));
        }
        if (first == null) throw new IOException("complete paired object enumeration absent");
        ActorRead actor = actor(request, first, fixture);
        List<RecordStamp> records = new ArrayList<>();
        for (var scope : first.projection().scopes()) if (scope.kind() != org.xar.ck3.save.SaveContracts.ScopeKind.ACTOR && scope.kind() != org.xar.ck3.save.SaveContracts.ScopeKind.METADATA) {
            if (scope.coverage() != org.xar.ck3.save.SaveContracts.Coverage.FULL_RECORD) throw new IOException("full selected source record required");
            records.add(new RecordStamp(ScopeKind.valueOf(scope.kind().name()), new NativeId(scope.path().getLast()), scope.canonicalTokenSha256()));
        }
        records.sort(Comparator.comparing((RecordStamp r) -> r.kind().name()).thenComparing(r -> r.id().value()));
        return new SideRead(first, new CancelSide(save, identity, first.streamSha256(), first.streamBytes(), actor.value(), inventories, records), actor);
    }
    private static final class InventorySink implements org.xar.ck3.save.SaveContracts.StreamingTableSink {
        final Set<NativeId> objects = new java.util.HashSet<>(), tombstones = new java.util.HashSet<>();
        private void add(String value, boolean tombstone) throws IOException {
            NativeId id = new NativeId(value);
            if (objects.contains(id) || tombstones.contains(id)) throw new IOException("duplicate strict native slot identity");
            (tombstone ? tombstones : objects).add(id);
        }
        @Override public void discriminator(org.xar.ck3.save.SaveContracts.NativeId id, String value) throws IOException { new NativeId(value); add(id.value(), false); }
        @Override public void record(org.xar.ck3.save.SaveContracts.StreamedRecord record) throws IOException { if (!objects.contains(new NativeId(record.id().value()))) throw new IOException("unexpected streaming callback without identity"); }
        @Override public void missingDiscriminator(org.xar.ck3.save.SaveContracts.UntypedRecord record) throws IOException { add(record.id().value(), false); }
        @Override public void tombstone(org.xar.ck3.save.SaveContracts.NativeTombstone slot) throws IOException { add(slot.id().value(), true); }
    }
    private static List<NativeId> sorted(Set<NativeId> ids) { return ids.stream().sorted(ORDER).toList(); }
    private static ActorRead actor(Request request, org.xar.ck3.save.SaveContracts.Decoded decoded, BoundRequest fixture) throws IOException {
        NativeId id = request.selection().actorId(); var actorScope = full(decoded, org.xar.ck3.save.SaveContracts.ScopeKind.ACTOR, id); Clausewitz.Block actor = actorScope.ast();
        if (!actor.named("flags").isEmpty() || !block(actor, "alive_data").named("flags").isEmpty() || !actor.named("character_flags").isEmpty()) throw new IOException("unqualified alternate character flag storage");
        Clausewitz.Block alive = block(actor, "alive_data"), vars = block(alive, "variables");
        if (vars.entries().stream().anyMatch(e -> !Set.of("data", "list").contains(e.key()))) throw new IOException("unqualified variable container field");
        Map<String, Clausewitz.Block> values = namedRows(block(vars, "data"), "flag");
        Map<String, Clausewitz.Block> lists = vars.named("list").isEmpty() ? Map.of() : namedRows(block(vars, "list"), "name");
        for (String forbidden : FORBIDDEN) if (values.containsKey(forbidden)) throw new IOException("cancelled baseline contains committed/result/cooldown variable: " + forbidden);
        for (String draft : DRAFT_VALUES) if (values.containsKey(draft)) throw new IOException("final draft is not closed: " + draft);
        for (String list : DRAFT_LISTS) if (lists.containsKey(list) && !lists.get(list).named("item").isEmpty()) throw new IOException("final draft list is not empty: " + list);
        StateValue state = new StateValue(false, "");
        if (values.containsKey("rrf_state")) {
            Clausewitz.Block v = block(values.get("rrf_state"), "data");
            if (!atom(v, "type").equals("flag") || !atom(v, "flag").equals("idle")) throw new IOException("baseline must have explicit closed state; editing/committing/unresolved are not normalized");
            state = new StateValue(true, atom(v, "flag"));
        }
        if (!values.containsKey("rrfa_seed_done") || !block(values.get("rrfa_seed_done"), "data").entries().isEmpty()) throw new IOException("actual fixture seed actor marker required");
        NativeId a = reference(values, "rrfa_source_a", "rite"), b = reference(values, "rrfa_source_b_rite", "rite"), c = reference(values, "rrfa_source_b_faith_rite", "rite");
        if (Set.of(a,b,c).size()!=3 || !Set.of(a,b,c).equals(Set.copyOf(request.selection().riteIds()))) throw new IOException("all three distinct source Rite records must be selected");
        NativeId af = reference(values, "rrfa_source_a_faith", "faith"), bf = reference(values, "rrfa_source_b_faith", "faith");
        if (af.equals(bf) || !Set.of(af,bf).equals(Set.copyOf(request.selection().faithIds()))) throw new IOException("both exact source Faiths required");
        NativeId rite = nativeAtom(actor,"rite"), house = nativeAtom(actor,"dynasty_house");
        if (!rite.equals(a)) throw new IOException("actor no longer follows original source A");
        var ar = full(decoded,org.xar.ck3.save.SaveContracts.ScopeKind.RITE,a).ast();
        var br = full(decoded,org.xar.ck3.save.SaveContracts.ScopeKind.RITE,b).ast();
        var cr = full(decoded,org.xar.ck3.save.SaveContracts.ScopeKind.RITE,c).ast();
        if (!nativeAtom(ar,"faith").equals(af) || !nativeAtom(br,"faith").equals(af) || !nativeAtom(cr,"faith").equals(bf)) throw new IOException("source Rite/Faith pointers changed");
        for (var pair : List.of(Map.entry(ar,FixtureContracts.SOURCE_A),Map.entry(br,FixtureContracts.SOURCE_B),Map.entry(cr,FixtureContracts.SOURCE_B))) {
            var wrapped = SaveStream.fromShared(pair.getKey());
            try { new ExpectedSelection(pair.getValue()).requireExact(SavedSelectionComparator.cores(wrapped),"cancel source cores"); } catch (IllegalArgumentException ex) { throw new IOException(ex.getMessage(),ex); }
        }
        var faithA = full(decoded,org.xar.ck3.save.SaveContracts.ScopeKind.FAITH,af).ast(); var faithB = full(decoded,org.xar.ck3.save.SaveContracts.ScopeKind.FAITH,bf).ast();
        NativeId religion=nativeAtom(faithA,"religion");
        if (!nativeAtom(faithB,"religion").equals(religion) || !nativeAtom(faithB,"main_rite").equals(c) || !request.selection().religionIds().equals(List.of(religion))) throw new IOException("source Faith/religion contract differs");
        full(decoded,org.xar.ck3.save.SaveContracts.ScopeKind.RELIGION,religion);
        var houseRecord=full(decoded,org.xar.ck3.save.SaveContracts.ScopeKind.HOUSE,house).ast();NativeId dynasty=nativeAtom(houseRecord,"dynasty");full(decoded,org.xar.ck3.save.SaveContracts.ScopeKind.DYNASTY,dynasty);
        if (!actor.named("faith").isEmpty() && !nativeAtom(actor,"faith").equals(af) || !actor.named("dynasty").isEmpty() && !nativeAtom(actor,"dynasty").equals(dynasty)) throw new IOException("direct actor identity disagrees with actual Rite/House records");
        Clausewitz.Block modeValue=block(required(values,"rrfa_mode"),"data");
        if(!atom(modeValue,"type").equals("flag"))throw new IOException("actual fixture mode must be a flag");
        String mode=atom(modeValue,"flag");
        if (!mode.equals(fixture.request().mode().wire())) throw new IOException("saved fixture mode differs");
        NativeId expectedB=reference(values,"rrfa_expected_b","rite");if (!expectedB.equals(mode.equals("rite")?b:c)) throw new IOException("saved fixture source B differs");
        Clausewitz.Block piety=block(alive,"piety");String amount=rawAtom(piety,"currency");
        if (!amount.matches("-?(?:0|[1-9][0-9]{0,15})(?:\\.[0-9]{1,8})?") || amount.startsWith("-") && new BigDecimal(amount).signum()==0) throw new IOException("exact bounded decimal Piety required");
        return new ActorRead(new CancelActor(id,amount,rite,af,house,dynasty,state,actorScope.canonicalTokenSha256()),values,lists);
    }
    private static Map<String,Clausewitz.Block> namedRows(Clausewitz.Block container,String field) throws IOException {
        Map<String,Clausewitz.Block> result=new TreeMap<>();
        for(var e:container.entries()) {
            if (!e.key().isEmpty() || !(e.value() instanceof Clausewitz.Block row)) throw new IOException("anonymous saved variable row required");
            String key=atom(row,field);if(result.putIfAbsent(key,row)!=null)throw new IOException("duplicate saved variable/list: "+key);
            if(field.equals("flag")) {
                block(row,"data");if(row.entries().stream().anyMatch(v->!Set.of("flag","tick","data").contains(v.key())))throw new IOException("unqualified saved variable row fields");
                if(!row.named("tick").isEmpty()&&!rawAtom(row,"tick").matches("-?(?:0|[1-9][0-9]{0,18})"))throw new IOException("canonical variable tick required");
            } else if(DRAFT_LISTS.contains(key)) {
                if(row.entries().stream().anyMatch(v->!Set.of("name","item","duration").contains(v.key())))throw new IOException("unqualified empty draft-list field");
                if(!row.named("duration").isEmpty())for(var v:block(row,"duration").entries())
                    if(!v.key().isEmpty()||!v.operator().isEmpty()||!(v.value() instanceof Clausewitz.Atom token)||!token.token().matches("-?(?:0|[1-9][0-9]{0,18})"))throw new IOException("unqualified draft-list duration");
            }
        }
        return result;
    }
    private static void compareVariables(Map<String,Clausewitz.Block> b,Map<String,Clausewitz.Block> a)throws IOException { if(!hashes(b).equals(hashes(a)))throw new IOException("persistent saved variables changed"); }
    private static List<DraftDifference> compareLists(Map<String,Clausewitz.Block> b,Map<String,Clausewitz.Block> a)throws IOException {
        List<DraftDifference> result=new ArrayList<>();Set<String> keys=new TreeSet<>();keys.addAll(b.keySet());keys.addAll(a.keySet());
        for(String key:keys){FieldStamp x=stamp(b.get(key)),y=stamp(a.get(key));if(!x.equals(y)){if(!DRAFT_LISTS.contains(key))throw new IOException("persistent saved list changed: "+key);result.add(new DraftDifference("explicit-empty-draft-list",key,x,y));}}
        return List.copyOf(result);
    }
    private static Map<String,String> hashes(Map<String,Clausewitz.Block> rows){Map<String,String> r=new TreeMap<>();rows.forEach((k,v)->r.put(k,stamp(v).sha256()));return r;}
    private static FieldStamp stamp(Clausewitz.Block b){return b==null?new FieldStamp(false,""):new FieldStamp(true,FilePins.sha256(b.render().getBytes(StandardCharsets.UTF_8)));}
    private static Clausewitz.Block required(Map<String,Clausewitz.Block> m,String key)throws IOException {var r=m.get(key);if(r==null)throw new IOException("missing actual fixture variable: "+key);return r;}
    private static NativeId reference(Map<String,Clausewitz.Block> m,String key,String type)throws IOException {var b=block(required(m,key),"data");if(!atom(b,"type").equals(type))throw new IOException("mistyped source reference: "+key);return nativeAtom(b,"identity");}
    private static NativeId nativeAtom(Clausewitz.Block b,String key)throws IOException {String raw=rawAtom(b,key);try{return new NativeId(raw);}catch(IllegalArgumentException ex){throw new IOException("canonical numeric reference required: "+key,ex);}}
    private static Clausewitz.Entry one(Clausewitz.Block b,String key)throws IOException {var e=b.named(key);if(e.size()!=1||!e.getFirst().operator().equals("="))throw new IOException("one assigned field required: "+key);return e.getFirst();}
    private static Clausewitz.Block block(Clausewitz.Block b,String key)throws IOException {var e=one(b,key);if(!(e.value() instanceof Clausewitz.Block c))throw new IOException("block field required: "+key);return c;}
    private static String rawAtom(Clausewitz.Block b,String key)throws IOException {var e=one(b,key);if(!(e.value() instanceof Clausewitz.Atom a))throw new IOException("atom field required: "+key);return a.token();}
    private static String atom(Clausewitz.Block b,String key)throws IOException {String s=rawAtom(b,key);if(s.startsWith("\"")&&s.endsWith("\""))s=s.substring(1,s.length()-1);if(s.isEmpty()||s.contains("\\")||s.contains("\""))throw new IOException("canonical saved token required: "+key);return s;}
    private static org.xar.ck3.save.SaveContracts.Scope full(org.xar.ck3.save.SaveContracts.Decoded d,org.xar.ck3.save.SaveContracts.ScopeKind kind,NativeId id)throws IOException {
        var rows=d.projection().scopes().stream().filter(s->s.kind()==kind&&s.path().getLast().equals(id.value())).toList();
        var observations=d.projection().records().stream().filter(r->r.kind()==kind&&r.id().value().equals(id.value())&&r.status()==org.xar.ck3.save.SaveContracts.RecordStatus.FULL_RECORD).toList();
        if(rows.size()!=1||observations.size()!=1||rows.getFirst().coverage()!=org.xar.ck3.save.SaveContracts.Coverage.FULL_RECORD)throw new IOException("complete observed selected "+kind+" "+id.value()+" required");return rows.getFirst();
    }
    private static String root(org.xar.ck3.save.SaveContracts.Decoded d,String key)throws IOException{return atom(new Clausewitz.Block(d.projection().rootScalars()),key);}
    private static void metadata(org.xar.ck3.save.SaveContracts.Decoded b,org.xar.ck3.save.SaveContracts.Decoded a)throws IOException {
        var x=b.projection().scopes().stream().filter(s->s.kind()==org.xar.ck3.save.SaveContracts.ScopeKind.METADATA).toList();var y=a.projection().scopes().stream().filter(s->s.kind()==org.xar.ck3.save.SaveContracts.ScopeKind.METADATA).toList();
        if(x.size()!=1||y.size()!=1||!atom(x.getFirst().ast(),"version").equals(atom(y.getFirst().ast(),"version")))throw new IOException("same actual saved game version metadata required");
    }
    private static org.xar.ck3.save.SaveContracts.Pin core(Pin p){return new org.xar.ck3.save.SaveContracts.Pin(p.path(),p.bytes(),p.sha256());}
    private static void verify(Pin p)throws IOException{FilePins.verify(Path.of(p.path()),core(p));}
    private static PhysicalIdentity physical(Path p)throws IOException {return SavedFileIdentity.read(p);}
}
