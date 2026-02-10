import SwiftUI

enum TimelineCardFactory {
    @ViewBuilder
    static func makeCard(
        for event: TimelineEvent,
        onInsightTap: @escaping (InsightPayload) -> Void,
        onEditGoals: @escaping (GoalPayload) -> Void,
        onRealignGoals: @escaping () -> Void
    ) -> some View {
        switch event.payload {
        case .status(let payload):
            StatusCard(payload: payload)
        case .weeklyProgress(let payload):
            WeeklyProgressCard(payload: payload)
        case .insight(let payload):
            Button { onInsightTap(payload) } label: { InsightCard(payload: payload) }
                .buttonStyle(.plain)
        case .goalUpdate(let payload):
            GoalCard(payload: payload) { onEditGoals(payload) }
        case .breakthrough(let payload):
            BreakthroughCard(payload: payload, onRealignGoals: onRealignGoals)
        case .emptyState(let payload):
            EmptyStateCard(payload: payload)
        }
    }
}
