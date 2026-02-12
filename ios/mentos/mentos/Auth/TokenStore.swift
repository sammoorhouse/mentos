import Foundation
import Security

struct AuthTokens: Codable, Hashable {
    let accessToken: String
    let refreshToken: String
}

final class TokenStore {
    static let shared = TokenStore()

    private let service: String
    private let accessKey = "accessToken"
    private let refreshKey = "refreshToken"

    init(service: String? = nil) {
        self.service = service ?? (Bundle.main.bundleIdentifier ?? "com.mentos.app")
    }

    func saveTokens(_ tokens: AuthTokens) {
        save(key: accessKey, value: tokens.accessToken)
        save(key: refreshKey, value: tokens.refreshToken)
    }

    func loadTokens() -> AuthTokens? {
        guard let accessToken = load(key: accessKey),
              let refreshToken = load(key: refreshKey) else {
            return nil
        }
        return AuthTokens(accessToken: accessToken, refreshToken: refreshToken)
    }

    func clear() {
        delete(key: accessKey)
        delete(key: refreshKey)
    }

    private func save(key: String, value: String) {
        let data = Data(value.utf8)
        let query: [CFString: Any] = [
            kSecClass: kSecClassGenericPassword,
            kSecAttrService: service,
            kSecAttrAccount: key
        ]
        SecItemDelete(query as CFDictionary)
        let attributes: [CFString: Any] = [
            kSecClass: kSecClassGenericPassword,
            kSecAttrService: service,
            kSecAttrAccount: key,
            kSecValueData: data
        ]
        SecItemAdd(attributes as CFDictionary, nil)
    }

    private func load(key: String) -> String? {
        let query: [CFString: Any] = [
            kSecClass: kSecClassGenericPassword,
            kSecAttrService: service,
            kSecAttrAccount: key,
            kSecReturnData: true,
            kSecMatchLimit: kSecMatchLimitOne
        ]
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        guard status == errSecSuccess, let data = result as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }

    private func delete(key: String) {
        let query: [CFString: Any] = [
            kSecClass: kSecClassGenericPassword,
            kSecAttrService: service,
            kSecAttrAccount: key
        ]
        SecItemDelete(query as CFDictionary)
    }
}
