import Foundation

struct User: Codable, Identifiable {
    let id: String
    let email: String?
    let preferences: UserPreferences?
    let monzo: UserMonzoStatus?
}

struct UserPreferences: Codable, Hashable {
    let tone: String?
    let quietHoursStart: String?
    let quietHoursEnd: String?
    let maxNotificationsPerDay: Int?
}

struct UserMonzoStatus: Codable, Hashable {
    let connected: Bool
    let status: String?
}
