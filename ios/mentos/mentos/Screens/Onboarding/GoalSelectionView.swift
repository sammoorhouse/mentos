import SwiftUI

struct GoalSelectionView: View {
    let goals = ["Spend less", "Save weekly", "Reduce impulse buys", "Debt payoff", "Emergency fund", "Track subscriptions", "Meal budget", "No-spend days"]
    @State private var selected: Set<String> = []
    var onSubmit: ([String]) -> Void

    var body: some View {
        OnboardingShell(
            title: "Pick your goals",
            subtitle: "Pick a few. You can change later.",
            buttonTitle: "Continue",
            isButtonEnabled: !selected.isEmpty,
            action: { onSubmit(Array(selected)) }
        ) {
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 130), spacing: DSSpacing.s)], spacing: DSSpacing.s) {
                ForEach(goals, id: \.self) { goal in
                    DSChip(title: goal, selected: selected.contains(goal)) {
                        if selected.contains(goal) { selected.remove(goal) } else { selected.insert(goal) }
                    }
                }
            }
        }
    }
}
