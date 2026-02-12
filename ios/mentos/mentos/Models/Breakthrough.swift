import Foundation

struct Breakthrough: Codable, Identifiable, Hashable {
    let id: String
    let headline: String
    let impact: String
    let suggestion: String
    let triggeredAt: Date?
}
