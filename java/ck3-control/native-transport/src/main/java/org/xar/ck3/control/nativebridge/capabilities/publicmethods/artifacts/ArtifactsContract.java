package org.xar.ck3.control.nativebridge.capabilities.publicmethods.artifacts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.contracts.PublicUnsigned64;
import org.xar.ck3.control.contracts.PublicUnsigned64.Field;
import org.xar.ck3.control.contracts.StrictJson;

/** Original public artifact DATA contracts. None of these values is a Native permission, Ready, once claim or source qualification. */
public final class ArtifactsContract {
    public static final String VERSION = "1.20.0.4";
    public static final String EXECUTABLE_SHA256 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    public enum Kind { PERSONAL_ITEM, PERSONAL_ACTION, INVENTORY_OPEN, INVENTORY_CLOSE, KNIGHT, SKILLS, RELIC_CONTEXT, RELIC_PERMISSIONS, RELIC_ACTION_CONTEXT, RELIC_ACTION, CREATION_SELECTION }
    public enum Method {
        CLOSE("ck3_close_player_inventory_window_v1",Kind.INVENTORY_CLOSE,"close-player-inventory-window-v1-private","player_inventory_window_close_v1","player_inventory_window_close","close",false),
        ENSHRINE("ck3_enshrine_holy_site_relic_v1",Kind.RELIC_ACTION,"navigate-ingame-ui-v1","holy_site_relic_action","holy_site_relic_action","enshrine_relic",false),
        OPEN("ck3_open_player_inventory_window_v1",Kind.INVENTORY_OPEN,"open-player-inventory-window-v1-private","player_inventory_window_v1","player_inventory_window","open",false),
        KNIGHT("ck3_query_character_knight_effectiveness_v1",Kind.KNIGHT,"query-character-knight-effectiveness-v1-private","character_knight_effectiveness_v1","character_knight_effectiveness_v1","query",true),
        SKILLS("ck3_query_character_skill_effects_v1",Kind.SKILLS,"query-character-skill-effects-v1-private","character_skill_effects_v1","character_skill_effects_v1","query",true),
        PERSONAL_POST("ck3_query_player_artifact_personal_use_action_post_v1",Kind.PERSONAL_ACTION,"query-player-artifact-personal-use-action-post-v1-private","player_artifact_personal_use_action_v1","player_artifact_personal_use_action","post",true),
        PERSONAL_ITEM("ck3_query_player_artifact_personal_use_v1",Kind.PERSONAL_ITEM,"query-player-artifact-personal-use-v1","player_artifact_personal_use_v1","player_artifact_personal_use","query",true),
        RELIC_ACTION_CONTEXT("ck3_query_player_holy_site_relic_action_context_v1",Kind.RELIC_ACTION_CONTEXT,"query-player-holy-site-relic-action-context-v1","player_holy_site_relic_action_context_v1","player_holy_site_relic_action_context","query",true),
        RELIC_CONTEXT("ck3_query_player_holy_site_relic_context_v1",Kind.RELIC_CONTEXT,"query-player-holy-site-relic-context-v1","player_holy_site_relic_context_v1","player_holy_site_relic_context","query",true),
        RELIC_PERMISSIONS("ck3_query_player_holy_site_relic_permissions_v1",Kind.RELIC_PERMISSIONS,"query-player-holy-site-relic-permissions-v1","player_holy_site_relic_permissions_v1","player_holy_site_relic_permissions","query",true),
        CLOSE_POST("ck3_query_player_inventory_window_close_post_v1",Kind.INVENTORY_CLOSE,"query-player-inventory-window-close-post-v1-private","player_inventory_window_close_v1","player_inventory_window_close","post",true),
        CLOSE_QUERY("ck3_query_player_inventory_window_close_v1",Kind.INVENTORY_CLOSE,"query-player-inventory-window-close-v1-private","player_inventory_window_close_v1","player_inventory_window_close","query",true),
        OPEN_POST("ck3_query_player_inventory_window_open_post_v1",Kind.INVENTORY_OPEN,"query-player-inventory-window-open-post-v1-private","player_inventory_window_v1","player_inventory_window","post",true),
        REMOVE("ck3_remove_holy_site_relic_v1",Kind.RELIC_ACTION,"navigate-ingame-ui-v1","holy_site_relic_action","holy_site_relic_action","remove_relic",false),
        SELECT_RELIC("ck3_select_holy_site_relic_artifact_v1",Kind.RELIC_ACTION,"navigate-ingame-ui-v1","holy_site_relic_action","holy_site_relic_action","select_relic_artifact",false),
        CREATION_SELECTION("ck3_set_holy_site_creation_artifact_selection_v1",Kind.CREATION_SELECTION,"navigate-ingame-ui-v1","holy_site_creation_artifact_selection","holy_site_creation_artifact_selection","set_holy_site_creation_artifact_selection",false),
        RELIC_SLOT("ck3_set_holy_site_relic_slot_selection_v1",Kind.RELIC_ACTION,"navigate-ingame-ui-v1","holy_site_relic_action","holy_site_relic_action","set_relic_slot",false),
        PERSONAL_SUBMIT("ck3_submit_player_artifact_personal_use_v1",Kind.PERSONAL_ACTION,"submit-player-artifact-personal-use-v1-private","player_artifact_personal_use_action_v1","player_artifact_personal_use_action","submit",false);
        private final String originalName,step,domain,resultKey,operation; private final Kind kind; private final boolean readOnly;
        Method(String name,Kind kind,String step,String domain,String resultKey,String operation,boolean readOnly){this.originalName=name;this.kind=kind;this.step=step;this.domain=domain;this.resultKey=resultKey;this.operation=operation;this.readOnly=readOnly;}
        public String originalName(){return originalName;} public Kind kind(){return kind;} public String step(){return step;}
        public String domain(){return domain;} public String resultKey(){return resultKey;} public String operation(){return operation;} public boolean readOnly(){return readOnly;}
        public static Method exact(String name){for(Method method:values())if(method.originalName.equals(name))return method;throw new IllegalArgumentException("unknown original artifact public method: "+name);}
    }
    public enum Skill { DIPLOMACY, MARTIAL, STEWARDSHIP, INTRIGUE, LEARNING, PROWESS;
        public String key(){return name().toLowerCase(java.util.Locale.ROOT);}
        public static Skill exact(String key){for(Skill value:values())if(value.key().equals(key))return value;throw new IllegalArgumentException("unknown native skill");}
    }
    public sealed interface Request permits RevisionRequest,InventoryPost,ArtifactRead,PersonalSubmit,PersonalPost,CharacterRead,SkillRead,RelicSite,RelicPermissions,RelicPair,RelicSlot,Enshrine,Remove,CreationSelection {
        Method method(); BigInteger expectedRevision();
    }
    public record RevisionRequest(Method method,BigInteger expectedRevision) implements Request {
        public RevisionRequest{oneOf(method,Method.CLOSE,Method.OPEN,Method.CLOSE_QUERY);revision(expectedRevision,false);}
    }
    public record InventoryPost(Method method,BigInteger expectedRevision,BigInteger expectedIntentSequence) implements Request {
        public InventoryPost{oneOf(method,Method.OPEN_POST,Method.CLOSE_POST);revision(expectedRevision,false);revision(expectedIntentSequence,false);}
    }
    public record ArtifactRead(BigInteger expectedRevision,long artifactId) implements Request {
        public ArtifactRead{revision(expectedRevision,false);fullId(artifactId);} public Method method(){return Method.PERSONAL_ITEM;}
    }
    public record PersonalSubmit(BigInteger expectedRevision,long artifactId,boolean desiredEquipped,int expectedSlotIndex,Field expectedReplacingArtifactId,boolean policyPositive) implements Request {
        public PersonalSubmit{revision(expectedRevision,false);fullId(artifactId);slot(expectedSlotIndex,63);optionalId(expectedReplacingArtifactId);StrictJson.require(desiredEquipped||!(expectedReplacingArtifactId instanceof PublicUnsigned64.Value),"unequip has no replacing artifact");}
        public Method method(){return Method.PERSONAL_SUBMIT;}
    }
    public record PersonalPost(BigInteger expectedRevision,long artifactId,BigInteger expectedIntentSequence) implements Request {
        public PersonalPost{revision(expectedRevision,false);fullId(artifactId);revision(expectedIntentSequence,false);} public Method method(){return Method.PERSONAL_POST;}
    }
    public record CharacterRead(BigInteger expectedRevision,long characterId) implements Request {
        public CharacterRead{revision(expectedRevision,false);fullId(characterId);} public Method method(){return Method.KNIGHT;}
    }
    public record SkillRead(BigInteger expectedRevision,long characterId,Skill skill) implements Request {
        public SkillRead{revision(expectedRevision,false);fullId(characterId);Objects.requireNonNull(skill);} public Method method(){return Method.SKILLS;}
    }
    public record RelicSite(BigInteger expectedRevision,long holySiteId) implements Request {
        public RelicSite{revision(expectedRevision,false);fullId(holySiteId);} public Method method(){return Method.RELIC_CONTEXT;}
    }
    public record RelicPermissions(BigInteger expectedRevision,long holySiteId,Field artifactId) implements Request {
        public RelicPermissions{revision(expectedRevision,false);fullId(holySiteId);optionalId(artifactId);} public Method method(){return Method.RELIC_PERMISSIONS;}
    }
    public record RelicPair(Method method,BigInteger expectedRevision,long holySiteId,long artifactId) implements Request {
        public RelicPair{oneOf(method,Method.RELIC_ACTION_CONTEXT,Method.SELECT_RELIC);revision(expectedRevision,false);fullId(holySiteId);fullId(artifactId);}
    }
    public record RelicSlot(BigInteger expectedRevision,long holySiteId,int slotIndex,boolean desiredSelected) implements Request {
        public RelicSlot{revision(expectedRevision,false);fullId(holySiteId);slot(slotIndex,4095);} public Method method(){return Method.RELIC_SLOT;}
    }
    public record Enshrine(BigInteger expectedRevision,long holySiteId,long artifactId,int expectedEffectiveSlotIndex,boolean expectedReplacingEmpty,String expectedPreviewSha256,Field expectedReplacingArtifactId) implements Request {
        public Enshrine{revision(expectedRevision,false);fullId(holySiteId);fullId(artifactId);slot(expectedEffectiveSlotIndex,4095);digest(expectedPreviewSha256);optionalId(expectedReplacingArtifactId);StrictJson.require(expectedReplacingEmpty?!(expectedReplacingArtifactId instanceof PublicUnsigned64.Value):expectedReplacingArtifactId instanceof PublicUnsigned64.Value,"frozen replacement fields differ from empty/nonempty destination");}
        public Method method(){return Method.ENSHRINE;}
    }
    public record Remove(BigInteger expectedRevision,long holySiteId,long artifactId,boolean expectedReplacingEmpty,String expectedPreviewSha256) implements Request {
        public Remove{revision(expectedRevision,false);fullId(holySiteId);fullId(artifactId);StrictJson.require(expectedReplacingEmpty,"remove has no replacement destination");digest(expectedPreviewSha256);} public Method method(){return Method.REMOVE;}
    }
    public record CreationSelection(BigInteger expectedRevision,long artifactId,boolean selected) implements Request {
        public CreationSelection{revision(expectedRevision,true);fullId(artifactId);} public Method method(){return Method.CREATION_SELECTION;}
    }
    /** Actual physical DATA supplied by the owning Root; public construction does not qualify it. */
    public record NativeFrame(BigInteger publicRevision,BigInteger nativeRevision,BigInteger dateRaw,long actorCharacterId,long gamePid,
            BigInteger gameCreationFiletime,BigInteger connectionGeneration,String episodeRunId,String executableSha256,boolean paused,boolean mapReady,boolean alive) {
        public NativeFrame{revision(publicRevision,true);revision(nativeRevision,false);Objects.requireNonNull(dateRaw);StrictJson.require(dateRaw.bitLength()<=31,"signed native date required");fullId(actorCharacterId);StrictJson.require(actorCharacterId>0&&gamePid>0&&gamePid<=0xffffffffL,"actual played actor/Game PID required");revision(gameCreationFiletime,false);revision(connectionGeneration,false);StrictJson.require(episodeRunId!=null&&!episodeRunId.isEmpty(),"actual episode required");digest(executableSha256);}
    }
    /** Complete actual command_result plus independently observed after-frame; no Native IO occurs in the codec. */
    public record NativeEnvelope(String expectedRequestId,JsonNode packet,NativeFrame afterFrame) {
        public NativeEnvelope{StrictJson.require(expectedRequestId!=null&&!expectedRequestId.isEmpty(),"actual native request identity required");packet=Objects.requireNonNull(packet).deepCopy();Objects.requireNonNull(afterFrame);}
        @Override public JsonNode packet(){return packet.deepCopy();}
    }
    /** Positive observations only: false does not manufacture a native negative for an absent optional field. */
    public record Facts(boolean available,boolean onceIntentConsumed,boolean invoked,boolean needsRecovery,boolean independentDesiredObserved,
            Optional<BigInteger> actualIntentSequence,boolean selectionPostconditionObserved,boolean nativeDispatchAttempted,boolean gameplayCommandMayHaveBeenQueued) {
        public Facts{Objects.requireNonNull(actualIntentSequence);actualIntentSequence.ifPresent(value->revision(value,false));}
    }
    /** Immutable complete native field representation, constructed only after the domain codec validates its exact schema and semantics. */
    public static final class NativePayload {
        private final ObjectNode original;
        NativePayload(ObjectNode original){this.original=Objects.requireNonNull(original).deepCopy();}
        public ObjectNode original(){return original.deepCopy();}
    }
    public sealed interface Reply permits PersonalItemReply,PersonalActionReply,InventoryReply,KnightReply,SkillsReply,RelicContextReply,RelicPermissionsReply,RelicActionContextReply,RelicActionReply,CreationSelectionReply {
        Method method(); Facts facts(); NativePayload payload();
    }
    public record PersonalItemReply(Method method,Facts facts,NativePayload payload) implements Reply {public PersonalItemReply{reply(method,facts,payload,Kind.PERSONAL_ITEM);}}
    public record PersonalActionReply(Method method,Facts facts,NativePayload payload) implements Reply {public PersonalActionReply{reply(method,facts,payload,Kind.PERSONAL_ACTION);}}
    public record InventoryReply(Method method,Facts facts,NativePayload payload) implements Reply {public InventoryReply{reply(method,facts,payload,Kind.INVENTORY_OPEN,Kind.INVENTORY_CLOSE);}}
    public record KnightReply(Method method,Facts facts,NativePayload payload) implements Reply {public KnightReply{reply(method,facts,payload,Kind.KNIGHT);}}
    public record SkillsReply(Method method,Facts facts,NativePayload payload) implements Reply {public SkillsReply{reply(method,facts,payload,Kind.SKILLS);}}
    public record RelicContextReply(Method method,Facts facts,NativePayload payload) implements Reply {public RelicContextReply{reply(method,facts,payload,Kind.RELIC_CONTEXT);}}
    public record RelicPermissionsReply(Method method,Facts facts,NativePayload payload) implements Reply {public RelicPermissionsReply{reply(method,facts,payload,Kind.RELIC_PERMISSIONS);}}
    public record RelicActionContextReply(Method method,Facts facts,NativePayload payload) implements Reply {public RelicActionContextReply{reply(method,facts,payload,Kind.RELIC_ACTION_CONTEXT);}}
    public record RelicActionReply(Method method,Facts facts,NativePayload payload) implements Reply {public RelicActionReply{reply(method,facts,payload,Kind.RELIC_ACTION);}}
    public record CreationSelectionReply(Method method,Facts facts,NativePayload payload) implements Reply {public CreationSelectionReply{reply(method,facts,payload,Kind.CREATION_SELECTION);}}
    static void fullId(long value){StrictJson.require(value>=0&&value<=0xfffffffeL,"full32 native reference required; sentinel rejected");}
    static void slot(int value,int maximum){StrictJson.require(value>=0&&value<=maximum,"native slot outside bounded original range");}
    static void revision(BigInteger value,boolean zero){PublicUnsigned64.canonical(value,zero?PublicUnsigned64.Minimum.ZERO:PublicUnsigned64.Minimum.ONE);}
    static void digest(String value){StrictJson.require(value!=null&&value.matches("[0-9a-f]{64}"),"canonical lowercase SHA256 required");}
    static void optionalId(Field field){Objects.requireNonNull(field);if(field instanceof PublicUnsigned64.Value value){StrictJson.require(value.value().bitLength()<=32,"full32 reference required");fullId(value.value().longValueExact());}}
    private static void oneOf(Method method,Method... allowed){StrictJson.require(method!=null&&Set.of(allowed).contains(method),"request variant does not match exact original method");}
    private static void reply(Method method,Facts facts,NativePayload payload,Kind... kinds){Objects.requireNonNull(method);Objects.requireNonNull(facts);Objects.requireNonNull(payload);StrictJson.require(Set.of(kinds).contains(method.kind()),"reply variant does not match original method");}
    private ArtifactsContract(){ }
}
