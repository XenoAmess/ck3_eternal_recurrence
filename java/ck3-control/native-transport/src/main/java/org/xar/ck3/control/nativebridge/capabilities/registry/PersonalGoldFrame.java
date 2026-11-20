package org.xar.ck3.control.nativebridge.capabilities.registry;

import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.semantic.NativePlayedResources;

/** Public personal-gold DATA only. It is neither treasury/monthly cash nor a complete gameplay observation. */
public sealed interface PersonalGoldFrame permits PersonalGoldFrame.Partial, PersonalGoldFrame.Unavailable {
    /** Historical aliases retain the V1 numeric wire contract. */
    String STEP="query-personal-gold-frame-v1";
    String CAPABILITY="game.query.personal-gold-frame.v1";
    String SCHEMA="ck3_1210_personal_gold_frame_v1";
    String ADAPTER="ck3-1.21.0-msvc-x64";
    String BACKEND="ck3-1.21.0-native-headless-main-thread";
    ExactCk3Build BUILD=ExactCk3Build.CK3_1210;
    Set<String> FIELDS=Set.of("step","schema","game_version","executable_sha256","adapter_id","backend","status",
            "personal_gold_available","application_main_observed","complete_snapshot","treasury_observed","monthly_flow_observed",
            "core_frame","personal_gold","unavailable_reason");
    enum Version {
        V1(STEP,CAPABILITY,SCHEMA,BUILD),
        V2("query-personal-gold-frame-v2","game.query.personal-gold-frame.v2","ck3_1210_personal_gold_frame_v2",
                ExactCk3Build.CK3_121003_STEAM_26785313);
        private final String step,capability,schema;
        private final ExactCk3Build build;
        Version(String step,String capability,String schema,ExactCk3Build build){
            this.step=step;this.capability=capability;this.schema=schema;this.build=build;
        }
        public String step(){return step;}
        public String capability(){return capability;}
        public String schema(){return schema;}
        public ExactCk3Build build(){return build;}
        public String adapter(){return build.coreFrameAdapterId();}
        public String backend(){return "ck3-"+build.version()+"-native-headless-main-thread";}
        public static Optional<Version> forStep(String step){
            for(var version:values())if(version.step.equals(step))return Optional.of(version);
            return Optional.empty();
        }
        public static Optional<Version> forSource(String gameVersion,String executableSha256,String adapter){
            for(var version:values())if(version.build.matches(gameVersion,executableSha256)&&version.adapter().equals(adapter))
                return Optional.of(version);
            return Optional.empty();
        }
    }
    Version version();
    default ExactCk3Build build(){return version().build();}
    CoreFrame coreFrame();
    boolean applicationMainObserved();

    record Partial(Version version,CoreFrame.Partial coreFrame,NativePlayedResources.Amount personalGold) implements PersonalGoldFrame {
        public Partial {
            Objects.requireNonNull(version);Objects.requireNonNull(coreFrame);Objects.requireNonNull(personalGold);
            RegistryJson.require(coreFrame.build()==version.build(),"personal gold requires its exact versioned core frame");
            var prefix=coreFrame.prefix();
            RegistryJson.require(prefix.mapReady()&&prefix.paused()&&prefix.hasPlayedCharacter()&&prefix.playedCharacterAlive(),
                    "personal gold requires the actual paused map and living played character");
        }
        public Partial(CoreFrame.Partial coreFrame,NativePlayedResources.Amount personalGold){this(Version.V1,coreFrame,personalGold);}
        @Override public boolean applicationMainObserved(){return true;}
    }
    record Unavailable(Version version,CoreFrame coreFrame,boolean applicationMainObserved,String reason) implements PersonalGoldFrame {
        public Unavailable {
            Objects.requireNonNull(version);Objects.requireNonNull(coreFrame);
            RegistryJson.require(coreFrame.build()==version.build(),"personal gold requires its exact versioned core frame");
            boolean coreObserved=coreFrame instanceof CoreFrame.Partial
                    ||((CoreFrame.Unavailable)coreFrame).applicationMainObserved();
            RegistryJson.require(applicationMainObserved==coreObserved,"personal gold and core application-main observations differ");
            RegistryJson.require(reason!=null&&!reason.isEmpty(),"personal gold unavailability requires its original reason");
        }
        public Unavailable(CoreFrame coreFrame,boolean applicationMainObserved,String reason){this(Version.V1,coreFrame,applicationMainObserved,reason);}
    }
    static PersonalGoldFrame decode(RawJson original) {
        var row=RegistryJson.object(original);
        var version=Version.forStep(RegistryJson.text(row.get("step"))).orElseThrow(()->new IllegalArgumentException("unknown personal-gold wire version"));
        return decode(row,version);
    }
    static PersonalGoldFrame decodeV2(RawJson original){return decode(RegistryJson.object(original),Version.V2);}
    static PersonalGoldFrame decode(RawJson original,Version expected){return decode(RegistryJson.object(original),Objects.requireNonNull(expected));}
    private static PersonalGoldFrame decode(com.fasterxml.jackson.databind.node.ObjectNode row,Version version) {
        RegistryJson.keys(row,FIELDS);
        RegistryJson.require(version.step().equals(RegistryJson.text(row.get("step")))&&version.schema().equals(RegistryJson.text(row.get("schema")))
                &&version.build().matches(RegistryJson.text(row.get("game_version")),RegistryJson.text(row.get("executable_sha256")))
                &&version.adapter().equals(RegistryJson.text(row.get("adapter_id")))&&version.backend().equals(RegistryJson.text(row.get("backend"))),
                "personal gold exact source mismatch");
        RegistryJson.require(!RegistryJson.bool(row.get("complete_snapshot"))&&!RegistryJson.bool(row.get("treasury_observed"))
                &&!RegistryJson.bool(row.get("monthly_flow_observed")),"personal gold cannot claim complete, treasury or monthly observations");
        var core=CoreFrame.decodeObject(RegistryJson.object(row.get("core_frame")));
        RegistryJson.require(core.build()==version.build(),"personal gold and nested core exact sources differ");
        boolean available=RegistryJson.bool(row.get("personal_gold_available"));
        boolean observed=RegistryJson.bool(row.get("application_main_observed"));
        if(!available) {
            RegistryJson.require("unavailable".equals(RegistryJson.text(row.get("status")))&&row.get("personal_gold").isNull(),
                    "unavailable personal gold must retain explicit null");
            return new Unavailable(version,core,observed,RegistryJson.text(row.get("unavailable_reason")));
        }
        RegistryJson.require("partial".equals(RegistryJson.text(row.get("status")))&&observed&&row.get("unavailable_reason").isNull()
                &&core instanceof CoreFrame.Partial,"personal gold requires its actual partial core and application-main observation");
        var amount=version==Version.V2?decodeV2Amount(row.get("personal_gold")):NativePlayedResources.decode(row.get("personal_gold"));
        RegistryJson.require(amount instanceof NativePlayedResources.Amount,"available personal gold requires its exact signed amount");
        return new Partial(version,(CoreFrame.Partial)core,(NativePlayedResources.Amount)amount);
    }
    private static NativePlayedResources.Amount decodeV2Amount(com.fasterxml.jackson.databind.JsonNode value){
        var amount=RegistryJson.object(value);RegistryJson.keys(amount,Set.of("raw","scale"));
        RegistryJson.require(RegistryJson.int32(amount.get("scale"))==NativePlayedResources.SCALE,"personal-gold V2 scale mismatch");
        String raw=RegistryJson.text(amount.get("raw"));
        RegistryJson.require(raw.length()<=20&&raw.matches("0|-?[1-9][0-9]*"),"canonical signed64 personal-gold V2 string required");
        return new NativePlayedResources.Amount(Long.parseLong(raw));
    }
}
