import Foundation

struct Goal: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let type: String
    let tags: String?
    let active: Int?
}
