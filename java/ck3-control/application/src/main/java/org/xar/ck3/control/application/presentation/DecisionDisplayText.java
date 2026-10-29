package org.xar.ck3.control.application.presentation;

import java.util.List;
import org.xar.ck3.control.application.presentation.DecisionDisplay.Card;
import org.xar.ck3.control.application.presentation.DecisionDisplay.Snapshot;
import org.xar.ck3.control.application.presentation.DecisionDisplay.Status;

/** Audience prose only; exact Game/episode/parent/attempt identities remain in the typed snapshot. */
public final class DecisionDisplayText {
    public static final String TITLE = "智能体实时决策";
    private DecisionDisplayText() { }

    public static String render(Snapshot actual) {
        StringBuilder text = new StringBuilder(TITLE).append("\n\n");
        if (actual.current().isEmpty()) return text.append("状态：等待当前游戏决策。\n").toString();
        Card current = actual.current().orElseThrow();
        text.append("状态：").append(status(current.status())).append("\n\n")
                .append("决策：").append(action(current)).append("\n\n")
                .append("理由：").append(audienceReason(current.rationale())).append("\n\n")
                .append("结果：").append(result(current.status())).append("\n");
        if (!current.parents().isEmpty()) text.append("\n本条是当前复合决策的子步骤。\n");
        List<Card> history = actual.history();
        if (!history.isEmpty()) {
            text.append("\n近期记录\n");
            int index = 1;
            for (Card row : history) text.append(index++).append(". ").append(action(row)).append("：")
                    .append(status(row.status())).append("\n");
        }
        actual.diagnostic().ifPresent(ignored -> text.append("\n展示更新暂不可用；游戏结果仍以原始回执为准。\n"));
        return text.toString();
    }
    public static String action(Card card) {
        if (card.action().isEmpty()) return card.status() == Status.PLANNING_STOPPED ? "保留当前局势，等待处理" : "观察当前局势";
        String step = card.action().orElseThrow().operation().value();
        if (step.startsWith("advance-route-contact-window-") || step.startsWith("advance-route-contact-horizon-")) return "按接敌窗口推进，随后复查军情";
        if (step.startsWith("life-advance") || step.startsWith("exact-one-day") || step.contains("battle-decision-epoch")) return "推进时间，观察局势变化";
        if (step.startsWith("declare-war-")) return "向选定目标宣战";
        if (step.startsWith("surrender-war-") || step.startsWith("offer-white-peace-") || step.startsWith("enforce-demands-")) return "处理当前战争的结束条件";
        if (step.startsWith("move-army-") || step.startsWith("halt-army-") || step.contains("retreat")) return "调整军队行动";
        if (step.startsWith("raise-troops") || step.startsWith("raise-army")) return "集结军队";
        if (step.contains("mercenary")) return step.startsWith("query-") ? "核对当前雇佣兵与军费条件" : "处理雇佣兵事务";
        if (step.contains("select-event-option") || step.startsWith("resolve-mandatory") || step.startsWith("choose-")) return "处理当前事件选择";
        if (step.startsWith("save-checkpoint") || step.startsWith("save-")) return "保存本次进度";
        if (step.contains("restore-checkpoint")) return "恢复原有存档与决策状态";
        if (step.contains("successor") || step.contains("death-modal") || step.contains("death-terminal")) return "处理统治者继承";
        if (step.contains("sway")) return step.contains("query") ? "核对拉拢计谋结果" : "处理拉拢计谋";
        if (step.contains("construction") || step.contains("building")) return "检查或安排领地建设";
        if (step.contains("marriage") || step.contains("betrothal")) return "处理婚配与家族延续";
        if (step.contains("guardian") || step.contains("education") || step.contains("focus") || step.contains("lifestyle")) return "处理教育与生活方式";
        if (step.contains("crown") || step.contains("realm-law") || step.contains("council")) return "处理领地政务";
        if (step.contains("faith") || step.contains("religion") || step.contains("pilgrimage") || step.contains("holy")) return "处理宗教事务";
        if (step.startsWith("camera-") || step.startsWith("center-map")) return "调整观察镜头";
        if (step.startsWith("query-") || step.startsWith("preview-") || step.startsWith("verify-")) return "核对当前局势与合法条件";
        if (step.equals("pause-map") || step.startsWith("set-speed-") || step.equals("resume-map")) return "调整当前时间推进状态";
        return "处理当前游戏事务";
    }
    private static String audienceReason(String original) {
        if (original.isBlank()) return "本条未提供规划理由。";
        if (original.contains("罗贝尔的30年")) return "本条原理由包含影片标题，未用于实时展示。";
        return original.replace('\r', '\n').replace("\u0000", "");
    }
    public static String status(Status value) {
        return switch (value) {
            case PLANNED -> "计划已形成";
            case WAITING -> "等待当前状态变化";
            case PLANNING_STOPPED -> "当前规划已停止";
            case PREPARING -> "准备执行";
            case RECONCILING -> "核对原有尝试";
            case ACK_RECEIVED -> "原生回执已返回";
            case UNRESOLVED -> "原操作结果仍待确认";
            case SEND_CONFIRMED -> "已确认发出请求";
            case CONFIRMED -> "独立后验已确认";
            case REJECTED_BEFORE_DISPATCH -> "已确认提交前拒绝";
            case REJECTED -> "已确认请求被拒绝";
            case TERMINAL_WITHOUT_EFFECT -> "步骤已完成";
            case CALL_UNAVAILABLE -> "本次调用结果暂不可用";
        };
    }
    public static String result(Status value) {
        return switch (value) {
            case PLANNED -> "尚未提交。";
            case WAITING, PLANNING_STOPPED -> "没有因这条显示提交新动作。";
            case PREPARING -> "即将进入原动作通道；尚未确认提交。";
            case RECONCILING -> "只核对原始尝试，不重复提交。";
            case ACK_RECEIVED -> "已收到原生回执；独立后验仍待核对，不能据此推断业务完成。";
            case UNRESOLVED -> "保留原始请求及回执，不能重复提交或推断已生效。";
            case SEND_CONFIRMED -> "只确认请求已发出；关系、付款和最终结果仍需后验。";
            case CONFIRMED -> "原动作权威已通过独立后验确认该步骤结果。";
            case REJECTED_BEFORE_DISPATCH -> "原始回执确认本次没有提交。";
            case REJECTED -> "原始回执确认拒绝，不推断业务成功。";
            case TERMINAL_WITHOUT_EFFECT -> "原步骤已到终态；本条显示不增加游戏日或保存信用。";
            case CALL_UNAVAILABLE -> "本次调用未返回完整结果；是否提交及实际后态以原账本为准。";
        };
    }
}

