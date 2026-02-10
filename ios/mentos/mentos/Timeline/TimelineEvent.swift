import Foundation

enum TimelineEventType {
    case status
    case weeklyProgress
    case insight
    case goalUpdate
    case breakthrough
    case emptyState
}

struct TimelineEvent: Identifiable {
    enum Payload {
        case status(StatusPayload)
        case weeklyProgress(WeeklyProgressPayload)
        case insight(InsightPayload)
        case goalUpdate(GoalPayload)
        case breakthrough(BreakthroughPayload)
        case emptyState(EmptyStatePayload)
    }

    let id: String
    let date: Date
    let type: TimelineEventType
    let payload: Payload
    let priority: Int
}

struct StatusPayload {
    let isConnected: Bool
    let providerName: String
    let lastSyncText: String
}

struct WeeklyProgressPayload {
    let dayLabels: [String]
    let progress: [Double]
    let summary: String
}

struct InsightPayload {
    let title: String
    let body: String
    let detail: String
}

struct GoalItem: Identifiable, Hashable {
    let id: String
    let title: String
    let icon: String
    let progressText: String
    let progress: Double
}

struct GoalPayload {
    let title: String
    let subtitle: String
    let goals: [GoalItem]
}

struct BreakthroughPayload {
    let title: String
    let metric: String
    let detail: String
    let ctaTitle: String
}

struct EmptyStatePayload {
    let title: String
    let message: String
}
