package org.xar.ck3.control.nativebridge;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Fourteen fixed Living requests, without caller IDs, roles, keys, indices, slots or finite phases. */
public final class CurrentLivingUi {
    public static final String SCHEMA = "xar.living-ui.request/v1";
    public static final String SOURCE_SCHEMA = "xar.living-ui.source/v1";
    public static final String RESULT_SCHEMA = "xar.living-ui.result/v1";
    public static final String BACKEND = "current267-fixed-living-ui-v1";
    public static final String STEP = "ck3_121003_living_ui.execute";
    public static final String CAPABILITY = "game.command.current-living-fixed-ui.v1";

    public enum Action {
        QUERY_WEAPON("query_weapon", CurrentLivingUiSource.Kind.WEAPON, true),
        SELECT_WEAPON("select_weapon", CurrentLivingUiSource.Kind.WEAPON, false),
        EQUIP_TARGET("equip_target", CurrentLivingUiSource.Kind.WEAPON, false),
        UNEQUIP_TARGET("unequip_target", CurrentLivingUiSource.Kind.WEAPON, false),
        QUERY_EVENTS("query_events", CurrentLivingUiSource.Kind.EVENTS, true),
        OPEN_TUTORIAL("open_tutorial", CurrentLivingUiSource.Kind.EVENTS, false),
        FEED_COMMON("feed_common", CurrentLivingUiSource.Kind.EVENTS, false),
        FEED_MASTERWORK("feed_masterwork", CurrentLivingUiSource.Kind.EVENTS, false),
        FEED_FAMED("feed_famed", CurrentLivingUiSource.Kind.EVENTS, false),
        FEED_ILLUSTRIOUS("feed_illustrious", CurrentLivingUiSource.Kind.EVENTS, false),
        CANCEL_REVIEW("cancel_review", CurrentLivingUiSource.Kind.EVENTS, false),
        CONFIRM_REVIEW("confirm_review", CurrentLivingUiSource.Kind.EVENTS, false),
        QUERY_DETAIL("query_detail", CurrentLivingUiSource.Kind.DETAIL, true),
        CLOSE_MANAGEMENT("close_management", CurrentLivingUiSource.Kind.EVENTS, false);

        private final String wire;
        private final CurrentLivingUiSource.Kind sourceKind;
        private final boolean queryOnly;
        Action(String wire, CurrentLivingUiSource.Kind sourceKind, boolean queryOnly) {
            this.wire=wire; this.sourceKind=sourceKind; this.queryOnly=queryOnly;
        }
        public String wire(){return wire;}
        public CurrentLivingUiSource.Kind sourceKind(){return sourceKind;}
        public boolean queryOnly(){return queryOnly;}
        public String step(){return STEP;}
        public String capability(){return CAPABILITY;}
        public static Action parse(String text)throws IOException {
            for(var action:values())if(action.wire.equals(text))return action;
            throw new IOException("Unknown fixed Living UI action");
        }
    }

    private CurrentLivingUi(){ }

    public static NativeRequest request(CoreFrame.Partial actual, Action action,
            BigInteger provider, BigInteger query) {
        Objects.requireNonNull(actual);Objects.requireNonNull(action);
        StrictJson.require(actual.build()==ExactCk3Build.CK3_121003_STEAM_26785313,"Exact current267 Core required");
        requirePrefix(actual.prefix());
        CurrentLivingInventoryQuery.unsigned(provider,false);CurrentLivingInventoryQuery.unsigned(query,false);
        StrictJson.require(action.queryOnly()?provider.signum()==0&&query.signum()==0:provider.signum()>0&&query.signum()>0,
                "Original query/action generations differ");
        var build=actual.build();
        var claim=StrictJson.object().put("schema",SCHEMA).put("game_version",build.version())
                .put("executable_sha256",build.executableSha256()).put("adapter_id",build.coreFrameAdapterId())
                .put("backend",BACKEND).put("action",action.wire()).put("provider_generation",provider).put("query_sequence",query);
        claim.set("expected_core",CurrentLivingInventoryQuery.prefix(actual.prefix()));
        var fields=StrictJson.object();fields.set("living_ui",claim);fields.set("arguments",StrictJson.object());
        // Only the dedicated Transport supplies the original strict8 actor/target/ID/deadline envelope.
        return new NativeRequest(STEP,CAPABILITY,new RawJson(StrictJson.canonical(fields)));
    }

    public static void requirePrefix(CoreFrame.Prefix prefix){CurrentLivingEntry.requirePrefix(prefix);}
    static CoreFrame.Prefix readCore(JsonNode node)throws IOException{return CurrentLivingEntry.readCore(node);}

    /** Exact authored DATA mapping only. In particular .12/index1 is not the management close. */
    static int fixedIndex(Action action,String definition) {
        if(definition.equals("xalw.12")&&action==Action.OPEN_TUTORIAL)return 0;
        if(definition.equals("xalw.10"))return switch(action) {
            case FEED_COMMON -> 1;
            case FEED_MASTERWORK -> 2;
            case FEED_FAMED -> 3;
            case FEED_ILLUSTRIOUS -> 4;
            case CLOSE_MANAGEMENT -> 9;
            default -> -1;
        };
        if(definition.equals("xalw.11"))return switch(action) {
            case CONFIRM_REVIEW -> 0;
            case CANCEL_REVIEW -> 1;
            default -> -1;
        };
        return -1;
        // Actual latest instance, held target, settled_mask0xF and once/UNKNOWN custody stay private in Native.
    }
}
