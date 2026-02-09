import SwiftUI

struct RootView: View {
    @State private var isSignedIn = false
    @State private var onboardingStep: OnboardingStep = .welcome

    var body: some View {
        Group {
            if !isSignedIn {
                SignInView { result in
                    if case .success = result {
                        isSignedIn = true
                    }
                }
            } else if onboardingStep != .done {
                onboardingFlow
                    .transition(.opacity.combined(with: .move(edge: .trailing)))
            } else {
                MainTabView()
            }
        }
        .tint(.accentColor)
        .animation(DS.Animation.spring, value: isSignedIn)
        .animation(DS.Animation.spring, value: onboardingStep)
    }

    @ViewBuilder
    private var onboardingFlow: some View {
        switch onboardingStep {
        case .welcome:
            WelcomeView { onboardingStep = .connect }
        case .connect:
            ConnectMonzoView(onConnect: { onboardingStep = .goals }, onSkip: { onboardingStep = .goals })
        case .goals:
            GoalSelectionView { _ in onboardingStep = .done }
        case .done:
            EmptyView()
        }
    }
}

enum OnboardingStep {
    case welcome
    case connect
    case goals
    case done
}
