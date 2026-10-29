package org.xar.ck3.control.nativebridge.capabilities.interactions;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.ExactRef;
import static org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionJson.need;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.Context;

/** Actual finite original Driver failure. This is not a serializable permission or a public fault factory.
 * The Root consumer must check the identical installed producer, held Context and original selector
 * before mapping its finite Kind. Java source/frame/revision guards are not original Python faults. */
public final class InteractionOriginalFailure extends RuntimeException {
    private static final long serialVersionUID=1L;
    public enum Kind { MARRIAGE_CHOICE_NOT_IN_LATEST_QUERY }
    public enum CauseBranch { NO_RETAINED_QUERY, CHOICE_ABSENT }
    private static final String MESSAGE="native arrange-marriage choice is not in the latest query";
    private final transient InteractionCapabilities.MarriageFailureSource source;
    private final transient Context actual;
    private final String choice;
    private final CauseBranch branch;
    private final transient Optional<ExactRef> query;

    private InteractionOriginalFailure(InteractionCapabilities.MarriageFailureSource source,Context actual,
            String choice,CauseBranch branch,Optional<ExactRef> query) {
        super(MESSAGE);
        this.source=Objects.requireNonNull(source);this.actual=Objects.requireNonNull(actual);
        this.choice=Objects.requireNonNull(choice);this.branch=Objects.requireNonNull(branch);this.query=Objects.requireNonNull(query);
        need(choice.matches("[0-9]+-[0-9]+"),"original marriage selector required");
        need((branch==CauseBranch.CHOICE_ABSENT)==query.isPresent(),"actual marriage query provenance differs from the failing branch");
    }
    /** Package internal and gated by the facade's private-constructed source, never an arbitrary caller DTO. */
    static InteractionOriginalFailure choiceMissing(InteractionCapabilities.MarriageFailureSource source,Context actual,
            String choice,CauseBranch branch,Optional<ExactRef> query) {
        return new InteractionOriginalFailure(source,actual,choice,branch,query);
    }
    public Kind kind() { return Kind.MARRIAGE_CHOICE_NOT_IN_LATEST_QUERY; }
    public CauseBranch causeBranch() { return branch; }
    public String originalErrorClass() { return "BridgeUnavailableError"; }
    public String originalMessage() { return MESSAGE; }
    public String choiceId() { return choice; }
    public Context actualContext() { return actual; }
    /** Optional original READ reference is provenance only; it is never an original failure candidate. */
    public Optional<ExactRef> originalQuery() { return query; }
    public void requireProducer(InteractionCapabilities identical,Context actualFrame,String actualChoice) {
        source.requireProducer(identical);
        need(actual.equals(Objects.requireNonNull(actualFrame))&&choice.equals(Objects.requireNonNull(actualChoice)),
                "marriage original failure crossed its actual held context or selector");
    }
}
