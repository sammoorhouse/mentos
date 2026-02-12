import Foundation

final class APIClient {
    static let shared = APIClient()

    enum APIClientError: Error {
        case invalidBaseURL
        case invalidResponse
        case unauthorized
        case missingTokens
    }

    private let baseURL: URL
    private let tokenStore: TokenStore
    private let session: URLSession
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder

    init(tokenStore: TokenStore = .shared, session: URLSession = .shared) {
        guard let baseString = Bundle.main.infoDictionary?["API_BASE_URL"] as? String,
              let url = URL(string: baseString) else {
            self.baseURL = URL(string: "https://example.invalid")!
            self.tokenStore = tokenStore
            self.session = session
            self.decoder = JSONDecoder()
            self.encoder = JSONEncoder()
            return
        }
        self.baseURL = url
        self.tokenStore = tokenStore
        self.session = session
        self.decoder = JSONDecoder()
        self.encoder = JSONEncoder()
        self.decoder.keyDecodingStrategy = .convertFromSnakeCase
        self.decoder.dateDecodingStrategy = .iso8601
    }

    func signInWithApple(identityToken: String) async throws -> AuthTokens {
        struct Payload: Codable { let identityToken: String }
        return try await request("/auth/apple", method: "POST", body: Payload(identityToken: identityToken), requiresAuth: false)
    }

    func refreshTokens() async throws -> AuthTokens {
        guard let tokens = tokenStore.loadTokens() else { throw APIClientError.missingTokens }
        struct Payload: Codable { let refreshToken: String }
        let refreshed: AuthTokens = try await request("/auth/refresh", method: "POST", body: Payload(refreshToken: tokens.refreshToken), requiresAuth: false)
        tokenStore.saveTokens(refreshed)
        return refreshed
    }

    func getMe() async throws -> User {
        try await request("/me")
    }

    func getGoals() async throws -> [Goal] {
        try await request("/goals")
    }

    func createGoal(name: String, type: String, tags: String = "", active: Bool = true) async throws -> Goal {
        struct Payload: Codable { let name: String; let type: String; let tags: String; let active: Bool }
        return try await request("/goals", method: "POST", body: Payload(name: name, type: type, tags: tags, active: active))
    }

    func getInsights() async throws -> [Insight] {
        try await request("/insights")
    }

    func getBreakthroughs() async throws -> [Breakthrough] {
        try await request("/breakthroughs")
    }

    func getMonzoStatus() async throws -> MonzoStatus {
        try await request("/monzo/status")
    }

    func getTimeline(cursor: String? = nil, limit: Int = 50) async throws -> TimelinePageDTO {
        var query: [String] = ["limit=\(limit)"]
        if let cursor, !cursor.isEmpty {
            query.append("cursor=\(cursor)")
        }
        let path = "/timeline" + (query.isEmpty ? "" : "?\(query.joined(separator: "&"))")
        return try await request(path)
    }

    func startMonzoConnect() async throws -> MonzoConnectStartResponse {
        try await request("/monzo/connect/start")
    }

    func completeMonzoConnect(code: String, stateId: String) async throws {
        struct Payload: Codable { let code: String; let stateId: String }
        let _: EmptyResponse = try await request("/monzo/connect/complete", method: "POST", body: Payload(code: code, stateId: stateId))
    }

    func registerDevice(apnsToken: String) async throws {
        struct Payload: Codable { let apnsToken: String }
        let _: EmptyResponse = try await request("/devices", method: "POST", body: Payload(apnsToken: apnsToken))
    }

    func disconnectMonzo() async throws {
        let _: EmptyResponse = try await request("/monzo/disconnect", method: "POST", body: nil)
    }

    private func request<T: Decodable>(_ path: String,
                                       method: String = "GET",
                                       body: Encodable? = nil,
                                       requiresAuth: Bool = true) async throws -> T {
        try await request(path, method: method, body: body, requiresAuth: requiresAuth, retryOnAuthFailure: true)
    }

    private func request<T: Decodable>(_ path: String,
                                       method: String,
                                       body: Encodable?,
                                       requiresAuth: Bool,
                                       retryOnAuthFailure: Bool) async throws -> T {
        let urlRequest = try makeRequest(path: path, method: method, body: body, requiresAuth: requiresAuth)
        let (data, response) = try await session.data(for: urlRequest)
        guard let http = response as? HTTPURLResponse else { throw APIClientError.invalidResponse }

        if path == "/auth/apple" {
            let bodyText = String(data: data, encoding: .utf8) ?? "<non-utf8>"
            print("[API] /auth/apple status=\(http.statusCode) body=\(bodyText)")
        }

        if http.statusCode == 401, requiresAuth, retryOnAuthFailure {
            _ = try await refreshTokens()
            return try await request(path, method: method, body: body, requiresAuth: requiresAuth, retryOnAuthFailure: false)
        }

        guard (200...299).contains(http.statusCode) else {
            if http.statusCode == 401 { throw APIClientError.unauthorized }
            throw APIClientError.invalidResponse
        }

        if T.self == EmptyResponse.self {
            return EmptyResponse() as! T
        }

        return try decoder.decode(T.self, from: data)
    }

    private func makeRequest(path: String,
                             method: String,
                             body: Encodable?,
                             requiresAuth: Bool) throws -> URLRequest {
        guard let url = URL(string: path, relativeTo: baseURL) else { throw APIClientError.invalidBaseURL }
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if requiresAuth, let token = tokenStore.loadTokens()?.accessToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        if let body = body {
            request.httpBody = try encoder.encode(AnyEncodable(body))
        }

        return request
    }
}

struct MonzoConnectStartResponse: Codable, Hashable {
    let authUrl: String
    let stateId: String
}

struct EmptyResponse: Codable, Hashable {
    init() {}
}

struct AnyEncodable: Encodable {
    private let encodeClosure: (Encoder) throws -> Void

    init(_ encodable: Encodable) {
        self.encodeClosure = encodable.encode
    }

    func encode(to encoder: Encoder) throws {
        try encodeClosure(encoder)
    }
}
