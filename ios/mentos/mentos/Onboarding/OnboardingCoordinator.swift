import SwiftUI

struct OnboardingCoordinator: View {
    @EnvironmentObject private var session: SessionStore

    var body: some View {
        Group {
            switch session.onboardingState {
            case .signedOut:
                SignInView()
            case .needsOnboarding:
                WelcomeView()
            case .needsMonzo:
                ConnectMonzoView()
            case .needsGoals:
                GoalSelectionView()
            case .ready:
                MainTabView()
            }
        }
        .task {
            await session.initialize()
        }
    }
}
