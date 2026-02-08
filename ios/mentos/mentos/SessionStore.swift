import Foundation
import AuthenticationServices

final class SessionStore: ObservableObject {
    @Published var accessToken: String?
    @Published var selectedInsightId: String?

    func handleDeepLink(_ url: URL) {
        if url.host == "insights" { selectedInsightId = url.lastPathComponent }
    }
}
