package org.xar.ck3.control.g2.m6.prisonerransom;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleaseCollectionProjection12003;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreview12003;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003;
import org.xar.ck3.control.wave2.prisoners.releasepreview.ReleasePreviewValues12003.FrameBinding;

/** Source-bound read-only explanation of existing prisoner observations. No ranking or action authority. */
public final class PrisonerVanillaResearch {
    public static final String STOCK_SHA256 = "1bb43b3c2061212af8d41b11314ff4e569af2a3506319f820d05877a7762abc5";
    public static final int STOCK_BYTES = 222_958;
    public static final String EXACT_BUILD = "1.20.0.4";
    public static final String EXE_SHA256 = "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
    public static final int RANSOM_AUTHORED_OPTION_COUNT = org.xar.ck3.control.wave2.prisoners.ransomquote.RansomOptionMask12004.AUTHORED_OPTION_COUNT;
    public static final int RANSOM_OPTION_MASK_MAXIMUM = org.xar.ck3.control.wave2.prisoners.ransomquote.RansomOptionMask12004.MAXIMUM_MASK;
    private static final Set<String> SECTION_KEYS = Set.of("redirect", "ai_targets", "ai_frequency_by_tier",
            "ai_target_quick_trigger", "is_shown", "is_valid", "is_valid_showing_failures_only",
            "send_option", "auto_accept", "ai_accept", "ai_will_do", "on_accept", "on_decline", "cost");
    private static final Set<String> AVAILABLE_QUOTE_KEYS = Set.of("private_build", "read_only", "advertised",
            "action_surface_present", "status", "unavailable_reason", "snapshot_id", "public_revision",
            "native_revision", "proof_epoch", "date_raw", "definition_key", "jailer_character_id",
            "payer_character_id", "prisoner_character_id", "selected_option", "can_send", "quoted_gold_raw",
            "raw_scale", "recipient_acceptance_raw", "recipient_answer_status_raw", "would_accept_now",
            "amount_is_acceptance_time_quote");
    private static final Set<String> UNAVAILABLE_QUOTE_KEYS = Set.of("private_build", "read_only", "advertised",
            "action_surface_present", "status", "unavailable_reason");

    private PrisonerVanillaResearch() { }

    public enum Interaction {
        RANSOM("ransom_interaction"), PAY_RANSOM("pay_ransom_interaction"), SELF_RANSOM("ransom_me_interaction"),
        RELEASE("release_from_prison_interaction"), EXECUTE("execute_prisoner_interaction");
        private final String key;
        Interaction(String key) { this.key = key; }
        public String key() { return key; }
    }
    public enum Operator {
        ASSIGN("="), OPTIONAL("?="), DIFFERENT("!="), LESS("<"), LESS_EQUAL("<="), GREATER(">"), GREATER_EQUAL(">=");
        private final String token;
        Operator(String token) { this.token = token; }
        public String token() { return token; }
        static Operator parse(String token) {
            for (Operator operator : values()) if (operator.token.equals(token)) return operator;
            throw new IllegalArgumentException("unrecognized script operator");
        }
    }
    public enum Knowledge { OBSERVED_TRUE, OBSERVED_FALSE, UNKNOWN }
    public enum Gate { NOT_EVALUATED, UNAVAILABLE, REFUSED, ACCEPTED_READ_ONLY }
    public enum Option { GOLD, CURRENT_GOLD }
    public enum EdgeState { STATIC_CONFIRMED, UNKNOWN }
    public record Span(int startOffset, int endOffset, int startLine, int endLine) {
        public Span {
            StrictJson.require(startOffset >= 0 && endOffset > startOffset && startLine > 0 && endLine >= startLine,
                    "exact nonempty script span required");
        }
    }
    public sealed interface Node permits Atom, Group, Assignment { Span span(); }
    public record Atom(String text, boolean quoted, Span span) implements Node {
        public Atom { Objects.requireNonNull(text); if (!text.isEmpty()) StrictJson.text(text); Objects.requireNonNull(span); }
    }
    public record Group(List<Node> children, Span span) implements Node {
        public Group { children = List.copyOf(children); Objects.requireNonNull(span); }
    }
    public record Assignment(String key, Operator operator, Node value, Span span) implements Node {
        public Assignment {
            StrictJson.text(key); Objects.requireNonNull(operator); Objects.requireNonNull(value); Objects.requireNonNull(span);
        }
    }
    public record Source(G2Source provenance, String executableSha256) {
        public Source {
            Objects.requireNonNull(provenance);
            StrictJson.require(provenance.sourceRef().bytes() == STOCK_BYTES && STOCK_SHA256.equals(provenance.sourceRef().sha256())
                    && EXACT_BUILD.equals(provenance.exactBuild()) && EXE_SHA256.equals(executableSha256),
                    "exact current script and .4 build identity required");
        }
    }
    public record SourceSection(String key, int occurrence, Span span, String sha256, Node expression) {
        public SourceSection {
            StrictJson.text(key); StrictJson.require(occurrence >= 0, "nonnegative section occurrence required");
            Objects.requireNonNull(span); digest(sha256); Objects.requireNonNull(expression);
        }
    }
    public record InteractionTree(Interaction interaction, Span span, List<SourceSection> sections) {
        public InteractionTree { Objects.requireNonNull(interaction); Objects.requireNonNull(span); sections = List.copyOf(sections); }
        public List<SourceSection> sections(String key) { return sections.stream().filter(section -> section.key().equals(key)).toList(); }
    }
    public record Edge(String from, String to, EdgeState state, String sourceKey, String unresolvedQuestion) {
        public Edge {
            StrictJson.text(from); StrictJson.text(to); Objects.requireNonNull(state); StrictJson.text(sourceKey);
            StrictJson.require(state == EdgeState.UNKNOWN ? unresolvedQuestion != null && !unresolvedQuestion.isEmpty()
                    : unresolvedQuestion == null, "unknown edges require a concrete question");
        }
    }
    public record Catalog(Source source, List<InteractionTree> interactions, List<Edge> edges) {
        public Catalog {
            Objects.requireNonNull(source); interactions = List.copyOf(interactions); edges = List.copyOf(edges);
            StrictJson.require(interactions.size() == Interaction.values().length, "all five prisoner opportunities required");
            for (Interaction kind : Interaction.values()) StrictJson.require(
                    interactions.stream().filter(tree -> tree.interaction() == kind).count() == 1, "one tree per interaction required");
        }
        public InteractionTree tree(Interaction kind) { return interactions.stream().filter(tree -> tree.interaction() == kind).findFirst().orElseThrow(); }
    }

    /** Parse actual stock text, preserving repeated modifiers, operand spelling, scope and source order. */
    public static Catalog inspect(byte[] stockBytes, Source source) {
        Objects.requireNonNull(source); Objects.requireNonNull(stockBytes);
        StrictJson.require(stockBytes.length == source.provenance().sourceRef().bytes()
                && sha256(stockBytes).equals(source.provenance().sourceRef().sha256()), "stock source drift");
        String text = utf8(stockBytes);
        Group root = new Parser(text).parse();
        List<InteractionTree> trees = new ArrayList<>();
        for (Interaction interaction : Interaction.values()) {
            List<Assignment> matches = root.children().stream().filter(Assignment.class::isInstance).map(Assignment.class::cast)
                    .filter(entry -> entry.key().equals(interaction.key())).toList();
            StrictJson.require(matches.size() == 1 && matches.getFirst().value() instanceof Group,
                    "one original interaction block required: " + interaction.key());
            Assignment block = matches.getFirst();
            List<SourceSection> sections = new ArrayList<>();
            for (Node child : ((Group) block.value()).children()) {
                if (child instanceof Assignment entry && SECTION_KEYS.contains(entry.key())) {
                    int occurrence = (int) sections.stream().filter(section -> section.key().equals(entry.key())).count();
                    Span span = entry.span();
                    sections.add(new SourceSection(entry.key(), occurrence, span,
                            sha256(text.substring(span.startOffset(), span.endOffset()).getBytes(StandardCharsets.UTF_8)), entry.value()));
                }
            }
            for (String required : List.of("ai_targets", "ai_frequency_by_tier", "ai_will_do", "is_shown")) {
                StrictJson.require(sections.stream().anyMatch(section -> section.key().equals(required)), "stock opportunity section missing: " + required);
            }
            if (interaction == Interaction.RANSOM) {
                org.xar.ck3.control.wave2.prisoners.ransomquote.RansomOptionMask12004.requireAuthoredOptionCount(
                        (int) sections.stream().filter(section -> section.key().equals("send_option")).count());
            }
            trees.add(new InteractionTree(interaction, block.span(), sections));
        }
        List<Edge> edges = List.of(
                new Edge("independent-opportunity", "authored-candidates", EdgeState.STATIC_CONFIRMED, "ai_targets", null),
                new Edge("authored-candidates", "redirected-roles", EdgeState.STATIC_CONFIRMED, "redirect", null),
                new Edge("redirected-roles", "player-legality", EdgeState.STATIC_CONFIRMED, "is_shown/is_valid_showing_failures_only/send_option", null),
                new Edge("redirected-roles", "sender-willingness", EdgeState.STATIC_CONFIRMED, "ai_will_do", null),
                new Edge("player-legality", "recipient-answer", EdgeState.STATIC_CONFIRMED, "ai_accept/auto_accept", null),
                new Edge("recipient-answer", "acceptance-time-effects", EdgeState.STATIC_CONFIRMED, "on_accept", null),
                new Edge("human-refusal", "ten-year-prisoner-flag", EdgeState.STATIC_CONFIRMED, "on_decline", null),
                new Edge("sender-willingness", "native-opportunity-arbitration", EdgeState.UNKNOWN, "native scheduler",
                        "Locate the current .4 caller consuming ai_frequency_by_tier and comparing different interaction opportunities."),
                new Edge("native-opportunity-arbitration", "retained-custody-utility", EdgeState.UNKNOWN, "native retention comparator",
                        "No independently evaluated retain utility or cross-action comparator has been closed."),
                new Edge("ten-year-prisoner-flag", "opportunity-reevaluation", EdgeState.UNKNOWN, "native cache invalidation",
                        "The script writes a ten-year flag; exact scheduler invalidation and reevaluation timing remain unlocated."));
        return new Catalog(source, trees, edges);
    }

    public sealed interface RansomQuote permits AvailableQuote, UnavailableQuote { }
    public record AvailableQuote(FrameBinding frame, BigInteger proofEpoch, long payerCharacterId, Option option,
                                 long quotedGoldRaw, long recipientAcceptanceRaw, int answerStatusRaw) implements RansomQuote {
        public AvailableQuote {
            Objects.requireNonNull(frame); ReleasePreviewValues12003.unsigned64(proofEpoch, "quote epoch");
            StrictJson.require(payerCharacterId > 0 && payerCharacterId <= ReleasePreviewValues12003.UINT32_MAX
                    && payerCharacterId != frame.playerCharacterId(), "redirected payer must be another full uint32 ID");
            Objects.requireNonNull(option); StrictJson.require(quotedGoldRaw > 0 && answerStatusRaw >= 0 && answerStatusRaw <= 2, "native ordinary quote required");
        }
        public boolean wouldAcceptNow() { return answerStatusRaw != 2; }
        public boolean amountIsAcceptanceTimeQuote() { return option == Option.CURRENT_GOLD; }
    }
    public sealed interface QuoteDiagnostic permits NoQuoteDiagnostic, OptionCounts, OptionMask { }
    public record NoQuoteDiagnostic() implements QuoteDiagnostic { }
    public record OptionCounts(int definitionCount, Integer contextCount) implements QuoteDiagnostic { }
    public record OptionMask(int requestedOptionIndex, int observedOptionMaskBits) implements QuoteDiagnostic {
        public OptionMask {
            new org.xar.ck3.control.wave2.prisoners.ransomquote.RansomOptionMask12004(requestedOptionIndex, observedOptionMaskBits);
        }
    }
    public record UnavailableQuote(String reason, QuoteDiagnostic diagnostic) implements RansomQuote {
        public UnavailableQuote {
            StrictJson.text(reason); Objects.requireNonNull(diagnostic);
            StrictJson.require((diagnostic instanceof OptionCounts) == reason.equals("option_definition_count_unexpected")
                    && (!(diagnostic instanceof OptionMask) || reason.equals("option_mask_unexpected")), "diagnostic branch differs from native reason");
        }
    }

    /** The existing ordinary native quote contract. Available CanSend is true by producer contract. */
    public static RansomQuote decodeQuote(byte[] raw, FrameBinding frame, BigInteger proofEpoch) {
        return readQuote(StrictJson.parse(raw), frame, proofEpoch);
    }
    public static RansomQuote readQuote(JsonNode node, FrameBinding frame, BigInteger proofEpoch) {
        Objects.requireNonNull(frame); ReleasePreviewValues12003.unsigned64(proofEpoch, "quote collection epoch");
        StrictJson.require(node != null && node.isObject(), "ordinary native quote object required");
        StrictJson.trueValue(node.get("private_build")); StrictJson.trueValue(node.get("read_only"));
        StrictJson.require(!bool(node.get("advertised")) && !bool(node.get("action_surface_present")), "private read-only quote required");
        String status = StrictJson.text(node.get("status"));
        if (status.equals("unavailable")) {
            String reason = StrictJson.text(node.get("unavailable_reason"));
            Set<String> fields = new java.util.HashSet<>(UNAVAILABLE_QUOTE_KEYS);
            QuoteDiagnostic diagnostic = new NoQuoteDiagnostic();
            if (reason.equals("option_definition_count_unexpected")) {
                fields.addAll(Set.of("observed_definition_option_count", "observed_context_option_count"));
                int definitionCount = (int) StrictJson.integer(node.get("observed_definition_option_count"), Integer.MIN_VALUE, Integer.MAX_VALUE);
                JsonNode context = node.get("observed_context_option_count");
                StrictJson.require(context != null, "native optional count field required");
                Integer contextCount = context.isNull() ? null : (int) StrictJson.integer(context, Integer.MIN_VALUE, Integer.MAX_VALUE);
                diagnostic = new OptionCounts(definitionCount, contextCount);
            } else if (reason.equals("option_mask_unexpected") && (node.has("requested_option_index") || node.has("observed_option_mask_bits"))) {
                fields.addAll(Set.of("requested_option_index", "observed_option_mask_bits"));
                diagnostic = new OptionMask((int) StrictJson.integer(node.get("requested_option_index"), 0, 3),
                        (int) StrictJson.integer(node.get("observed_option_mask_bits"), 1, RANSOM_OPTION_MASK_MAXIMUM));
            }
            StrictJson.object(node, fields);
            return new UnavailableQuote(reason, diagnostic);
        }
        StrictJson.require(status.equals("available"), "ordinary quote status required");
        StrictJson.object(node, AVAILABLE_QUOTE_KEYS);
        StrictJson.require(node.get("unavailable_reason").isNull(), "available quote reason must be explicit null");
        StrictJson.require(StrictJson.text(node.get("snapshot_id")).equals(frame.snapshotId()), "quote snapshot differs");
        for (String revision : List.of("public_revision", "native_revision")) StrictJson.require(
                StrictJson.integer(node.get(revision), BigInteger.ONE, StrictJson.UINT64_MAX).equals(frame.nativeRevision()), "quote native revision differs");
        StrictJson.require(StrictJson.integer(node.get("proof_epoch"), BigInteger.ONE, StrictJson.UINT64_MAX).equals(proofEpoch), "quote epoch differs");
        StrictJson.integer(node.get("date_raw"), frame.dateRaw(), frame.dateRaw());
        StrictJson.require(StrictJson.text(node.get("definition_key")).equals("ransom_interaction"), "ordinary ransom definition required");
        StrictJson.integer(node.get("jailer_character_id"), frame.playerCharacterId(), frame.playerCharacterId());
        StrictJson.integer(node.get("prisoner_character_id"), frame.prisonerCharacterId(), frame.prisonerCharacterId());
        StrictJson.trueValue(node.get("can_send")); StrictJson.integer(node.get("raw_scale"), 100_000, 100_000);
        String optionKey = StrictJson.text(node.get("selected_option"));
        StrictJson.require(optionKey.equals("gold") || optionKey.equals("current_gold"), "ordinary gold option required");
        AvailableQuote quote = new AvailableQuote(frame, proofEpoch,
                StrictJson.integer(node.get("payer_character_id"), 1, ReleasePreviewValues12003.UINT32_MAX),
                optionKey.equals("gold") ? Option.GOLD : Option.CURRENT_GOLD,
                StrictJson.integer(node.get("quoted_gold_raw"), 1, Long.MAX_VALUE),
                StrictJson.integer(node.get("recipient_acceptance_raw"), Long.MIN_VALUE, Long.MAX_VALUE),
                (int) StrictJson.integer(node.get("recipient_answer_status_raw"), 0, 2));
        StrictJson.require(bool(node.get("would_accept_now")) == quote.wouldAcceptNow()
                && bool(node.get("amount_is_acceptance_time_quote")) == quote.amountIsAcceptanceTimeQuote(), "quote answer or timing differs");
        return quote;
    }
    public static ObjectNode quoteJson(RansomQuote quote) {
        Objects.requireNonNull(quote);
        ObjectNode value = StrictJson.object().put("private_build", true).put("read_only", true)
                .put("advertised", false).put("action_surface_present", false);
        if (quote instanceof UnavailableQuote unavailable) {
            value.put("status", "unavailable").put("unavailable_reason", unavailable.reason());
            if (unavailable.diagnostic() instanceof OptionCounts counts) {
                value.put("observed_definition_option_count", counts.definitionCount());
                if (counts.contextCount() == null) value.putNull("observed_context_option_count");
                else value.put("observed_context_option_count", counts.contextCount());
            } else if (unavailable.diagnostic() instanceof OptionMask mask) {
                value.put("requested_option_index", mask.requestedOptionIndex()).put("observed_option_mask_bits", mask.observedOptionMaskBits());
            }
            return value;
        }
        AvailableQuote available = (AvailableQuote) quote;
        FrameBinding frame = available.frame();
        value.put("status", "available").putNull("unavailable_reason").put("snapshot_id", frame.snapshotId())
                .put("public_revision", frame.nativeRevision()).put("native_revision", frame.nativeRevision())
                .put("proof_epoch", available.proofEpoch()).put("date_raw", frame.dateRaw()).put("definition_key", "ransom_interaction")
                .put("jailer_character_id", frame.playerCharacterId()).put("payer_character_id", available.payerCharacterId())
                .put("prisoner_character_id", frame.prisonerCharacterId()).put("selected_option", available.option() == Option.GOLD ? "gold" : "current_gold")
                .put("can_send", true).put("quoted_gold_raw", available.quotedGoldRaw()).put("raw_scale", 100_000)
                .put("recipient_acceptance_raw", available.recipientAcceptanceRaw()).put("recipient_answer_status_raw", available.answerStatusRaw())
                .put("would_accept_now", available.wouldAcceptNow()).put("amount_is_acceptance_time_quote", available.amountIsAcceptanceTimeQuote());
        return value;
    }

    public record Candidate(int sourceOrdinal, long prisonerCharacterId, Gate ransomGate, RansomQuote ransomQuote,
                            Gate releaseGate, Knowledge closeFamily, Knowledge closeOrExtendedFamily,
                            ReleaseCollectionProjection12003.Row originalProjection) {
        public Candidate {
            StrictJson.require(sourceOrdinal >= 0 && sourceOrdinal <= 63, "candidate ordinal required");
            Objects.requireNonNull(ransomGate); Objects.requireNonNull(ransomQuote); Objects.requireNonNull(releaseGate);
            Objects.requireNonNull(closeFamily); Objects.requireNonNull(closeOrExtendedFamily); Objects.requireNonNull(originalProjection);
            StrictJson.require(originalProjection.sourceOrdinal() == sourceOrdinal
                    && originalProjection.prisonerCharacterId() == prisonerCharacterId, "candidate projection identity differs");
            StrictJson.require(ransomGate == quoteGate(ransomQuote) && releaseGate == previewGate(originalProjection.preview()),
                    "candidate gate differs from its original observation");
            StrictJson.require(closeFamily == Knowledge.UNKNOWN && closeOrExtendedFamily == Knowledge.UNKNOWN,
                    "current-build kinship qualification remains unknown");
        }
    }
    public record Explanation(Source source, String originalCollectionSha256, BigInteger publicPlanningRevision,
                              BigInteger nativeWireRevision, BigInteger proofEpoch, List<Candidate> candidates,
                              List<String> unresolvedInputs) {
        public Explanation {
            Objects.requireNonNull(source); digest(originalCollectionSha256);
            ReleasePreviewValues12003.unsigned64(publicPlanningRevision, "public planning revision");
            ReleasePreviewValues12003.unsigned64(nativeWireRevision, "native wire revision");
            ReleasePreviewValues12003.unsigned64(proofEpoch, "observation epoch");
            candidates = List.copyOf(candidates); unresolvedInputs = List.copyOf(unresolvedInputs);
            StrictJson.require(candidates.size() <= 64, "complete native collection bound required");
            Set<Long> identities = new java.util.HashSet<>();
            for (int ordinal = 0; ordinal < candidates.size(); ordinal++) {
                Candidate candidate = candidates.get(ordinal);
                StrictJson.require(candidate.sourceOrdinal() == ordinal && identities.add(candidate.prisonerCharacterId()),
                        "candidate collection order or identity differs");
                if (candidate.ransomQuote() instanceof AvailableQuote quote) StrictJson.require(
                        quote.frame().nativeRevision().equals(nativeWireRevision) && quote.proofEpoch().equals(proofEpoch),
                        "candidate quote crossed the observation frame");
            }
        }
    }

    /** Complete returned-row superset. Native legality and answer are observations, without new filters or rankings. */
    public static Explanation explain(byte[] originalCollection, ReleaseCollectionProjection12003.SupportedBuild build,
                                      FrameBinding selectedFrame, BigInteger publicPlanningRevision, Catalog catalog) {
        Objects.requireNonNull(catalog);
        StrictJson.require(build == ReleaseCollectionProjection12003.SupportedBuild.CK3_12004, "this research source is bound to current .4");
        var collection = ReleaseCollectionProjection12003.decode(originalCollection, build, selectedFrame);
        JsonNode wireRows = StrictJson.parse(originalCollection, ReleaseCollectionProjection12003.MAX_BYTES)
                .get("player_prisoner_collection").get("prisoners");
        List<Candidate> candidates = new ArrayList<>();
        for (var row : collection.rows()) {
            FrameBinding frame = new FrameBinding(selectedFrame.nativeRevision(), selectedFrame.dateRaw(),
                    selectedFrame.playerCharacterId(), row.prisonerCharacterId());
            RansomQuote quote = readQuote(wireRows.get(row.sourceOrdinal()).get("ransom_quote_preview"), frame, collection.proofEpoch());
            Gate ransom = quoteGate(quote);
            StrictJson.require((ransom == Gate.NOT_EVALUATED) != (row.sourceOrdinal() == collection.selectedOrdinal()),
                    "ransom evaluated a different selected ordinal");
            Gate release = previewGate(row.preview());
            // The retained typed leaf is .3. Current .4 mapping/producer qualification is outside that leaf's proof.
            // Keep it verbatim in originalProjection; do not promote its booleans to current-build policy inputs.
            candidates.add(new Candidate(row.sourceOrdinal(), row.prisonerCharacterId(), ransom, quote, release,
                    Knowledge.UNKNOWN, Knowledge.UNKNOWN, row));
        }
        return new Explanation(catalog.source(), collection.originalSha256(), publicPlanningRevision, selectedFrame.nativeRevision(),
                collection.proofEpoch(), candidates, List.of("native-ai-scheduler-and-cross-action-arbitration",
                "sender-personality-rival-nemesis-feud-and-prison-duration", "current-build-native-kinship-qualification",
                "complete-current-war-retention-value",
                "post-release-relationship-stress-legitimacy-and-resource-outcomes", "action-and-save-postconditions"));
    }
    public static ObjectNode explanationJson(Explanation explanation) {
        Objects.requireNonNull(explanation);
        ObjectNode out = StrictJson.object().put("schema", "xar.g2.prisoner-vanilla-explanation/v1")
                .put("action_selected", false).put("material_result", false).put("native_ai_score_computed", false)
                .put("current_build_kinship_qualified", false)
                .put("candidate_scope", "complete_returned_collection_without_strategy_filter")
                .put("source_sha256", explanation.source().provenance().sourceRef().sha256()).put("original_collection_sha256", explanation.originalCollectionSha256())
                .put("public_planning_revision", explanation.publicPlanningRevision()).put("native_wire_revision", explanation.nativeWireRevision())
                .put("proof_epoch", explanation.proofEpoch());
        ArrayNode rows = out.putArray("candidates");
        for (Candidate candidate : explanation.candidates()) {
            ObjectNode row = rows.addObject().put("source_ordinal", candidate.sourceOrdinal()).put("prisoner_character_id", candidate.prisonerCharacterId())
                    .put("ransom_gate", candidate.ransomGate().name()).put("release_gate", candidate.releaseGate().name())
                    .put("close_family", candidate.closeFamily().name()).put("close_or_extended_family", candidate.closeOrExtendedFamily().name())
                    .put("sender_willingness", "UNKNOWN").put("war_retention_value", "UNKNOWN");
            row.set("ransom_quote_preview", quoteJson(candidate.ransomQuote()));
        }
        ArrayNode unknown = out.putArray("unresolved_inputs"); explanation.unresolvedInputs().forEach(unknown::add);
        return out;
    }
    public static ObjectNode catalogJson(Catalog catalog) {
        ObjectNode out = StrictJson.object().put("schema", "xar.g2.prisoner-vanilla-source-tree/v1")
                .put("machine_id", catalog.source().provenance().machineId()).put("observed_at_utc", catalog.source().provenance().observedAtUtc())
                .put("exact_build", catalog.source().provenance().exactBuild()).put("exe_sha256", catalog.source().executableSha256())
                .put("source_path", catalog.source().provenance().sourceRef().path()).put("source_bytes", catalog.source().provenance().sourceRef().bytes())
                .put("source_sha256", catalog.source().provenance().sourceRef().sha256()).put("native_execution_performed", false);
        ArrayNode trees = out.putArray("interactions");
        for (InteractionTree tree : catalog.interactions()) {
            ObjectNode value = trees.addObject().put("interaction_key", tree.interaction().key()).put("start_line", tree.span().startLine())
                    .put("end_line", tree.span().endLine());
            ArrayNode sections = value.putArray("sections");
            for (SourceSection section : tree.sections()) {
                ObjectNode sectionJson = sections.addObject().put("key", section.key()).put("occurrence", section.occurrence())
                        .put("start_line", section.span().startLine()).put("end_line", section.span().endLine()).put("source_sha256", section.sha256());
                // Full on_accept effects are source-referenced; none is evaluated as an actual outcome here.
                if (!section.key().equals("on_accept")) sectionJson.set("expression", nodeJson(section.expression()));
            }
        }
        ArrayNode edges = out.putArray("edges");
        for (Edge edge : catalog.edges()) {
            ObjectNode value = edges.addObject().put("from", edge.from()).put("to", edge.to()).put("status", edge.state().name())
                    .put("source_key", edge.sourceKey());
            if (edge.unresolvedQuestion() == null) value.putNull("open_question"); else value.put("open_question", edge.unresolvedQuestion());
        }
        return out;
    }
    private static ObjectNode nodeJson(Node node) {
        ObjectNode out = StrictJson.object().put("start_line", node.span().startLine()).put("end_line", node.span().endLine());
        if (node instanceof Atom atom) return out.put("kind", "atom").put("text", atom.text()).put("quoted", atom.quoted());
        if (node instanceof Assignment assignment) {
            out.put("kind", "assignment").put("key", assignment.key()).put("operator", assignment.operator().token());
            out.set("value", nodeJson(assignment.value())); return out;
        }
        out.put("kind", "group"); ArrayNode children = out.putArray("children");
        for (Node child : ((Group) node).children()) children.add(nodeJson(child));
        return out;
    }
    public static String catalogMarkdown(Catalog catalog) {
        Objects.requireNonNull(catalog);
        StringBuilder out = new StringBuilder("# Prisoner vanilla source tree\n\n")
                .append("machine_id: ").append(catalog.source().provenance().machineId()).append("; observed_at_utc: ")
                .append(catalog.source().provenance().observedAtUtc()).append("\n\n")
                .append("Exact source SHA-256 `").append(catalog.source().provenance().sourceRef().sha256())
                .append("`; build ").append(catalog.source().provenance().exactBuild()).append(". No native AI or Game executed.\n\n")
                .append("Solid edges describe authored source sections. Dashed edges remain native caller questions.\n\n```mermaid\nflowchart TD\n");
        for (int index = 0; index < catalog.edges().size(); index++) {
            Edge edge = catalog.edges().get(index);
            String from = edge.from().replace('-', '_'), to = edge.to().replace('-', '_');
            out.append("  ").append(from).append(edge.state() == EdgeState.UNKNOWN ? " -. \"" : " -->|\"")
                    .append(edge.sourceKey()).append(edge.state() == EdgeState.UNKNOWN ? "\" .-> " : "\"| ").append(to).append('\n');
        }
        out.append("```\n\n| Interaction | Section | Occurrence | Source lines | Fragment SHA-256 |\n| --- | --- | ---: | --- | --- |\n");
        for (InteractionTree tree : catalog.interactions()) for (SourceSection section : tree.sections()) {
            out.append("| ").append(tree.interaction().key()).append(" | ").append(section.key()).append(" | ").append(section.occurrence())
                    .append(" | ").append(section.span().startLine()).append('-').append(section.span().endLine()).append(" | ")
                    .append(section.sha256()).append(" |\n");
        }
        out.append("\nOpen native questions:\n\n");
        for (Edge edge : catalog.edges()) if (edge.state() == EdgeState.UNKNOWN) out.append("- ").append(edge.unresolvedQuestion()).append('\n');
        return out.toString();
    }
    public static List<Assignment> assignments(Node root, String key) {
        List<Assignment> found = new ArrayList<>(); collect(root, key, found); return List.copyOf(found);
    }
    private static void collect(Node node, String key, List<Assignment> found) {
        if (node instanceof Assignment assignment) {
            if (assignment.key().equals(key)) found.add(assignment);
            collect(assignment.value(), key, found);
        } else if (node instanceof Group group) for (Node child : group.children()) collect(child, key, found);
    }
    private static Gate quoteGate(RansomQuote quote) {
        return quote instanceof AvailableQuote available ? (available.wouldAcceptNow() ? Gate.ACCEPTED_READ_ONLY : Gate.REFUSED)
                : ((UnavailableQuote) quote).reason().equals("not_evaluated") ? Gate.NOT_EVALUATED : Gate.UNAVAILABLE;
    }
    private static Gate previewGate(ReleasePreview12003 preview) {
        return preview instanceof ReleasePreview12003.Available available ? (available.canSend() ? Gate.ACCEPTED_READ_ONLY : Gate.REFUSED)
                : ((ReleasePreview12003.Unavailable) preview).reason().equals("not_evaluated") ? Gate.NOT_EVALUATED : Gate.UNAVAILABLE;
    }
    private static boolean bool(JsonNode node) { StrictJson.require(node != null && node.isBoolean(), "actual JSON boolean required"); return node.booleanValue(); }
    private static void digest(String value) { StrictJson.require(value != null && value.matches("[0-9a-f]{64}"), "canonical SHA-256 required"); }
    public static String sha256(byte[] raw) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); }
        catch (NoSuchAlgorithmException failure) { throw new IllegalStateException(failure); }
    }
    private static String utf8(byte[] raw) {
        try { return StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(raw)).toString(); }
        catch (CharacterCodingException failure) { throw new IllegalArgumentException("actual UTF-8 source required", failure); }
    }
    /** Small lexical parser, not a Clausewitz evaluator. Never invents predicate or modifier results. */
    private static final class Parser {
        private final String text;
        private int offset;
        private int line = 1;
        private int nodes;
        Parser(String text) { this.text = text; }
        Group parse() {
            List<Node> children = new ArrayList<>(); skip();
            while (offset < text.length()) { children.add(node(0)); skip(); }
            return new Group(children, new Span(0, text.length(), 1, line));
        }
        private Node node(int depth) {
            StrictJson.require(depth <= 128 && ++nodes <= 100_000, "bounded stock syntax required");
            skip(); int start = offset, startLine = line;
            if (peek('{')) {
                take(); List<Node> children = new ArrayList<>(); skip();
                while (!peek('}')) {
                    StrictJson.require(offset < text.length(), "unterminated script group"); children.add(node(depth + 1)); skip();
                }
                take(); return new Group(children, new Span(start, offset, startLine, line));
            }
            StrictJson.require(!peek('}'), "unexpected script group end");
            Atom key = atom(); skip();
            if (offset < text.length() && "=?!<>".indexOf(text.charAt(offset)) >= 0) {
                int operatorStart = offset; take(); if (peek('=')) take();
                Operator operator = Operator.parse(text.substring(operatorStart, offset));
                Node value = node(depth + 1);
                return new Assignment(key.text(), operator, value, new Span(start, offset, startLine, line));
            }
            return key;
        }
        private Atom atom() {
            int start = offset, startLine = line; boolean quoted = peek('"');
            if (quoted) {
                take(); boolean escaped = false;
                while (offset < text.length()) {
                    char current = take();
                    if (!escaped && current == '"') return new Atom(text.substring(start + 1, offset - 1), true, new Span(start, offset, startLine, line));
                    if (!escaped && current == '\\') escaped = true; else escaped = false;
                }
                throw new IllegalArgumentException("unterminated script string");
            }
            while (offset < text.length()) {
                char current = text.charAt(offset);
                if (Character.isWhitespace(current) || "{}#=?!<>".indexOf(current) >= 0) break;
                take();
            }
            StrictJson.require(offset > start, "script token required");
            return new Atom(text.substring(start, offset), false, new Span(start, offset, startLine, line));
        }
        private void skip() {
            while (offset < text.length()) {
                char current = text.charAt(offset);
                if (Character.isWhitespace(current) || current == '\ufeff') { take(); continue; }
                if (current == '#') { while (offset < text.length() && !peek('\n')) take(); continue; }
                return;
            }
        }
        private boolean peek(char value) { return offset < text.length() && text.charAt(offset) == value; }
        private char take() { char value = text.charAt(offset++); if (value == '\n') line++; return value; }
    }
}
