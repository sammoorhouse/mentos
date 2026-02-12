import Foundation

struct TimelinePageDTO: Decodable {
    let events: [TimelineEventDTO]
    let nextCursor: String?
}

struct TimelineEventDTO: Decodable {
    let id: String
    let type: String
    let occurredAt: Date
    let title: String
    let body: String
    let meta: [String: JSONValue]
    let actions: [TimelineActionDTO]
    let priority: Int
    let schemaVersion: Int
}

struct TimelineActionDTO: Decodable {
    let id: String
    let label: String
    let kind: String
    let actionType: String
    let payload: [String: JSONValue]
}

enum JSONValue: Decodable {
    case string(String)
    case number(Double)
    case object([String: JSONValue])
    case array([JSONValue])
    case bool(Bool)
    case null

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if container.decodeNil() {
            self = .null
        } else if let value = try? container.decode(Bool.self) {
            self = .bool(value)
        } else if let value = try? container.decode(Double.self) {
            self = .number(value)
        } else if let value = try? container.decode(String.self) {
            self = .string(value)
        } else if let value = try? container.decode([String: JSONValue].self) {
            self = .object(value)
        } else if let value = try? container.decode([JSONValue].self) {
            self = .array(value)
        } else {
            self = .null
        }
    }

    var stringValue: String? {
        if case let .string(value) = self { return value }
        return nil
    }

    var doubleValue: Double? {
        if case let .number(value) = self { return value }
        return nil
    }

    var intValue: Int? {
        if case let .number(value) = self { return Int(value) }
        if case let .string(value) = self { return Int(value) }
        return nil
    }

    var arrayValue: [JSONValue]? {
        if case let .array(value) = self { return value }
        return nil
    }

    var intArrayValue: [Int]? {
        guard let array = arrayValue else { return nil }
        let values = array.compactMap { $0.intValue }
        return values.isEmpty ? nil : values
    }

    var objectValue: [String: JSONValue]? {
        if case let .object(value) = self { return value }
        return nil
    }
}
