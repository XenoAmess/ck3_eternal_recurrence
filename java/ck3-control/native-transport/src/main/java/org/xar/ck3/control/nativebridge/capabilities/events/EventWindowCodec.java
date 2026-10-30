package org.xar.ck3.control.nativebridge.capabilities.events;

import static org.xar.ck3.control.nativebridge.capabilities.events.EventWindowModels.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.contracts.events.GuiAvailabilityObservation;

/** Full original event_window_context_contract boundary. Trees never escape into the typed model. */
public final class EventWindowCodec {
    private static final BigInteger U64=new BigInteger("18446744073709551615");
    private static final Readiness READY=new Readiness(true,true,true,true,true,false,false);
    private static final Readiness NONE=new Readiness(false,false,false,false,false,false,false);
    private static final Readiness PARTIAL=new Readiness(true,false,false,false,false,false,false);
    private EventWindowCodec() { }

    public static Context decode(RawJson original, Binding expected) {
        ObjectNode f=parse(original);
        exact(f,"schema schema_version status snapshot_revision date_raw current_event_instance_id window_match_count unavailable_reason event_definition_key calculated_event_id runtime_stats_ordinal root_scope saved_scopes options readiness provenance");
        int schemaVersion=integer(f,"schema_version",1,2);
        eq(f,"schema",schemaVersion==1?"current-event-window-context-v1":"current-event-window-context-v2");
        BigInteger revision=number(f,"snapshot_revision",BigInteger.ONE,U64);
        int date=i32(f,"date_raw"), event=integer(f,"current_event_instance_id",1,Integer.MAX_VALUE);
        need(revision.equals(expected.nativeRevision()) && date==expected.dateRaw() && event==expected.eventInstanceId(),"event-window exact frame changed");
        int matches=integer(f,"window_match_count",0,32);
        Readiness readiness=readiness(field(f,"readiness"));
        Build build=provenance(field(f,"provenance")); need(build==expected.build(),"event-window locator belongs to another connected exact build");
        String status=text(f,"status"); need(status.equals("available") || status.equals("unavailable"),"event-window status differs");
        if (status.equals("unavailable")) {
            String reason=nonempty(f,"unavailable_reason"); Optional<Definition> partial=Optional.empty();
            if (reason.equals("event_saved_scope_invalid") && readiness.definitionIdentity()) {
                need(readiness.equals(PARTIAL) && matches==0,"partial event identity gained actionable readiness");
                partial=Optional.of(definition(f));
            } else {
                need(readiness.equals(NONE),"unavailable event readiness is actionable");
                nil(f,"event_definition_key"); nil(f,"calculated_event_id"); nil(f,"runtime_stats_ordinal");
            }
            nil(f,"root_scope"); nil(f,"saved_scopes"); nil(f,"options");
            return new Unavailable(expected,matches,reason,partial,readiness,original);
        }
        nil(f,"unavailable_reason"); need(matches==1 && readiness.equals(READY),"available event needs one match and indicator-only readiness");
        Definition definition=definition(f); Scope root=scope(field(f,"root_scope"),build,false,false);
        List<SavedScope> saved=new ArrayList<>(); Set<String> names=new HashSet<>(); Set<Integer> identifiers=new HashSet<>();
        for (JsonNode raw:array(f,"saved_scopes",1024)) {
            exact(raw,"name name_identifier scope"); String name=stable(raw,"name"); int identifier=i32(raw,"name_identifier");
            need(names.add(name) && identifiers.add(identifier),"saved scope names/identifiers must be unique");
            saved.add(new SavedScope(name,identifier,scope(field(raw,"scope"),build,true,build.numericScopes())));
        }
        List<Option> options=new ArrayList<>(); Set<Integer> nativeIndices=new HashSet<>();
        for (JsonNode raw:array(f,"options",64)) {
            exact(raw,"rendered_index native_option_index shown enabled fallback cancel resolved_name unavailable_reason effect_indicators effect_preview resource_deltas relationship_deltas"+(schemaVersion==2?" gui_availability":""));
            int rendered=integer(raw,"rendered_index",0,Integer.MAX_VALUE), nativeIndex=integer(raw,"native_option_index",0,Integer.MAX_VALUE);
            need(rendered==options.size() && nativeIndices.add(nativeIndex),"event display order/native index uniqueness changed"); yes(raw,"shown");
            JsonNode indicators=field(raw,"effect_indicators"); exact(indicators,"status coverage complete_effect_set rows");
            eq(indicators,"status","available"); eq(indicators,"coverage",build.coverage()); no(indicators,"complete_effect_set");
            List<Indicator> copied=new ArrayList<>(); for (JsonNode row:array(indicators,"rows",128)) copied.add(indicator(row,build));
            JsonNode preview=field(raw,"effect_preview"); exact(preview,"status reason"); eq(preview,"status","unavailable"); eq(preview,"reason","indicator_subset_has_no_completeness_signal");
            for (String key:List.of("resource_deltas","relationship_deltas")) { JsonNode unavailable=field(raw,key); exact(unavailable,"status"); eq(unavailable,"status","unavailable"); }
            options.add(new Option(rendered,nativeIndex,bool(raw,"enabled"),bool(raw,"fallback"),bool(raw,"cancel"),text(raw,"resolved_name"),text(raw,"unavailable_reason"),copied,guiAvailability(raw,schemaVersion)));
        }
        return new Available(expected,definition,root,saved,options,readiness,original);
    }

    /** Retain the validated JSON type domain and original decimal strings byte-for-byte. */
    public static RawJson encode(Context context) { return java.util.Objects.requireNonNull(context).original(); }

    private static GuiAvailabilityObservation guiAvailability(JsonNode row,int schemaVersion) {
        if (schemaVersion==1) return new GuiAvailabilityObservation.LegacyNotReported();
        JsonNode observation=field(row,"gui_availability");
        String status=text(observation,"status");
        if (status.equals("observed")) {
            exact(observation,"status is_valid");
            return new GuiAvailabilityObservation.Observed(bool(observation,"is_valid"));
        }
        need(status.equals("unobserved"),"GUI observation status differs");
        exact(observation,"status reason");
        return new GuiAvailabilityObservation.Unobserved(GuiAvailabilityObservation.Reason.fromWire(text(observation,"reason")));
    }

    private static Definition definition(JsonNode f) { return new Definition(stable(f,"event_definition_key"),i32(f,"calculated_event_id"),i32(f,"runtime_stats_ordinal")); }
    private static Readiness readiness(JsonNode r) {
        exact(r,"event_definition_identity_ready root_scope_ready saved_scopes_ready option_presentation_ready effect_indicators_ready effect_preview_ready semantic_decision_ready");
        return new Readiness(bool(r,"event_definition_identity_ready"),bool(r,"root_scope_ready"),bool(r,"saved_scopes_ready"),bool(r,"option_presentation_ready"),bool(r,"effect_indicators_ready"),bool(r,"effect_preview_ready"),bool(r,"semantic_decision_ready"));
    }
    private static Build provenance(JsonNode p) {
        exact(p,"root idler_vtable_rva manager_offset backend_id"); String backend=nonempty(p,"backend_id");
        for (Build build:Build.values()) if (build.backend().equals(backend)) {
            eq(p,"root",build.root()); eq(p,"idler_vtable_rva",build.vtable()); eq(p,"manager_offset","+0x28"); return build;
        }
        throw new IllegalArgumentException("unknown exact-build event locator");
    }
    private static Scope scope(JsonNode s, Build build, boolean allowUnavailableCharacter, boolean allowNullCharacter) {
        boolean hasNumeric=s!=null && s.isObject() && s.has("numeric_value");
        need(!hasNumeric || build.numericScopes(),"numeric event scope not supported by this build");
        exact(s,"status raw_type_index type_key subtype typed_identity"+(hasNumeric?" numeric_value":"")); eq(s,"status","available");
        int raw=integer(s,"raw_type_index",1,65535), subtype=integer(s,"subtype",0,65535); String key=stable(s,"type_key");
        Optional<NumericValue> numeric=Optional.empty();
        if (hasNumeric) { need(raw==1 && key.equals("value") && subtype==0,"numeric scope type/subtype differs"); numeric=Optional.of(numeric(field(s,"numeric_value"))); }
        JsonNode identity=field(s,"typed_identity"); Identity typed;
        if (raw==25 && key.equals("faction")) {
            if (isStatus(identity,"available")) { exact(identity,"status kind faction_id"); eq(identity,"kind","faction"); typed=new FactionIdentity(integer(identity,"faction_id",1,Integer.MAX_VALUE)); }
            else typed=unavailable(identity,Set.of(IdentityReason.FACTION_SCOPE_IDENTITY_UNAVAILABLE,IdentityReason.GENERIC_SCOPE_PAYLOAD_IDENTITY_NOT_CLOSED));
        } else if (raw==5 && key.equals("landed_title")) {
            if (isStatus(identity,"available")) { exact(identity,"status kind title_id"); eq(identity,"kind","landed_title"); int id=i32(identity,"title_id"); need(id!=-1,"title null FullRef cannot become an identity"); typed=new TitleIdentity(id); }
            else typed=unavailable(identity,allowNullCharacter?Set.of(IdentityReason.GENERIC_SCOPE_PAYLOAD_IDENTITY_NOT_CLOSED,IdentityReason.LANDED_TITLE_SCOPE_IS_NULL):Set.of(IdentityReason.GENERIC_SCOPE_PAYLOAD_IDENTITY_NOT_CLOSED));
        } else if (raw==4) {
            need(key.equals("character"),"character scope type key drifted");
            if (isStatus(identity,"unavailable")) {
                need(allowUnavailableCharacter,"root character identity cannot be unavailable");
                typed=unavailable(identity,allowNullCharacter?Set.of(IdentityReason.CHARACTER_SCOPE_IDENTITY_UNAVAILABLE,IdentityReason.CHARACTER_SCOPE_IS_NULL):Set.of(IdentityReason.CHARACTER_SCOPE_IDENTITY_UNAVAILABLE));
            } else { exact(identity,"status kind character_id"); eq(identity,"status","available"); eq(identity,"kind","character"); typed=new CharacterIdentity(integer(identity,"character_id",1,Integer.MAX_VALUE)); }
        } else {
            need(!key.equals("character"),"generic scope aliases the character index");
            typed=unavailable(identity,Set.of(IdentityReason.GENERIC_SCOPE_PAYLOAD_IDENTITY_NOT_CLOSED));
        }
        return new Scope(raw,key,subtype,typed,numeric);
    }
    private static UnavailableIdentity unavailable(JsonNode value,Set<IdentityReason> allowed) {
        exact(value,"status reason"); eq(value,"status","unavailable"); String reason=text(value,"reason");
        for (IdentityReason candidate:allowed) if (candidate.wire().equals(reason)) return new UnavailableIdentity(candidate);
        throw new IllegalArgumentException("scope identity unavailable reason differs");
    }
    private static NumericValue numeric(JsonNode n) {
        exact(n,"raw_fixed_point scale decimal_value integer_value"); String raw=text(n,"raw_fixed_point");
        need(raw.length()>=1 && raw.length()<=20 && raw.matches("-?(0|[1-9][0-9]*)"),"canonical signed64 fixed-point string required");
        BigInteger value=new BigInteger(raw); need(value.toString().equals(raw) && value.bitLength()<=63,"numeric scope signed64 string outside range"); integer(n,"scale",100000,100000);
        BigInteger[] qr=value.abs().divideAndRemainder(BigInteger.valueOf(100000)); String decimal=(value.signum()<0?"-":"")+qr[0];
        if (qr[1].signum()!=0) decimal+="."+String.format(java.util.Locale.ROOT,"%05d",qr[1].intValueExact()).replaceAll("0+$","");
        need(text(n,"decimal_value").equals(decimal),"numeric scope exact decimal differs"); Optional<String> integer=Optional.empty();
        if (qr[1].signum()==0) { String expected=value.divide(BigInteger.valueOf(100000)).toString(); need(text(n,"integer_value").equals(expected),"numeric scope integer differs"); integer=Optional.of(expected); }
        else nil(n,"integer_value");
        return new NumericValue(raw,decimal,integer);
    }
    private static Indicator indicator(JsonNode row,Build build) {
        String kind=text(row,"kind");
        switch (kind) {
            case "trait": {
                exact(row,"kind operation trait"); String op=text(row,"operation"); need(op.equals("add") || op.equals("remove"),"trait operation differs");
                JsonNode t=field(row,"trait"); TraitIdentity trait;
                if (isStatus(t,"available")) { exact(t,"status native_id key"); trait=new KnownTrait(integer(t,"native_id",0,Integer.MAX_VALUE),stable(t,"key")); }
                else { exact(t,"status reason"); eq(t,"status","unavailable"); eq(t,"reason","trait_identity_unavailable"); trait=new UnavailableTrait(); }
                return new TraitIndicator(op.equals("add")?Operation.ADD:Operation.REMOVE,trait);
            }
            case "stress", "fulfillment", "stress_and_fulfillment": {
                need(kind.equals("stress") || build!=Build.TOURS,"fulfillment icon does not belong to this build");
                boolean both=kind.equals("stress_and_fulfillment"); exact(row,"kind direction magnitude affected_by_trait critical"+(both?" secondary_direction":""));
                JsonNode magnitude=field(row,"magnitude"); exact(magnitude,"status"); eq(magnitude,"status","unavailable");
                boolean affected=bool(row,"affected_by_trait"), critical=bool(row,"critical");
                need(!kind.equals("fulfillment") || (!affected && !critical),"fulfillment cannot acquire stress flags");
                StressKind type=kind.equals("stress")?StressKind.STRESS:both?StressKind.STRESS_AND_FULFILLMENT:StressKind.FULFILLMENT;
                return new StressIndicator(type,direction(row,"direction"),both?Optional.of(direction(row,"secondary_direction")):Optional.empty(),affected,critical);
            }
            case "death": exact(row,"kind subject direction"); eq(row,"subject","played_character"); eq(row,"direction","not_applicable"); return new DeathIndicator();
            case "scheme": {
                exact(row,"kind subject operation direction scheme"); eq(row,"subject","played_character"); eq(row,"operation","start"); eq(row,"direction","not_applicable");
                JsonNode s=field(row,"scheme"); SchemeIdentity scheme;
                if (isStatus(s,"available")) { exact(s,"status scheme_type_key"); scheme=new KnownScheme(stable(s,"scheme_type_key")); }
                else { exact(s,"status reason"); eq(s,"status","unavailable"); eq(s,"reason","scheme_type_identity_unavailable"); scheme=new UnavailableScheme(); }
                return new SchemeIndicator(scheme);
            }
            case "unknown": {
                exact(row,"kind raw_kind"); int raw=i32(row,"raw_kind"); need(raw<0 || raw>(build==Build.TOURS?3:5),"unknown event icon aliases a known kind"); return new UnknownIndicator(raw);
            }
            default: throw new IllegalArgumentException("event icon kind differs");
        }
    }
    private static Direction direction(JsonNode row,String key) { String value=text(row,key); need(value.equals("increase") || value.equals("decrease"),"icon direction differs"); return value.equals("increase")?Direction.INCREASE:Direction.DECREASE; }
    private static boolean isStatus(JsonNode row,String value) { return row!=null && row.isObject() && row.has("status") && row.get("status").isTextual() && row.get("status").textValue().equals(value); }
    static ObjectNode parse(RawJson raw) { try { return NativeWire.object(NativeWire.parse(raw.bytes())); } catch (IOException error) { throw new IllegalArgumentException("malformed event JSON",error); } }
    static void need(boolean condition,String reason) { if (!condition) throw new IllegalArgumentException(reason); }
    static JsonNode field(JsonNode row,String key) { need(row!=null && row.isObject() && row.has(key),"missing event field: "+key); return row.get(key); }
    static void exact(JsonNode row,String fields) { need(row!=null && row.isObject(),"event object required"); Set<String> actual=new HashSet<>(); row.fieldNames().forEachRemaining(actual::add); need(actual.equals(Set.of(fields.split(" +"))),"event fields differ: "+actual); }
    static String text(JsonNode row,String key) { JsonNode n=field(row,key); need(n.isTextual(),"event string required: "+key); return n.textValue(); }
    static String nonempty(JsonNode row,String key) { String value=text(row,key); need(!value.isEmpty(),"nonempty event string required: "+key); return value; }
    static String stable(JsonNode row,String key) { String value=nonempty(row,key); need(value.getBytes(java.nio.charset.StandardCharsets.UTF_8).length<=16384,"event stable key exceeds UTF-8 bound"); return value; }
    static void eq(JsonNode row,String key,String expected) { need(text(row,key).equals(expected),"event constant differs: "+key); }
    static boolean bool(JsonNode row,String key) { JsonNode n=field(row,key); need(n.isBoolean(),"event boolean required: "+key); return n.booleanValue(); }
    static void yes(JsonNode row,String key) { need(bool(row,key),"event true required: "+key); }
    static void no(JsonNode row,String key) { need(!bool(row,key),"event false required: "+key); }
    static void nil(JsonNode row,String key) { need(field(row,key).isNull(),"event unobserved field must remain null: "+key); }
    static BigInteger number(JsonNode row,String key,BigInteger minimum,BigInteger maximum) { JsonNode n=field(row,key); need(n.isIntegralNumber(),"event integer required, refusing bool/float: "+key); BigInteger v=n.bigIntegerValue(); need(v.compareTo(minimum)>=0 && v.compareTo(maximum)<=0,"event integer out of range: "+key); return v; }
    static int integer(JsonNode row,String key,int minimum,int maximum) { return number(row,key,BigInteger.valueOf(minimum),BigInteger.valueOf(maximum)).intValueExact(); }
    static int i32(JsonNode row,String key) { return integer(row,key,Integer.MIN_VALUE,Integer.MAX_VALUE); }
    static List<JsonNode> array(JsonNode row,String key,int maximum) { JsonNode n=field(row,key); need(n.isArray() && n.size()<=maximum,"bounded event array required: "+key); List<JsonNode> items=new ArrayList<>(); n.forEach(items::add); return items; }
}
