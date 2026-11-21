package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.NativeActionPort.AckReceived;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Strict readonly native getter DATA. Raw CFixedPoint has no asserted scale, display unit or debit meaning. */
public record CurrentDjcSelectedCostResult(Status status,boolean cleanupKnown,BigInteger providerGeneration,
        BigInteger querySequence,Optional<CoreFrame.Prefix> factsBefore,
        Optional<CurrentDjcTargetWarQueryResult.OwnerWitness> ownerWitness,Optional<Source> source,
        Optional<List<Cost>> costs,int nativeGetterCalls,Optional<String> unavailableReason) {
    public enum Status {
        UNAVAILABLE("unavailable"),EXPIRED("expired"),STALE_SOURCE("stale_source"),CLAIM_CONSUMED("claim_consumed"),AVAILABLE("available"),INDETERMINATE("indeterminate");
        private final String wire;Status(String s){wire=s;}public String wire(){return wire;}
        static Status parse(String s)throws IOException {for(var v:values())if(v.wire.equals(s))return v;throw new IOException("Unknown current selected-cost status");}
    }
    public enum Currency {
        PIETY("piety"),PRESTIGE("prestige"),RENOWN("renown"),INFLUENCE("influence"),GOLD("gold");
        private final String wire;Currency(String s){wire=s;}public String wire(){return wire;}
        static Currency parse(String s)throws IOException {for(var v:values())if(v.wire.equals(s))return v;throw new IOException("Unknown fixed native cost currency");}
    }
    public record Cost(Currency currency,String raw) {
        public Cost {
            Objects.requireNonNull(currency);Objects.requireNonNull(raw);
            StrictJson.require(raw.matches("0|[1-9][0-9]{0,18}|-[1-9][0-9]{0,18}"),"Canonical signed64 raw string required; no float, leading zero or negative zero");
            Long.parseLong(raw);
        }
        public String nativeType(){return "CFixedPoint";}
    }
    public record Source(NativeCharacterId target,CurrentDjcTargetWarQueryResult.CasusBelliKey casusBelli,
            NativeCharacterId actor,NativeCharacterId recipient,Optional<NativeCharacterId> additionalRole,
            boolean interactionDefinitionVerified,int loadedInterface,Optional<Boolean> nativeConfirmation,
            boolean residentAvailable,boolean namedRootBound,boolean windowVisible,boolean windowEnabled,
            CurrentDjcDeclarationUiSource.SelectedTuple selected,boolean sourceMatchesPrivateQuery) {
        public Source {
            Objects.requireNonNull(target);Objects.requireNonNull(casusBelli);Objects.requireNonNull(actor);Objects.requireNonNull(recipient);
            Objects.requireNonNull(additionalRole);Objects.requireNonNull(nativeConfirmation);Objects.requireNonNull(selected);
            StrictJson.require(loadedInterface>=0&&loadedInterface<=255,"Actual uint8 loaded interface required");
        }
        /** Compare observation fields only; disabled rows/windows remain valid negative DATA, not action permission. */
        public boolean matches(CurrentDjcDeclarationUiSource original) {
            return target.equals(original.target())&&casusBelli==original.casusBelli()&&original.actor().filter(actor::equals).isPresent()
                    &&original.recipient().filter(recipient::equals).isPresent()&&additionalRole.equals(original.additionalRole())
                    &&interactionDefinitionVerified==original.interactionDefinitionVerified()&&loadedInterface==original.loadedInterface()
                    &&nativeConfirmation.equals(original.nativeConfirmation())&&residentAvailable==original.residentAvailable()
                    &&namedRootBound==original.namedRootBound()&&windowVisible==original.windowVisible()&&windowEnabled==original.windowEnabled()
                    &&original.selected().filter(selected::equals).isPresent()&&sourceMatchesPrivateQuery;
        }
    }
    public CurrentDjcSelectedCostResult {
        Objects.requireNonNull(status);u64(providerGeneration);u64(querySequence);Objects.requireNonNull(factsBefore);Objects.requireNonNull(ownerWitness);
        Objects.requireNonNull(source);Objects.requireNonNull(costs);Objects.requireNonNull(unavailableReason);costs=costs.map(List::copyOf);
        StrictJson.require(nativeGetterCalls>=0&&nativeGetterCalls<=10,"Bounded actual native getter count required");
        StrictJson.require(factsBefore.isPresent()==ownerWitness.isPresent(),"Actual Core and owner must be observed or null together");
        factsBefore.ifPresent(CurrentDjcTargetWarQuery::requirePrefix);
        if(status==Status.AVAILABLE) {
            StrictJson.require(cleanupKnown&&factsBefore.isPresent()&&source.isPresent()&&costs.isPresent()&&providerGeneration.signum()>0&&querySequence.signum()>0
                    &&nativeGetterCalls==10&&unavailableReason.isEmpty(),"Available cost requires complete actual source, echoed private lease, ten getters and known cleanup");
            var s=source.orElseThrow();var p=factsBefore.orElseThrow();
            StrictJson.require(s.interactionDefinitionVerified()&&s.loadedInterface()==4&&s.nativeConfirmation().orElse(false)
                    &&s.residentAvailable()&&s.namedRootBound()&&s.windowVisible()&&s.sourceMatchesPrivateQuery()
                    &&s.actor().value()==p.playedCharacterId()&&s.target().value()!=p.playedCharacterId()&&s.recipient().equals(s.target())
                    &&s.selected().casusBelli()==s.casusBelli(),"Cost requires an actually observed typed declaration and identical selected private source");
            var values=costs.orElseThrow();StrictJson.require(values.size()==5,"All five actual fixed currency values required");
            for(int i=0;i<5;i++)StrictJson.require(values.get(i).currency()==Currency.values()[i],"Exact fixed currency order required; no missing, duplicate or index guessed value");
        } else {
            StrictJson.require(source.isEmpty()&&costs.isEmpty()&&unavailableReason.filter(s->!s.isEmpty()).isPresent(),"A refusal has no source or synthetic zero costs and keeps its actual reason");
        }
    }
    public boolean nativeOk(){return status==Status.AVAILABLE;}
    public static CurrentDjcSelectedCostResult decode(RawJson raw)throws IOException {
        try {
            var r=StrictJson.object(NativeWire.parse(raw.bytes()),Set.of("schema","game_version","executable_sha256","adapter_id","backend","step","action","status","source_available","cleanup_known","provider_generation","query_sequence","claim_sequence","facts_before","owner_witness","source","costs","native_getter_calls","effect_attempted","native_returned","native_handled","formatted_text","addresses_redacted","payment_confirmed","physical_save_confirmed","unavailable_reason"));
            var build=ExactCk3Build.CK3_121003_STEAM_26785313;eq(r,"schema",CurrentDjcSelectedCost.RESULT_SCHEMA);eq(r,"game_version",build.version());eq(r,"executable_sha256",build.executableSha256().toUpperCase(Locale.ROOT));
            eq(r,"adapter_id",build.coreFrameAdapterId());eq(r,"backend",CurrentDjcSelectedCost.BACKEND);eq(r,"step",CurrentDjcSelectedCost.STEP);eq(r,"action",CurrentDjcSelectedCost.ACTION);
            if(bool(r,"effect_attempted")||bool(r,"native_returned")||bool(r,"native_handled")||bool(r,"payment_confirmed")||bool(r,"physical_save_confirmed")||!bool(r,"addresses_redacted")||!r.get("formatted_text").isNull()||decimal(r,"claim_sequence").signum()!=0)
                throw new IOException("A readonly raw getter cannot grant dispatch, payment, display conversion or SAVE");
            Optional<CoreFrame.Prefix> facts=Optional.empty();Optional<CurrentDjcTargetWarQueryResult.OwnerWitness> owner=Optional.empty();Optional<Source> source=Optional.empty();Optional<List<Cost>> costs=Optional.empty();
            if(!r.get("facts_before").isNull()) {var f=StrictJson.object(r.get("facts_before"),Set.of("date_raw","speed","paused","local_player_id","map_ready","has_played_character","played_character_id","played_character_alive"));facts=Optional.of(new CoreFrame.Prefix(i32(f.get("date_raw")),i32(f.get("speed")),bool(f,"paused"),i32(f.get("local_player_id")),bool(f,"map_ready"),bool(f,"has_played_character"),i32(f.get("played_character_id")),bool(f,"played_character_alive")));}
            if(!r.get("owner_witness").isNull()) {var w=StrictJson.object(r.get("owner_witness"),Set.of("connection_generation","ticket_sequence","pump_epoch","thread_id"));owner=Optional.of(new CurrentDjcTargetWarQueryResult.OwnerWitness(decimal(w,"connection_generation"),decimal(w,"ticket_sequence"),decimal(w,"pump_epoch"),NativeWire.integer(w.get("thread_id"),BigInteger.ONE,BigInteger.valueOf(0xffff_ffffL)).longValueExact()));}
            if(!r.get("source").isNull())source=Optional.of(source(r.get("source")));
            if(!r.get("costs").isNull()) {if(!r.get("costs").isArray()||r.get("costs").size()!=5)throw new IOException("Exact five-cost array or null required");var a=new ArrayList<Cost>();for(var rawCost:r.get("costs")){var c=StrictJson.object(rawCost,Set.of("currency","native_type","raw"));eq(c,"native_type","CFixedPoint");a.add(new Cost(Currency.parse(NativeWire.text(c.get("currency"))),NativeWire.text(c.get("raw"))));}costs=Optional.of(List.copyOf(a));}
            if(bool(r,"source_available")!=source.isPresent())throw new IOException("Actual selected-cost source_available/null role differs");
            return new CurrentDjcSelectedCostResult(Status.parse(NativeWire.text(r.get("status"))),bool(r,"cleanup_known"),decimal(r,"provider_generation"),decimal(r,"query_sequence"),facts,owner,source,costs,NativeWire.integer(r.get("native_getter_calls"),BigInteger.ZERO,BigInteger.TEN).intValueExact(),r.get("unavailable_reason").isNull()?Optional.empty():Optional.of(NativeWire.text(r.get("unavailable_reason"))));
        }catch(IllegalArgumentException|ArithmeticException invalid){throw new IOException("Invalid exact current selected-cost DATA",invalid);}
    }
    public static CurrentDjcSelectedCostResult decodeOutcome(AckReceived original)throws IOException {
        try {
            var e=StrictJson.object(NativeWire.parse(original.originalFrame().bytes()),Set.of("type","protocol_version","request_id","ok","result"));eq(e,"type","command_result");eq(e,"request_id",original.requestId());NativeWire.integer(e.get("protocol_version"),BigInteger.ONE,BigInteger.ONE);
            if(bool(e,"ok")!=original.nativeOk())throw new IOException("Selected-cost envelope ok differs from original custody");
            var token=original.originalResultToken().orElseThrow(()->new IOException("Original selected-cost result token required"));if(!NativeWire.parse(token.bytes()).equals(e.get("result")))throw new IOException("Selected-cost token differs from raw envelope");
            var value=decode(new RawJson(token.bytes()));if(value.nativeOk()!=original.nativeOk())throw new IOException("Selected-cost envelope/status differs");return value;
        }catch(IllegalArgumentException invalid){throw new IOException("Invalid original selected-cost envelope",invalid);}
    }
    private static Source source(JsonNode raw)throws IOException {
        var s=StrictJson.object(raw,Set.of("schema","target_character_id","cb_key","actor_id","recipient_id","additional_role_id","interaction_definition_verified","loaded_interface","native_confirmation","resident_available","named_root_bound","window_visible","window_enabled","selected","source_matches_private_query"));eq(s,"schema",CurrentDjcSelectedCost.SOURCE_SCHEMA);
        var t=StrictJson.object(s.get("selected"),Set.of("cb_key","claimant_character_id","target_title_ids","extra_configuration_ids","source_row_enabled"));
        var selected=new CurrentDjcDeclarationUiSource.SelectedTuple(CurrentDjcTargetWarQueryResult.CasusBelliKey.parse(NativeWire.text(t.get("cb_key"))),character(i32(t.get("claimant_character_id"))),ids(t.get("target_title_ids")),ids(t.get("extra_configuration_ids")),bool(t,"source_row_enabled"));
        return new Source(new NativeCharacterId(i32(s.get("target_character_id"))),CurrentDjcTargetWarQueryResult.CasusBelliKey.parse(NativeWire.text(s.get("cb_key"))),new NativeCharacterId(i32(s.get("actor_id"))),new NativeCharacterId(i32(s.get("recipient_id"))),character(i32(s.get("additional_role_id"))),bool(s,"interaction_definition_verified"),i32(s.get("loaded_interface")),s.get("native_confirmation").isNull()?Optional.empty():Optional.of(bool(s,"native_confirmation")),bool(s,"resident_available"),bool(s,"named_root_bound"),bool(s,"window_visible"),bool(s,"window_enabled"),selected,bool(s,"source_matches_private_query"));
    }
    private static Optional<NativeCharacterId> character(int n){return n==-1?Optional.empty():Optional.of(new NativeCharacterId(n));}
    private static List<Integer> ids(JsonNode n)throws IOException {if(!n.isArray()||n.size()>10000)throw new IOException("Bounded ordered signed tuple vector required");var a=new ArrayList<Integer>();for(var x:n)a.add(i32(x));return List.copyOf(a);}
    private static int i32(JsonNode n)throws IOException {return NativeWire.integer(n,BigInteger.valueOf(Integer.MIN_VALUE),BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact();}
    private static BigInteger decimal(ObjectNode n,String k)throws IOException {String s=NativeWire.text(n.get(k));if(!s.matches("0|[1-9][0-9]{0,19}"))throw new IOException("Canonical unsigned64 decimal string required");var v=new BigInteger(s);if(v.compareTo(NativeWire.UINT64_MAX)>0)throw new IOException("Unsigned64 range exceeded");return v;}
    private static void u64(BigInteger n){Objects.requireNonNull(n);StrictJson.require(n.signum()>=0&&n.compareTo(NativeWire.UINT64_MAX)<=0,"Unsigned64 DATA required");}
    private static boolean bool(ObjectNode n,String k)throws IOException {if(!n.get(k).isBoolean())throw new IOException("Actual boolean required: "+k);return n.get(k).booleanValue();}
    private static void eq(ObjectNode n,String k,String v)throws IOException {if(!NativeWire.text(n.get(k)).equals(v))throw new IOException("Exact selected-cost identity differs: "+k);}
}
