package org.xar.ck3.control.nativebridge;

import java.io.IOException;
import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.NativeRequest;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactCk3Build;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.CoreFrame;

/** Fixed RMTM read/navigation DATA. No TitleID, arbitrary interaction, Enact or Send route. */
public final class CurrentRmtmObservation {
    public static final String SCHEMA="ck3.rmtm_observation.current267_request.v1";
    public static final String SOURCE_SCHEMA="ck3.rmtm_observation.current267_source.v1";
    public static final String RESULT_SCHEMA="ck3.rmtm_observation.current267_result.v1";
    public static final String BACKEND="ck3-1.21.0.3-native-application-main-rmtm-observation";
    public enum Kind {TITLE_PHASE,COUNCIL,BUDGET,OFFER;
        public String wire(){return name().toLowerCase(java.util.Locale.ROOT);}
        public static Kind parse(String s)throws IOException{for(var k:values())if(k.wire().equals(s))return k;throw new IOException("Unknown RMTM observation kind");}
    }
    public enum Phase {D3,PREDEATH,POSTDEATH;
        public String wire(){return name().toLowerCase(java.util.Locale.ROOT);}
        public static Phase parse(String s)throws IOException{for(var k:values())if(k.wire().equals(s))return k;throw new IOException("Unknown RMTM physical phase");}
    }
    public enum OfferTarget {RELEASED_A,RELEASED_B;
        public String wire(){return name().toLowerCase(java.util.Locale.ROOT);}
        public static OfferTarget parse(String s)throws IOException{for(var k:values())if(k.wire().equals(s))return k;throw new IOException("Unknown fixed RMTM Offer target");}
    }
    public enum Action {
        QUERY_TITLE_PHASE("query_title_phase","query-rmtm-title-phase-current-v1","game.query.current-rmtm-title-phase.v1",Kind.TITLE_PHASE),
        QUERY_COUNCIL("query_council","query-rmtm-council-current-v1","game.query.current-rmtm-council.v1",Kind.COUNCIL),
        QUERY_BUDGET("query_budget","query-rmtm-budget-current-v1","game.query.current-rmtm-budget.v1",Kind.BUDGET),
        OPEN_BUDGET("open_budget","open-rmtm-budget-current-v1","game.command.open-current-rmtm-budget.v1",Kind.BUDGET),
        CANCEL_BUDGET("cancel_budget","cancel-rmtm-budget-current-v1","game.command.cancel-current-rmtm-budget.v1",Kind.BUDGET),
        QUERY_OFFER("query_offer","query-rmtm-offer-current-v1","game.query.current-rmtm-offer.v1",Kind.OFFER),
        OPEN_OFFER("open_offer","open-rmtm-offer-current-v1","game.command.open-current-rmtm-offer.v1",Kind.OFFER),
        CANCEL_OFFER("cancel_offer","cancel-rmtm-offer-current-v1","game.command.cancel-current-rmtm-offer.v1",Kind.OFFER);
        private final String wire,step,capability;private final Kind kind;
        Action(String w,String s,String c,Kind k){wire=w;step=s;capability=c;kind=k;}
        public String wire(){return wire;}public String step(){return step;}public String capability(){return capability;}public Kind kind(){return kind;}
        public boolean queryOnly(){return this==QUERY_TITLE_PHASE||this==QUERY_COUNCIL||this==QUERY_BUDGET||this==QUERY_OFFER;}
        public Action queryAction(){return kind==Kind.BUDGET?QUERY_BUDGET:kind==Kind.OFFER?QUERY_OFFER:this;}
        public static Action parse(String s)throws IOException{for(var k:values())if(k.wire.equals(s))return k;throw new IOException("Unknown RMTM observation action");}
    }
    private CurrentRmtmObservation() { }
    public static NativeRequest request(CoreFrame.Partial actual,Action action,BigInteger provider,BigInteger query,Optional<Phase> phase,Optional<OfferTarget> target){
        Objects.requireNonNull(actual);Objects.requireNonNull(action);Objects.requireNonNull(phase);Objects.requireNonNull(target);
        CurrentRmtmActorTransition.requireCore(actual.prefix());CurrentRmtmActorTransition.unsigned(provider,false);CurrentRmtmActorTransition.unsigned(query,false);
        StrictJson.require(actual.build()==ExactCk3Build.CK3_121003_STEAM_26785313,"Exact current267 Core required");
        StrictJson.require((action==Action.QUERY_TITLE_PHASE)==phase.isPresent()&&(action.kind()==Kind.OFFER)==target.isPresent(),"Exact phase/target union; no caller TitleID or generic selector");
        StrictJson.require(action.queryOnly()?provider.signum()==0&&query.signum()==0:provider.signum()>0&&query.signum()>0,"Original private query lease required only for actual UI entry");
        var b=actual.build();var claim=StrictJson.object().put("schema",SCHEMA).put("game_version",b.version()).put("executable_sha256",b.executableSha256()).put("adapter_id",b.coreFrameAdapterId())
                .put("backend",BACKEND).put("action",action.wire()).put("provider_generation",provider).put("query_sequence",query);
        claim.set("expected_core",CurrentRmtmActorTransition.core(actual.prefix()));
        if(phase.isPresent())claim.put("phase",phase.orElseThrow().wire());else claim.putNull("phase");
        if(target.isPresent())claim.put("offer_target",target.orElseThrow().wire());else claim.putNull("offer_target");
        var fields=StrictJson.object();fields.set("arguments",StrictJson.object());fields.set("rmtm_observation",claim);
        return new NativeRequest(action.step(),action.capability(),new RawJson(StrictJson.canonical(fields)));
    }
}
