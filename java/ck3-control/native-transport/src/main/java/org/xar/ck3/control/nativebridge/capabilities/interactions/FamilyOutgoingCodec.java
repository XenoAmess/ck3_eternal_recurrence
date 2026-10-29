package org.xar.ck3.control.nativebridge.capabilities.interactions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.OptionalInt;
import java.util.OptionalLong;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.StrictJson;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;

/** Sole complete actual4 outgoing-storage value codec. Values alone grant no read, submission or settlement authority. */
public final class FamilyOutgoingCodec {
    public static final String GROUP="family_outgoing_requests";
    /** v4 binds the actual native actor-shadow constructor/copy profile; v3 is never an alias. */
    public static final String SCHEMA="ck3-family-outgoing-storage-12004-v4";
    private FamilyOutgoingCodec() { }
    public enum Profile {
        EDUCATE_CHILD("educate_child_interaction"), ARRANGE_MARRIAGE("arrange_marriage_interaction");
        private final String key;Profile(String key){this.key=key;}public String interactionKey(){return key;}
        public static Profile fromKey(String key){for(var value:values())if(value.key.equals(key))return value;throw new IllegalArgumentException("unsupported outgoing definition");}
    }
    /** Sender is the actual storage filter. Every other native role preserves its explicit absent sentinel as null. */
    public record Roles(Long actor,Long recipient,Long secondaryActor,Long secondaryRecipient,Long intermediary) {
        public Roles {
            need(actor!=null&&actor>0&&actor<0xFFFF_FFFFL,"actual outgoing sender full ID required");
            for(Long id:new Long[]{recipient,secondaryActor,secondaryRecipient,intermediary})need(id==null||id>0&&id<0xFFFF_FFFFL,"explicit native full ID/null role required");
        }
    }
    /** Authored order and every raw byte remain distinct, including duplicate flag values. */
    public record OptionRow(int ordinal,long flag,int bankByte) {
        public OptionRow {need(ordinal>=0&&ordinal<4096 && flag>=0&&flag<=0xFFFF_FFFFL && bankByte>=0&&bankByte<=1,"complete raw authored option row required");}
    }
    public record Candidate(long pendingFullId,long definitionHash,Roles roles,int routeKind,int ageDays,int aiReplyCutoffDays,List<OptionRow> options) {
        public Candidate {
            pendingId(pendingFullId);u32(definitionHash);Objects.requireNonNull(roles);options=List.copyOf(options);need(options.size()<=4096,"bounded complete option bank required");
            for(int i=0;i<options.size();i++)need(options.get(i).ordinal()==i,"authored option order is not complete");
        }
        public boolean knownActiveRoute(){return routeKind==0||routeKind==2;}
    }
    public record Snapshot(Frame frame,Profile profile,boolean complete,OptionalLong definitionHash,OptionalInt scannedSlots,OptionalLong senderCharacterId,
            List<Long> occupiedPendingIds,List<Candidate> candidates,Optional<String> unavailableReason) {
        public Snapshot {
            Objects.requireNonNull(frame);Objects.requireNonNull(profile);Objects.requireNonNull(definitionHash);Objects.requireNonNull(scannedSlots);Objects.requireNonNull(senderCharacterId);
            occupiedPendingIds=List.copyOf(occupiedPendingIds);candidates=List.copyOf(candidates);Objects.requireNonNull(unavailableReason);
            need(frame.build()==Build.CROZIER4,"outgoing value requires actual4 frame profile");
            need(occupiedPendingIds.size()<=1_000_000 && candidates.size()<=256,"finite complete storage bounds required");
            definitionHash.ifPresent(FamilyOutgoingCodec::u32);
            if(complete) {
                need(senderCharacterId.isPresent()&&senderCharacterId.getAsLong()>0&&senderCharacterId.getAsLong()<0xFFFF_FFFFL&&definitionHash.isPresent()&&scannedSlots.isPresent()&&scannedSlots.getAsInt()>=0&&scannedSlots.getAsInt()<=1_000_000&&unavailableReason.isEmpty(),"complete storage observation lacks full proof");
                need(profile!=Profile.EDUCATE_CHILD||senderCharacterId.getAsLong()==frame.actor().longValueExact(),"education sender must retain actual played actor");
                need(occupiedPendingIds.size()<=scannedSlots.getAsInt(),"occupied IDs exceed scanned complete capacity");
                Set<Long> ids=new HashSet<>();long previousSlot=-1;
                for(long id:occupiedPendingIds) {
                    pendingId(id);long slot=id&0x00FF_FFFFL;
                    need(slot>previousSlot&&slot<scannedSlots.getAsInt()&&ids.add(id),"occupied storage IDs lack complete slot/generation order");previousSlot=slot;
                }
                Set<Long> selected=new HashSet<>();
                for(var row:candidates) {
                    need(ids.contains(row.pendingFullId())&&selected.add(row.pendingFullId())
                            &&row.definitionHash()==definitionHash.getAsLong()&&row.roles().actor()==senderCharacterId.getAsLong(),"candidate is not an original complete storage member/definition/sender");
                    need(profile!=Profile.EDUCATE_CHILD||row.roles().recipient()!=null&&row.roles().secondaryActor()!=null&&row.roles().secondaryRecipient()!=null,
                            "education requires its actual complete material roles");
                }
            } else need(senderCharacterId.isEmpty()&&definitionHash.isEmpty()&&scannedSlots.isEmpty()&&occupiedPendingIds.isEmpty()&&candidates.isEmpty()&&unavailableReason.isPresent(),"unavailable observation must not invent a partial/negative result");
            unavailableReason.ifPresent(reason->need(!reason.isEmpty()&&reason.length()<=512,"bounded actual unavailable reason required"));
        }
    }
    public static Snapshot decodeGroup(RawJson raw,Frame frame,Profile profile) {
        return decodeGroup(DriverJson.toNode(DriverJson.object(raw.bytes(),DriverJson.MAX_NATIVE_BYTES)),frame,profile);
    }
    public static Snapshot decodeGroup(JsonNode n,Frame frame,Profile profile) {
        StrictJson.object(n,Set.of("schema","status","source","producer_scope","read_only","complete","passes","scanned_slots",
                "actor_id","sender_character_id","interaction_key","definition_stable_hash","occupied_pending_full_ids","candidates","unavailable_reason"));
        text(n,"schema",SCHEMA);text(n,"source","native_complete_outgoing_pending_storage_1.20.0.4");text(n,"producer_scope","complete_outgoing_storage");
        yes(n,"read_only");need(StrictJson.integer(n.get("actor_id"),1,0xFFFF_FFFEL)==frame.actor().longValueExact(),"storage actor differs from original frame");
        text(n,"interaction_key",profile.interactionKey());boolean complete=bool(n.get("complete"));text(n,"status",complete?"available":"unavailable");
        StrictJson.integer(n.get("passes"),complete?2:0,complete?2:0);
        OptionalLong hash=optionalU32(n.get("definition_stable_hash"));OptionalInt scanned=optionalCapacity(n.get("scanned_slots"));
        JsonNode occupied=n.get("occupied_pending_full_ids"),rows=n.get("candidates");
        need(occupied!=null&&occupied.isArray()&&occupied.size()<=1_000_000&&rows!=null&&rows.isArray()&&rows.size()<=256,"complete finite storage arrays required");
        List<Long> ids=new ArrayList<>();for(JsonNode id:occupied)ids.add(StrictJson.integer(id,0,0xFFFF_FFFEL));
        List<Candidate> candidates=new ArrayList<>();
        for(JsonNode row:rows) {
            StrictJson.object(row,Set.of("pending_full_id","definition_stable_hash","interaction_key","effective_roles","route_kind","age_days","ai_reply_cutoff_days","selected_option_rows"));
            text(row,"interaction_key",profile.interactionKey());candidates.add(new Candidate(
                    StrictJson.integer(row.get("pending_full_id"),0,0xFFFF_FFFEL),StrictJson.integer(row.get("definition_stable_hash"),0,0xFFFF_FFFFL),
                    roles(row.get("effective_roles")),(int)StrictJson.integer(row.get("route_kind"),Integer.MIN_VALUE,Integer.MAX_VALUE),
                    (int)StrictJson.integer(row.get("age_days"),Integer.MIN_VALUE,Integer.MAX_VALUE),(int)StrictJson.integer(row.get("ai_reply_cutoff_days"),Integer.MIN_VALUE,Integer.MAX_VALUE),
                    options(row.get("selected_option_rows"))));
        }
        JsonNode reason=n.get("unavailable_reason");need(reason!=null,"explicit unavailable reason/null required");
        return new Snapshot(frame,profile,complete,hash,scanned,optionalCharacter(n.get("sender_character_id")),ids,candidates,reason.isNull()?Optional.empty():Optional.of(StrictJson.text(reason)));
    }
    public static Roles roles(JsonNode n) {
        StrictJson.object(n,Set.of("actor_id","recipient_id","secondary_actor_id","secondary_recipient_id","intermediary_id"));
        return new Roles(character(n.get("actor_id")),nullableCharacter(n.get("recipient_id")),nullableCharacter(n.get("secondary_actor_id")),nullableCharacter(n.get("secondary_recipient_id")),
                nullableCharacter(n.get("intermediary_id")));
    }
    public static List<OptionRow> options(JsonNode rows) {
        need(rows!=null&&rows.isArray()&&rows.size()<=4096,"explicit full authored option bank required");List<OptionRow> out=new ArrayList<>();
        for(JsonNode row:rows) {
            StrictJson.object(row,Set.of("declared_ordinal","flag_full_u32","bank_value_u8"));
            out.add(new OptionRow((int)StrictJson.integer(row.get("declared_ordinal"),out.size(),out.size()),
                    StrictJson.integer(row.get("flag_full_u32"),0,0xFFFF_FFFFL),(int)StrictJson.integer(row.get("bank_value_u8"),0,1)));
        }
        return List.copyOf(out);
    }
    public static ObjectNode encodeRoles(Roles r) {
        var n=StrictJson.object().put("actor_id",r.actor()).put("recipient_id",r.recipient()).put("secondary_actor_id",r.secondaryActor()).put("secondary_recipient_id",r.secondaryRecipient());
        if(r.intermediary()==null)n.putNull("intermediary_id");else n.put("intermediary_id",r.intermediary());return n;
    }
    public static com.fasterxml.jackson.databind.node.ArrayNode encodeOptions(List<OptionRow> rows) {
        var n=StrictJson.object().putArray("rows");for(var row:List.copyOf(rows))n.add(StrictJson.object().put("declared_ordinal",row.ordinal()).put("flag_full_u32",row.flag()).put("bank_value_u8",row.bankByte()));return n;
    }
    public static ObjectNode encodeGroup(Snapshot s) {
        var n=StrictJson.object().put("schema",SCHEMA).put("status",s.complete()?"available":"unavailable")
                .put("source","native_complete_outgoing_pending_storage_1.20.0.4").put("producer_scope","complete_outgoing_storage").put("read_only",true)
                .put("complete",s.complete()).put("passes",s.complete()?2:0).put("actor_id",s.frame().actor()).put("interaction_key",s.profile().interactionKey());
        if(s.senderCharacterId().isPresent())n.put("sender_character_id",s.senderCharacterId().getAsLong());else n.putNull("sender_character_id");
        if(s.definitionHash().isPresent())n.put("definition_stable_hash",s.definitionHash().getAsLong());else n.putNull("definition_stable_hash");
        if(s.scannedSlots().isPresent())n.put("scanned_slots",s.scannedSlots().getAsInt());else n.putNull("scanned_slots");
        var ids=n.putArray("occupied_pending_full_ids");s.occupiedPendingIds().forEach(ids::add);var candidates=n.putArray("candidates");
        for(var row:s.candidates()) {var value=candidates.addObject().put("pending_full_id",row.pendingFullId()).put("definition_stable_hash",row.definitionHash())
                .put("interaction_key",s.profile().interactionKey()).put("route_kind",row.routeKind()).put("age_days",row.ageDays()).put("ai_reply_cutoff_days",row.aiReplyCutoffDays());
            value.set("effective_roles",encodeRoles(row.roles()));value.set("selected_option_rows",encodeOptions(row.options()));}
        if(s.unavailableReason().isPresent())n.put("unavailable_reason",s.unavailableReason().orElseThrow());else n.putNull("unavailable_reason");return n;
    }
    private static OptionalLong optionalCharacter(JsonNode n){need(n!=null,"explicit sender/null required");return n.isNull()?OptionalLong.empty():OptionalLong.of(StrictJson.integer(n,1,0xFFFF_FFFEL));}
    private static Long nullableCharacter(JsonNode n){need(n!=null,"explicit native role/null required");return n.isNull()?null:character(n);}
    private static Long character(JsonNode n){return StrictJson.integer(n,1,0xFFFF_FFFEL);}
    private static OptionalLong optionalU32(JsonNode n){need(n!=null,"explicit hash/null required");return n.isNull()?OptionalLong.empty():OptionalLong.of(StrictJson.integer(n,0,0xFFFF_FFFFL));}
    private static OptionalInt optionalCapacity(JsonNode n){need(n!=null,"explicit capacity/null required");return n.isNull()?OptionalInt.empty():OptionalInt.of((int)StrictJson.integer(n,0,1_000_000));}
    private static boolean bool(JsonNode n){need(n!=null&&n.isBoolean(),"actual JSON boolean required");return n.booleanValue();}
    private static void yes(JsonNode n,String key){need(bool(n.get(key)),"actual true required");}
    private static void text(JsonNode n,String key,String expected){need(expected.equals(StrictJson.text(n.get(key))),"outgoing field differs: "+key);}
    private static void pendingId(long id){need(id>=0&&id<0xFFFF_FFFFL,"native pending full ID includes zero and excludes only invalid sentinel");}
    private static void u32(long value){need(value>=0&&value<=0xFFFF_FFFFL,"full uint32 required");}
    private static void need(boolean value,String message){StrictJson.require(value,message);}
}


