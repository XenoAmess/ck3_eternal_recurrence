package org.xar.ck3.control.nativebridge.capabilities.gui;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import static org.xar.ck3.control.nativebridge.capabilities.gui.GuiJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.gui.GuiModels.*;

/** Actual archived White READ roles. DATA never grants a writer/session or permission. */
public final class GuiWhiteOriginals {
    public static final String BUSINESS_BEFORE = "_gui_before_business_read";
    public static final String TEXT_BEFORE = "_gui_before_text_read";
    public record Before(PlanningReadReceipt business, PlanningReadReceipt text) {
        public Before { Objects.requireNonNull(business); Objects.requireNonNull(text); }
    }
    private GuiWhiteOriginals() { }

    public static void retainBefore(ObjectNode fields, PlanningReadResult.Known<WhiteBusiness> business,
            PlanningReadResult.Known<WhiteText> text) {
        fields.set(BUSINESS_BEFORE, business.originalReceipt().toJson());
        fields.set(TEXT_BEFORE, text.originalReceipt().toJson());
    }

    /** Reopens the exact originals; preparation and cold replay never resample the before values. */
    public static Before before(ActionCommand command, GuiReads contracts, ActionPorts.OutcomeArchive archive) {
        Context context = GuiReads.context(command);
        ObjectNode fields = arguments(command.arguments());
        ExactRef businessRef = ExactRef.fromJson(required(fields, BUSINESS_BEFORE));
        ExactRef textRef = ExactRef.fromJson(required(fields, TEXT_BEFORE));
        need(!businessRef.equals(textRef), "White before requires distinct original READs");
        PlanningReadReceipt business = archive.loadRead(businessRef), text = archive.loadRead(textRef);
        need(archive.readReferenceOf(business).equals(businessRef) && archive.readReferenceOf(text).equals(textRef),
                "White before READ custody changed");
        NativeRecordedEvidenceVerifier.requireRead(business, archive);
        NativeRecordedEvidenceVerifier.requireRead(text, archive);
        requireRole(business, context, contracts.whiteBusiness);
        requireRole(text, context, contracts.whiteText);
        WhiteBusiness values = contracts.whiteBusiness.decode(business);
        WhiteText texts = contracts.whiteText.decode(text);
        need(values.availability().available() && values.allIntegers() && texts.availability().available(),
                "actual White before business/text unavailable");
        ObjectNode suppliedValues = obj(required(fields, "_gui_before_values"));
        ObjectNode suppliedTexts = obj(required(fields, "_gui_before_texts"));
        need(suppliedValues.size() == Variable.values().length && suppliedTexts.size() == TextName.values().length,
                "complete actual White before values/text required");
        for (Variable key : Variable.values()) equal(suppliedValues, key.wire(), values.integer(key));
        for (TextName key : TextName.values()) equal(suppliedTexts, key.wire(), texts.text(key));
        boolean age = command.operation().value().equals("click-white-control-v1");
        need(age || command.operation().value().equals("click-white-numeric-control-v1"), "fixed White before operation required");
        Variable target = age ? Variable.AGE : Variable.valueOf(NumericControl.parse(text(fields, "control")).name());
        BigInteger expected = integer(fields, age ? "expected_before_age" : "expected_before_value");
        need(values.integer(target).equals(expected) && texts.text(TextName.valueOf(target.name())).equals(expected.toString()),
                "White actual before business/text differs from requested value");
        if (!age) equal(suppliedTexts, TextName.PRICE.wire(), text(fields, "expected_before_price_text"));
        return new Before(business, text);
    }

    public static <T> T requireRole(PlanningReadReceipt original, Context context, ReadContract<T> contract) {
        PlanningReadRequest expected = new PlanningReadRequest(context.before(), context.source(), context.sessionId(),
                contract.operation(), arguments(GuiReads.metadata(context, boundFields(context))), context.deadline());
        need(original.contractId().equals(contract.contractId()) && original.request().equals(expected),
                "White READ role/request/source/frame changed");
        return contract.decode(original);
    }

    public static void requireBeforeSubmission(Before before, ActionState.Attempt attempt,
            NativeActionPort.AckReceived actualSubmission) {
        NativeRequestChronology.requireBeforeSubmission(before.business(), attempt, actualSubmission);
        NativeRequestChronology.requireBeforeSubmission(before.text(), attempt, actualSubmission);
    }

    /** The original native ACK proves one callback; it never proves the independent business result. */
    public static void requireAck(ObjectNode ack, Context context, ObjectNode fields, String step) {
        equal(ack, "schema", "ck3-native-white-control-action-v1"); equal(ack, "step", step);
        equal(ack, "control", text(fields, "control"));
        if (ack.has("backend_id")) equal(ack, "backend_id", "native-headless");
        need(!bool(ack, "read_only") && !bool(ack, "selected_down_available") && !bool(ack, "postcondition_verified"),
                "White native ACK cannot grant independent/down/read credit");
        yes(ack, "available", "source_abi_pins_verified", "receiver_qualified", "gui_owner_binding_verified",
                "frame_verified", "dispatch_attempted", "dispatch_invoked", "native_after_read");
        bool(ack, "native_handled"); equal(ack, "unavailable_reason", "");
        equal(ack, "game_pid", BigInteger.valueOf(context.before().game().pid()));
        equal(ack, "native_revision", context.before().frame().identity().nativeRevision());
        equal(ack, "connection_generation", context.connectionGeneration());
        equal(ack, "played_character_id", context.before().frame().identity().player());
        equal(ack, "date_raw", context.before().frame().identity().dateRaw());
        String beforeField = step.equals("click-white-control-v1") ? "expected_before_age" : "expected_before_value";
        equal(ack, beforeField, integer(fields, beforeField));
        if (step.equals("click-white-numeric-control-v1")) yes(ack, "before_price_bound");
        String path = text(ack, "target_child_path");
        need(path.startsWith("0/") && path.split("/", -1).length <= 64, "White receiver outside original inner modal");
        for (String segment : path.split("/", -1))
            need(segment.matches("[0-9]+") && new BigInteger(segment).compareTo(BigInteger.valueOf(2048)) <= 0,
                    "White receiver path component invalid");
    }

    /** Shared live observer/cold verifier arithmetic; values come only from the two typed actual READs. */
    public static List<ExpectedValue> actual(ObjectNode fields, WhiteBusiness business, WhiteText text, String step) {
        need(business.availability().available() && business.allIntegers() && text.availability().available(),
                "White independent after business/text unavailable");
        Variable variable = step.equals("click-white-control-v1") ? Variable.AGE
                : Variable.valueOf(NumericControl.parse(GuiJson.text(fields, "control")).name());
        TextName widget = TextName.valueOf(variable.name());
        ObjectNode before = obj(required(fields, "_gui_before_values")), texts = obj(required(fields, "_gui_before_texts"));
        boolean unrelated = true;
        for (Variable key : Variable.values()) if (key != variable)
            unrelated &= business.integer(key).equals(integer(before, key.wire()));
        if (!step.equals("click-white-control-v1")) {
            need(!text.text(TextName.PRICE).isEmpty() && !text.text(TextName.GOLD).isEmpty(),
                    "White numeric requires actual price and gold strings");
            for (TextName key : TextName.values()) if (key != widget && key != TextName.PRICE)
                unrelated &= text.text(key).equals(GuiJson.text(texts, key.wire()));
        }
        return List.of(new ExpectedInteger(new FieldKey("gui.white_value"), business.integer(variable)),
                new ExpectedText(new FieldKey("gui.white_text"), text.text(widget)),
                new ExpectedBoolean(new FieldKey("gui.unrelated_business_unchanged"), unrelated));
    }
}
