import Foundation

struct MonzoStatus: Codable, Hashable {
    let connected: Bool
    let status: String?
    let lastSyncAt: Date?
    let health: String?
}
