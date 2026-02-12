import SwiftUI
import UIKit

final class AppDelegate: NSObject, UIApplicationDelegate {
    weak var sessionStore: SessionStore?

    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        let token = deviceToken.map { String(format: "%02x", $0) }.joined()
        Task { await sessionStore?.registerDeviceToken(token) }
    }

    func application(_ application: UIApplication, didFailToRegisterForRemoteNotificationsWithError error: Error) {
        // Ignore registration failures for now.
    }
}

@main
struct MentosApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate
    @StateObject private var session: SessionStore

    init() {
        let store = SessionStore()
        _session = StateObject(wrappedValue: store)
        appDelegate.sessionStore = store
    }

    var body: some Scene {
        WindowGroup {
            OnboardingCoordinator()
                .environmentObject(session)
                .onOpenURL { url in session.handleDeepLink(url) }
        }
    }
}
