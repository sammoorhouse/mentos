import Foundation

struct Insight: Codable, Identifiable, Hashable {
    let id: String
    let headline: String
    let message: String
    let severity: String?
    let createdAt: Date?
    let relatedGoalId: String?
}
