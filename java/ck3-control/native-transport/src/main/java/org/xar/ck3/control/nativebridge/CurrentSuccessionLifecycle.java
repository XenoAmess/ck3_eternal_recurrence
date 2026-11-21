package org.xar.ck3.control.nativebridge;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;

/** Current default succession request DATA. Only the identical transport's actual private query may authorize Continue. */
public final class CurrentSuccessionLifecycle {
    public static final String REQUEST_SCHEMA="ck3.succession_lifecycle.current267_request.v1";
    public static final String RESULT_SCHEMA="ck3.succession_lifecycle.current267_result.v1";
    public static final String WORLD_SCHEMA="ck3.succession_world.current267_prefix.v1";
    public static final String SOURCE_SCHEMA="ck3.succession_default_source.current267.v1";
    public static final String BACKEND="ck3-1.21.0.3-native-application-main-succession";
    public enum Action {
        QUERY_DEFAULT("query_default","query-current-succession-default-v1","game.query.current-succession-default.v1"),
        CONTINUE_DEFAULT("continue_default","continue-current-succession-default-v1","game.command.current-succession-default-continue.v1");
        private final String wire,step,capability;
        Action(String wire,String step,String capability){this.wire=wire;this.step=step;this.capability=capability;}
        public String wire(){return wire;}public String step(){return step;}public String capability(){return capability;}
    }
    public enum PlayerRelation { PENDING_PREDECESSOR,HEIR_ALREADY_ASSIGNED,UNASSIGNED_DURING_TRANSITION }
    /** Lifecycle observation, deliberately not a CoreFrame/Partial or a CoreReceived receipt. */
    public record WorldBefore(int dateRaw,int speed,boolean paused,int localPlayerId,boolean mapReady,
            boolean hasPlayedCharacter,Optional<NativeCharacterId> playedCharacter,boolean playedCharacterAlive) {
        public WorldBefore {Objects.requireNonNull(playedCharacter);StrictJson.require(hasPlayedCharacter?playedCharacter.isPresent():playedCharacter.isEmpty()&&!playedCharacterAlive,"Actual complete lifecycle world player fields must agree; map does not infer assignment");}
    }
    /** Source DATA alone is not authority; the wire emits it only after all native source gates qualify. */
    public record SourceBefore(Optional<NativeCharacterId> deadCharacter,Optional<NativeCharacterId> continueCharacter,
            PlayerRelation playerRelation,boolean deadCharacterDead,boolean continueCharacterAlive,boolean handlerSourceVerified,
            boolean namedRootBound,boolean windowVisible,boolean windowEnabled,boolean defaultButtonAdmissible,
            boolean defaultNativeRoute,boolean stableTwoPassVerified) {
        public SourceBefore {Objects.requireNonNull(deadCharacter);Objects.requireNonNull(continueCharacter);Objects.requireNonNull(playerRelation);}
        public boolean qualifiedRelation(WorldBefore actual) {
            Objects.requireNonNull(actual);
            if(deadCharacter.isEmpty()||continueCharacter.isEmpty()||deadCharacter.equals(continueCharacter)||!deadCharacterDead||!continueCharacterAlive
                    ||!handlerSourceVerified||!namedRootBound||!windowVisible||!windowEnabled||!defaultButtonAdmissible||!defaultNativeRoute||!stableTwoPassVerified)return false;
            return switch(playerRelation) {
                case PENDING_PREDECESSOR -> actual.hasPlayedCharacter()&&!actual.playedCharacterAlive()&&actual.playedCharacter().equals(deadCharacter);
                case HEIR_ALREADY_ASSIGNED -> actual.hasPlayedCharacter()&&actual.playedCharacterAlive()&&actual.playedCharacter().equals(continueCharacter);
                case UNASSIGNED_DURING_TRANSITION -> !actual.hasPlayedCharacter()&&!actual.playedCharacterAlive()&&actual.playedCharacter().isEmpty();
            };
        }
    }
    private CurrentSuccessionLifecycle() { }
    public static NativeRequest queryRequest(){return request(Action.QUERY_DEFAULT,BigInteger.ZERO,BigInteger.ZERO,Optional.empty(),Optional.empty());}
    static NativeRequest continueRequest(BigInteger actualProvider,BigInteger actualQuery,NativeCharacterId actualDead,NativeCharacterId actualContinue){
        return request(Action.CONTINUE_DEFAULT,actualProvider,actualQuery,Optional.of(Objects.requireNonNull(actualDead)),Optional.of(Objects.requireNonNull(actualContinue)));
    }
    private static NativeRequest request(Action action,BigInteger provider,BigInteger query,Optional<NativeCharacterId> dead,Optional<NativeCharacterId> heir) {
        Objects.requireNonNull(action);Objects.requireNonNull(provider);Objects.requireNonNull(query);Objects.requireNonNull(dead);Objects.requireNonNull(heir);
        StrictJson.require(provider.signum()>=0&&provider.compareTo(NativeWire.UINT64_MAX)<=0&&query.signum()>=0&&query.compareTo(NativeWire.UINT64_MAX)<=0,"Canonical uint64 native lease required");
        if(action==Action.QUERY_DEFAULT)StrictJson.require(provider.signum()==0&&query.signum()==0&&dead.isEmpty()&&heir.isEmpty(),"Query cannot supply source IDs or authority");
        else StrictJson.require(provider.signum()>0&&query.signum()>0&&dead.isPresent()&&heir.isPresent()&&!dead.equals(heir),"Continue DATA must preserve distinct actual native IDs and original nonzero lease");
        var b=ExactCk3Build.CK3_121003_STEAM_26785313;
        var claim=StrictJson.object().put("schema",REQUEST_SCHEMA).put("game_version",b.version()).put("executable_sha256",b.executableSha256())
                .put("adapter_id",b.coreFrameAdapterId()).put("backend",BACKEND).put("action",action.wire()).put("provider_generation",provider.toString()).put("query_sequence",query.toString())
                .put("expected_dead_character_id",dead.map(NativeCharacterId::value).orElse(-1)).put("expected_continue_character_id",heir.map(NativeCharacterId::value).orElse(-1));
        var fields=StrictJson.object();fields.set("succession_lifecycle",claim);fields.set("arguments",StrictJson.object());
        return new NativeRequest(action.step(),action.capability(),new RawJson(StrictJson.canonical(fields)));
    }
}
