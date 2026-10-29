package org.xar.ck3.control.wave2.events.uirecoveryidentity;

import static org.xar.ck3.control.wave2.events.uirecoveryidentity.UiRecoverySourceModel.*;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.IntegerIdentity;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.TextIdentity;

/** Pure implementation of stable_source_key: excludes live token, window pointer and rectangle. */
public final class UiRecoverySourceFingerprint implements UiRecoveryIdentityPort {
    @Override public Optional<Fingerprint> identify(Input input) {
        Objects.requireNonNull(input);
        SourceIdentity source = input.source();
        if (!sha(input.backendSha256()) || !sha(source.gameExeSha256())
                || source.backendSha256().filter(value -> !sha(value) || !value.equalsIgnoreCase(input.backendSha256())).isPresent()
                || source.catalogue().size() != input.displayedChoices().size()) { return Optional.empty(); }
        Map<String, DisplayedChoice> displayed = new HashMap<>();
        for (DisplayedChoice choice : input.displayedChoices()) {
            if (displayed.putIfAbsent(legacyIdentity(choice.identity()), choice) != null) { return Optional.empty(); }
        }
        List<NormalizedChoice> choices = new ArrayList<>();
        for (int index = 0; index < source.catalogue().size(); index++) {
            CatalogueChoice catalogue = source.catalogue().get(index);
            DisplayedChoice shown;
            if (catalogue.choiceId().hasValue()) { shown = displayed.get(legacyIdentity(catalogue.choiceId().value())); }
            else if (catalogue.choiceId().presence() == org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.Presence.NULL) {
                return Optional.empty();
            } else { shown = input.displayedChoices().get(index); }
            if (shown == null) { return Optional.empty(); }
            List<Callback> callbacks = new ArrayList<>(catalogue.callbacks());
            callbacks.sort(Comparator.comparing(StableSourceCanonical::callback, StableSourceCanonical::compareUnicode));
            Optional<String> role = catalogue.role().hasValue() ? Optional.of(catalogue.role().value())
                    : catalogue.role().presence() == org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.Presence.NULL
                    ? Optional.empty() : shown.role();
            choices.add(new NormalizedChoice(catalogue.runtimeName(), catalogue.widgetVtable(), role, shown.label(), callbacks));
        }
        choices.sort(Comparator.comparing(StableSourceCanonical::choice, StableSourceCanonical::compareUnicode));
        StableSource stable = new StableSource(source.gameExeSha256().toLowerCase(Locale.ROOT), input.backendSha256().toLowerCase(Locale.ROOT),
                source.nativeAdapterId(), source.rootRuntimeName(), source.rootType(), source.rootVtable(), choices);
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256").digest(StableSourceCanonical.source(stable).getBytes(StandardCharsets.UTF_8));
            return Optional.of(new Fingerprint(HexFormat.of().formatHex(digest), stable));
        } catch (NoSuchAlgorithmException error) { throw new IllegalStateException("Java SHA-256 unavailable", error); }
    }
    private static String legacyIdentity(org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.ChoiceIdentity identity) {
        return identity instanceof TextIdentity text ? text.value() : ((IntegerIdentity) identity).value().toString();
    }
    private static boolean sha(String value) { return value.matches("[0-9a-fA-F]{64}"); }
}
