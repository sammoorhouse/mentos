import Foundation
import UserNotifications
import UIKit

@MainActor
final class SessionStore: ObservableObject {
    enum OnboardingState {
        case signedOut
        case needsOnboarding
        case needsMonzo
        case needsGoals
        case ready
    }

    @Published var isAuthenticated = false
    @Published var user: User?
    @Published var onboardingState: OnboardingState = .signedOut
    @Published var monzoStatus: MonzoStatus?
    @Published var selectedInsightId: String?

    private let apiClient: APIClient
    private let tokenStore: TokenStore
    private let hasSeenWelcomeKey = "hasSeenWelcome"

    init(apiClient: APIClient = .shared, tokenStore: TokenStore = .shared) {
        self.apiClient = apiClient
        self.tokenStore = tokenStore
    }

    func initialize() async {
        if tokenStore.loadTokens() != nil {
            isAuthenticated = true
            await refreshSession()
        } else {
            onboardingState = .signedOut
        }
    }

    func handleDeepLink(_ url: URL) {
        if url.host == "insights" {
            selectedInsightId = url.lastPathComponent
            return
        }

        if url.host == "oauth", url.path.contains("monzo") {
            guard let components = URLComponents(url: url, resolvingAgainstBaseURL: false),
                  let code = components.queryItems?.first(where: { $0.name == "code" })?.value,
                  let state = components.queryItems?.first(where: { $0.name == "state" })?.value else {
                return
            }

            Task {
                do {
                    try await apiClient.completeMonzoConnect(code: code, stateId: state)
                    await refreshSession()
                    onboardingState = .needsGoals
                    NotificationCenter.default.post(name: .monzoConnected, object: nil)
                } catch {
                    // Ignore; user can retry from the connect screen.
                }
            }
        }
    }

    func signIn(identityToken: String) async throws {
        let tokens = try await apiClient.signInWithApple(identityToken: identityToken)
        tokenStore.saveTokens(tokens)
        isAuthenticated = true
        await refreshSession()
    }

    func signOut() {
        tokenStore.clear()
        isAuthenticated = false
        user = nil
        monzoStatus = nil
        onboardingState = .signedOut
    }

    func markWelcomeComplete() {
        UserDefaults.standard.set(true, forKey: hasSeenWelcomeKey)
    }

    func refreshSession() async {
        guard isAuthenticated else {
            onboardingState = .signedOut
            return
        }

        do {
            let me = try await apiClient.getMe()
            user = me
        } catch {
            signOut()
            return
        }

        if !UserDefaults.standard.bool(forKey: hasSeenWelcomeKey) {
            onboardingState = .needsOnboarding
            return
        }

        do {
            let status = try await apiClient.getMonzoStatus()
            monzoStatus = status
            if !status.connected {
                onboardingState = .needsMonzo
                return
            }
        } catch {
            onboardingState = .needsMonzo
            return
        }

        do {
            let goals = try await apiClient.getGoals()
            if goals.isEmpty {
                onboardingState = .needsGoals
            } else {
                onboardingState = .ready
                await requestNotificationAuthorization()
            }
        } catch {
            onboardingState = .needsGoals
        }
    }

    func requestNotificationAuthorization() async {
        let center = UNUserNotificationCenter.current()
        let granted = try? await center.requestAuthorization(options: [.alert, .sound, .badge])
        if granted == true {
            await MainActor.run { UIApplication.shared.registerForRemoteNotifications() }
        }
    }

    func registerDeviceToken(_ token: String) async {
        guard isAuthenticated else { return }
        do {
            try await apiClient.registerDevice(apnsToken: token)
        } catch {
            // Best-effort registration; ignore failures for now.
        }
    }
}

extension Notification.Name {
    static let monzoConnected = Notification.Name("monzoConnected")
}
