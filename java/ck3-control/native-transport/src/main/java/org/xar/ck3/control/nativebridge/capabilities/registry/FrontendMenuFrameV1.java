package org.xar.ck3.control.nativebridge.capabilities.registry;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;

/** Explicit current variant of the frontend route family. DATA is never menu action authority. */
public record FrontendMenuFrameV1(Action action, Status status, boolean effectAttempted,
        boolean nativeReturned, boolean postSelectionVerified, BigInteger providerGeneration,
        BigInteger querySequence, BigInteger claimSequence, Optional<Source> source,
        Optional<OwnerWitness> ownerWitness, Optional<String> unavailableReason) {
    public static final String REQUEST_SCHEMA="ck3.frontend_gui_route.current267_request.v1";
    public static final String SCHEMA="ck3.frontend_gui_route.current267_result.v1";
    public static final String BACKEND="ck3-1.21.0.3-native-application-main-frontend";
    public static final ExactCk3Build BUILD=ExactCk3Build.CK3_121003_STEAM_26785313;
    public static final String ROBERT_BOOKMARK="bm_1066_rags_to_riches";
    public static final String ROBERT_CHARACTER="bookmark_rags_to_riches_duke_robert";
    static final Set<String> FIELDS=Set.of("schema","game_version","executable_sha256","adapter_id","backend","step","action","status",
            "facts_available","effect_attempted","native_returned","post_selection_verified","addresses_redacted","world_core_fabricated",
            "application_exit_confirmed","game_started_confirmed","physical_save_confirmed","provider_generation","query_sequence","claim_sequence",
            "source","owner_witness","unavailable_reason");
    public enum Action {
        QUERY_MENU("query_menu","query-current-frontend-menu-v1","game.command.query-current-frontend-menu.v1"),
        QUIT_MENU("quit_menu","quit-current-frontend-menu-v1","game.command.quit-current-frontend-menu.v1"),
        OPEN_BOOKMARKS("open_bookmarks","open-current-frontend-bookmarks-v1","game.command.open-current-frontend-bookmarks.v1"),
        SELECT_1066_BOOKMARK("select_1066_bookmark","select-current-frontend-bookmark1066-v1","game.command.select-current-frontend-bookmark1066.v1"),
        SELECT_ROBERT_1066("select_robert_1066","select-current-frontend-robert1066-v1","game.command.select-current-frontend-robert1066.v1"),
        START_ROBERT_1066("start_robert_1066","start-current-frontend-robert1066-v1","game.command.start-current-frontend-robert1066.v1");
        private final String wire,step,capability;
        Action(String wire,String step,String capability){this.wire=wire;this.step=step;this.capability=capability;}
        public String wire(){return wire;} public String step(){return step;} public String capability(){return capability;}
        public boolean readOnly(){return this==QUERY_MENU;}
        public static Action wire(String value){for(var action:values())if(action.wire.equals(value))return action;throw new IllegalArgumentException("unknown fixed current frontend action");}
    }
    public enum Status {
        UNAVAILABLE("unavailable"),AVAILABLE("available"),EXPIRED("expired"),SOURCE_CHANGED("source_changed"),
        QUERY_CONSUMED("query_consumed"),CLAIM_CONSUMED("claim_consumed"),CAPACITY_EXHAUSTED("capacity_exhausted"),
        EXIT_REQUESTED("exit_requested"),BOOKMARKS_OPENED("bookmarks_opened"),BOOKMARK_SELECTED("bookmark_selected"),
        SELECTION_DISPATCHED("selection_dispatched"),START_DISPATCHED("start_dispatched"),INDETERMINATE("indeterminate");
        private final String wire;Status(String wire){this.wire=wire;}public String wire(){return wire;}
        public boolean successful(){return this==AVAILABLE||this==EXIT_REQUESTED||this==BOOKMARKS_OPENED||this==BOOKMARK_SELECTED||this==SELECTION_DISPATCHED||this==START_DISPATCHED;}
        public static Status wire(String value){for(var status:values())if(status.wire.equals(value))return status;throw new IllegalArgumentException("unknown current frontend status");}
    }
    public enum Route {
        MAIN_MENU("main_menu"),BOOKMARKS("bookmarks"),LOBBY("lobby");
        private final String wire;Route(String wire){this.wire=wire;}public String wire(){return wire;}
        public static Route wire(String value){for(var route:values())if(route.wire.equals(value))return route;throw new IllegalArgumentException("unknown current no-world menu route");}
    }
    /** Five true source guards are represented by this type, never by caller-provided authority flags. */
    public record Source(Route route,Optional<String> selectedBookmarkKey,Optional<String> selectedCharacterKey,
            boolean robertSourceVerified,boolean startAdmissible) {
        public Source {
            Objects.requireNonNull(route);Objects.requireNonNull(selectedBookmarkKey);Objects.requireNonNull(selectedCharacterKey);
            selectedBookmarkKey.ifPresent(v->RegistryJson.require(!v.isEmpty(),"empty selected bookmark key"));
            selectedCharacterKey.ifPresent(v->RegistryJson.require(!v.isEmpty(),"empty selected character key"));
            RegistryJson.require(!robertSourceVerified||(selectedBookmarkKey.filter(ROBERT_BOOKMARK::equals).isPresent()
                    &&selectedCharacterKey.filter(ROBERT_CHARACTER::equals).isPresent()),"Robert witness requires both actual fixed keys");
            RegistryJson.require(!startAdmissible||robertSourceVerified,"start admissibility requires actual verified Robert source");
        }
    }
    public record OwnerWitness(BigInteger connectionGeneration,BigInteger ticketSequence,BigInteger pumpEpoch,long threadId) {
        public OwnerWitness {for(var value:List.of(connectionGeneration,ticketSequence,pumpEpoch))uint64(value,true);
            RegistryJson.require(threadId>0&&threadId<=0xffff_ffffL,"positive uint32 frontend owner required");}
    }
    public FrontendMenuFrameV1 {
        Objects.requireNonNull(action);Objects.requireNonNull(status);Objects.requireNonNull(source);Objects.requireNonNull(ownerWitness);Objects.requireNonNull(unavailableReason);
        uint64(providerGeneration,false);uint64(querySequence,false);uint64(claimSequence,false);
        RegistryJson.require(source.isPresent()==ownerWitness.isPresent(),"frontend source and original owner must be atomic");
        if(status.successful()) {
            RegistryJson.require(source.isPresent()&&unavailableReason.isEmpty()&&providerGeneration.signum()>0&&querySequence.signum()>0,"successful frontend result needs actual source/owner/lease");
            switch(status) {
                case AVAILABLE->RegistryJson.require(action==Action.QUERY_MENU&&!effectAttempted&&!nativeReturned&&!postSelectionVerified&&claimSequence.signum()==0,"readonly menu query cannot perform an effect");
                case EXIT_REQUESTED->requireEffect(action==Action.QUIT_MENU,effectAttempted,nativeReturned,postSelectionVerified,false,claimSequence);
                case BOOKMARKS_OPENED->requireEffect(action==Action.OPEN_BOOKMARKS,effectAttempted,nativeReturned,postSelectionVerified,false,claimSequence);
                case BOOKMARK_SELECTED->requireEffect(action==Action.SELECT_1066_BOOKMARK,effectAttempted,nativeReturned,postSelectionVerified,false,claimSequence);
                case SELECTION_DISPATCHED->{requireEffect(action==Action.SELECT_ROBERT_1066,effectAttempted,nativeReturned,postSelectionVerified,true,claimSequence);RegistryJson.require(source.orElseThrow().robertSourceVerified(),"Robert selection requires actual after-model verification");}
                case START_DISPATCHED->{requireEffect(action==Action.START_ROBERT_1066,effectAttempted,nativeReturned,postSelectionVerified,false,claimSequence);RegistryJson.require(source.orElseThrow().startAdmissible(),"Robert start requires actual admissible selected model");}
                default->throw new IllegalArgumentException("unsupported frontend success");
            }
        } else RegistryJson.require(unavailableReason.isPresent()&&!unavailableReason.orElseThrow().isEmpty(),"known frontend refusal requires its exact reason");
    }
    private static void requireEffect(boolean actionMatches,boolean attempted,boolean returned,boolean selected,boolean expectedSelected,BigInteger claim) {
        RegistryJson.require(actionMatches&&attempted&&returned&&selected==expectedSelected&&claim.signum()>0,"frontend callback result coherence mismatch");
    }
    static void uint64(BigInteger value,boolean positive){Objects.requireNonNull(value);RegistryJson.require(value.signum()>=(positive?1:0)&&value.compareTo(RegistryJson.U64)<=0,"canonical uint64 outside range");}
    static BigInteger decimal(com.fasterxml.jackson.databind.JsonNode value,boolean positive) {
        String token=RegistryJson.text(value);RegistryJson.require(token.matches(positive?"[1-9][0-9]{0,19}":"0|[1-9][0-9]{0,19}"),"canonical unsigned decimal string required");
        BigInteger result=new BigInteger(token);uint64(result,positive);return result;
    }
    public boolean nativeOk(){return status.successful();}
    public static FrontendMenuFrameV1 decode(RawJson original) {
        var row=RegistryJson.object(original);RegistryJson.keys(row,FIELDS);requireTuple(row,SCHEMA);
        var action=Action.wire(RegistryJson.text(row.get("action")));RegistryJson.require(action.step().equals(RegistryJson.text(row.get("step"))),"frontend step must match its fixed action");
        RegistryJson.require(RegistryJson.bool(row.get("addresses_redacted"))&&!RegistryJson.bool(row.get("world_core_fabricated"))&&!RegistryJson.bool(row.get("application_exit_confirmed"))
                &&!RegistryJson.bool(row.get("game_started_confirmed"))&&!RegistryJson.bool(row.get("physical_save_confirmed")),"menu DATA cannot fabricate World Core, process exit, started Game or physical SAVE");
        boolean available=RegistryJson.bool(row.get("facts_available"));Optional<Source> source=Optional.empty();Optional<OwnerWitness> owner=Optional.empty();
        if(available) {
            var s=RegistryJson.object(row.get("source"));RegistryJson.keys(s,Set.of("route","application_verified","gui_context_verified","global_root_verified","route_root_visible","no_world","selected_bookmark_key","selected_character_key","robert_source_verified","start_admissible"));
            for(String field:List.of("application_verified","gui_context_verified","global_root_verified","route_root_visible","no_world"))RegistryJson.require(RegistryJson.bool(s.get(field)),"frontend actual no-world source guard missing: "+field);
            source=Optional.of(new Source(Route.wire(RegistryJson.text(s.get("route"))),nullableText(s.get("selected_bookmark_key")),nullableText(s.get("selected_character_key")),RegistryJson.bool(s.get("robert_source_verified")),RegistryJson.bool(s.get("start_admissible"))));
            var w=RegistryJson.object(row.get("owner_witness"));RegistryJson.keys(w,Set.of("connection_generation","ticket_sequence","pump_epoch","thread_id"));
            owner=Optional.of(new OwnerWitness(decimal(w.get("connection_generation"),true),decimal(w.get("ticket_sequence"),true),decimal(w.get("pump_epoch"),true),RegistryJson.integer(w.get("thread_id"),BigInteger.ONE,BigInteger.valueOf(0xffff_ffffL)).longValueExact()));
        } else RegistryJson.require(row.get("source").isNull()&&row.get("owner_witness").isNull(),"unavailable menu source/owner must both be explicit null");
        return new FrontendMenuFrameV1(action,Status.wire(RegistryJson.text(row.get("status"))),RegistryJson.bool(row.get("effect_attempted")),RegistryJson.bool(row.get("native_returned")),RegistryJson.bool(row.get("post_selection_verified")),decimal(row.get("provider_generation"),false),decimal(row.get("query_sequence"),false),decimal(row.get("claim_sequence"),false),source,owner,nullableText(row.get("unavailable_reason")));
    }
    static Optional<String> nullableText(com.fasterxml.jackson.databind.JsonNode value){RegistryJson.require(value!=null,"explicit null or text required");return value.isNull()?Optional.empty():Optional.of(RegistryJson.text(value));}
    static void requireTuple(com.fasterxml.jackson.databind.node.ObjectNode row,String schema){RegistryJson.require(schema.equals(RegistryJson.text(row.get("schema")))&&BUILD.matches(RegistryJson.text(row.get("game_version")),RegistryJson.text(row.get("executable_sha256")))&&BUILD.coreFrameAdapterId().equals(RegistryJson.text(row.get("adapter_id")))&&BACKEND.equals(RegistryJson.text(row.get("backend"))),"frontend exact current267 tuple mismatch");}
}
