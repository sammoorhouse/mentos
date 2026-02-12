import SwiftUI
import AuthenticationServices

struct OnboardingCoordinator: View {
    @EnvironmentObject private var session: SessionStore

    var body: some View {
        Group {
            switch session.onboardingState {
            case .signedOut:
                SignInView(onSignedIn: handleSignIn(result:))
            case .needsOnboarding:
                WelcomeView(onContinue: {
                    session.markWelcomeComplete()
                    session.onboardingState = .needsMonzo
                })
            case .needsMonzo:
                ConnectMonzoView(
                    onConnect: { session.onboardingState = .needsGoals },
                    onSkip: { session.onboardingState = .needsGoals }
                )
            case .needsGoals:
                GoalSelectionView { _ in
                    Task { await session.refreshSession() }
                    session.onboardingState = .ready
                }
            case .ready:
                MainTabView()
            }
        }
        .task {
            await session.initialize()
        }
    }

    private func handleSignIn(result: Result<ASAuthorization, Error>) {
        switch result {
        case .success(let authorization):
            guard let credential = authorization.credential as? ASAuthorizationAppleIDCredential,
                  let tokenData = credential.identityToken,
                  let token = String(data: tokenData, encoding: .utf8) else {
                return
            }
            Task {
                try? await session.signIn(identityToken: token)
            }
        case .failure:
            break
        }
    }
}
