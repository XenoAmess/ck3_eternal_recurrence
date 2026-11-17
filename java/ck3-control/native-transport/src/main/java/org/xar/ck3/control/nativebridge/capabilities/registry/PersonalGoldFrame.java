package org.xar.ck3.control.nativebridge.capabilities.registry;

import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.semantic.NativePlayedResources;

/** Public personal-gold DATA only. It is neither treasury/monthly cash nor a complete gameplay observation. */
public sealed interface PersonalGoldFrame permits PersonalGoldFrame.Partial, PersonalGoldFrame.Unavailable {
    String STEP="query-personal-gold-frame-v1";
    String CAPABILITY="game.query.personal-gold-frame.v1";
    String SCHEMA="ck3_1210_personal_gold_frame_v1";
    String ADAPTER="ck3-1.21.0-msvc-x64";
    String BACKEND="ck3-1.21.0-native-headless-main-thread";
    ExactCk3Build BUILD=ExactCk3Build.CK3_1210;
    Set<String> FIELDS=Set.of("step","schema","game_version","executable_sha256","adapter_id","backend","status",
            "personal_gold_available","application_main_observed","complete_snapshot","treasury_observed","monthly_flow_observed",
            "core_frame","personal_gold","unavailable_reason");
    default ExactCk3Build build(){return BUILD;}
    CoreFrame coreFrame();
    boolean applicationMainObserved();

    record Partial(CoreFrame.Partial coreFrame,NativePlayedResources.Amount personalGold) implements PersonalGoldFrame {
        public Partial {
            Objects.requireNonNull(coreFrame);Objects.requireNonNull(personalGold);
            RegistryJson.require(coreFrame.build()==BUILD,"personal gold requires the exact Florin core frame");
            var prefix=coreFrame.prefix();
            RegistryJson.require(prefix.mapReady()&&prefix.paused()&&prefix.hasPlayedCharacter()&&prefix.playedCharacterAlive(),
                    "personal gold requires the actual paused map and living played character");
        }
        @Override public boolean applicationMainObserved(){return true;}
    }
    record Unavailable(CoreFrame coreFrame,boolean applicationMainObserved,String reason) implements PersonalGoldFrame {
        public Unavailable {
            Objects.requireNonNull(coreFrame);
            RegistryJson.require(coreFrame.build()==BUILD,"personal gold requires the exact Florin core frame");
            boolean coreObserved=coreFrame instanceof CoreFrame.Partial
                    ||((CoreFrame.Unavailable)coreFrame).applicationMainObserved();
            RegistryJson.require(applicationMainObserved==coreObserved,"personal gold and core application-main observations differ");
            RegistryJson.require(reason!=null&&!reason.isEmpty(),"personal gold unavailability requires its original reason");
        }
    }
    static PersonalGoldFrame decode(RawJson original) {
        var row=RegistryJson.object(original);RegistryJson.keys(row,FIELDS);
        RegistryJson.require(STEP.equals(RegistryJson.text(row.get("step")))&&SCHEMA.equals(RegistryJson.text(row.get("schema")))
                &&BUILD.matches(RegistryJson.text(row.get("game_version")),RegistryJson.text(row.get("executable_sha256")))
                &&ADAPTER.equals(RegistryJson.text(row.get("adapter_id")))&&BACKEND.equals(RegistryJson.text(row.get("backend"))),
                "personal gold exact source mismatch");
        RegistryJson.require(!RegistryJson.bool(row.get("complete_snapshot"))&&!RegistryJson.bool(row.get("treasury_observed"))
                &&!RegistryJson.bool(row.get("monthly_flow_observed")),"personal gold cannot claim complete, treasury or monthly observations");
        var core=CoreFrame.decodeObject(RegistryJson.object(row.get("core_frame")));
        RegistryJson.require(core.build()==BUILD,"personal gold and nested core exact sources differ");
        boolean available=RegistryJson.bool(row.get("personal_gold_available"));
        boolean observed=RegistryJson.bool(row.get("application_main_observed"));
        if(!available) {
            RegistryJson.require("unavailable".equals(RegistryJson.text(row.get("status")))&&row.get("personal_gold").isNull(),
                    "unavailable personal gold must retain explicit null");
            return new Unavailable(core,observed,RegistryJson.text(row.get("unavailable_reason")));
        }
        RegistryJson.require("partial".equals(RegistryJson.text(row.get("status")))&&observed&&row.get("unavailable_reason").isNull()
                &&core instanceof CoreFrame.Partial,"personal gold requires its actual partial core and application-main observation");
        var amount=NativePlayedResources.decode(row.get("personal_gold"));
        RegistryJson.require(amount instanceof NativePlayedResources.Amount,"available personal gold requires its exact signed amount");
        return new Partial((CoreFrame.Partial)core,(NativePlayedResources.Amount)amount);
    }
}
