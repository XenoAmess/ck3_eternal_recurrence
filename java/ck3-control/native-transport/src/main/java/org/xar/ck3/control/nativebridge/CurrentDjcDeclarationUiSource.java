package org.xar.ck3.control.nativebridge;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.contracts.StrictJson;

/** Actual native observation DATA, including negative/unobserved predicates. It never authorizes Open/Send on its own. */
public record CurrentDjcDeclarationUiSource(NativeCharacterId target,CurrentDjcTargetWarQueryResult.CasusBelliKey casusBelli,
        boolean interactionDefinitionVerified,int loadedInterface,Optional<Boolean> nativeConfirmation,Optional<Boolean> nativeIsValid,
        boolean openAdmissible,boolean residentAvailable,boolean namedRootBound,boolean windowVisible,boolean windowEnabled,
        Optional<NativeCharacterId> actor,Optional<NativeCharacterId> recipient,Optional<NativeCharacterId> additionalRole,
        Optional<SelectedTuple> selected,List<Choice> choices,Optional<Boolean> nativeCanSend,boolean sendAdmissible,
        boolean warningSourceAvailable,Optional<Boolean> nativeCanAccept,boolean acceptAdmissible) {
    public record SelectedTuple(CurrentDjcTargetWarQueryResult.CasusBelliKey casusBelli,Optional<NativeCharacterId> claimant,
            List<Integer> targetTitleIds,List<Integer> extraConfigurationIds,boolean sourceRowEnabled) {
        public SelectedTuple {
            Objects.requireNonNull(casusBelli);Objects.requireNonNull(claimant);targetTitleIds=List.copyOf(targetTitleIds);extraConfigurationIds=List.copyOf(extraConfigurationIds);
            StrictJson.require(targetTitleIds.size()<=10000&&extraConfigurationIds.size()<=10000,"Bounded actual native tuple vectors required");
            StrictJson.require(targetTitleIds.stream().noneMatch(n->n==-1),"Absent title-1 is invalid; extra IDs keep their own signed domain");
            // Do not sort/deduplicate, reinterpret signed bits or label extra IDs as titles/characters.
        }
    }
    public record Choice(BigInteger nativeToken,SelectedTuple tuple) {
        public Choice {Objects.requireNonNull(nativeToken);Objects.requireNonNull(tuple);StrictJson.require(nativeToken.signum()>=0&&nativeToken.compareTo(NativeWire.UINT64_MAX)<=0,"Exact unsigned64 native token DATA required");}
    }
    public CurrentDjcDeclarationUiSource {
        Objects.requireNonNull(target);Objects.requireNonNull(casusBelli);Objects.requireNonNull(nativeConfirmation);Objects.requireNonNull(nativeIsValid);
        Objects.requireNonNull(actor);Objects.requireNonNull(recipient);Objects.requireNonNull(additionalRole);Objects.requireNonNull(selected);choices=List.copyOf(choices);Objects.requireNonNull(nativeCanSend);Objects.requireNonNull(nativeCanAccept);
        StrictJson.require(loadedInterface>=0&&loadedInterface<=255,"Actual uint8 loaded interface required");
        // SourceAvailable denotes actual observation, not truth of these predicates or permission for a callback.
    }
    public boolean permitsOpen(){return openAdmissible&&interactionDefinitionVerified&&loadedInterface==4&&nativeConfirmation.orElse(false)&&nativeIsValid.orElse(false);}
    boolean permitsSelection(Choice actual){return residentAvailable&&namedRootBound&&windowVisible&&windowEnabled&&choices.stream().anyMatch(c->c==actual)
            &&actual.nativeToken().signum()>0&&actual.tuple().sourceRowEnabled()&&actual.tuple().casusBelli()==casusBelli;}
    public boolean permitsSend(){return sendAdmissible&&residentAvailable&&namedRootBound&&windowVisible&&windowEnabled&&nativeCanSend.orElse(false)&&selected.filter(s->s.casusBelli()==casusBelli&&s.sourceRowEnabled()).isPresent();}
    public boolean permitsAccept(){return acceptAdmissible&&warningSourceAvailable&&nativeCanAccept.orElse(false);}
}
