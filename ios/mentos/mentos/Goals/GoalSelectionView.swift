import SwiftUI

struct GoalSelectionView: View {
    @EnvironmentObject private var session: SessionStore
    @State private var selections: Set<String> = []
    @State private var isLoading = false
    @State private var errorMessage: String?

    private let options: [GoalOption] = [
        .init(id: "save", title: "Save more money", type: "save"),
        .init(id: "mindful", title: "Spend more mindfully", type: "mindful"),
        .init(id: "health", title: "Eat healthier", type: "health"),
        .init(id: "takeaway", title: "Reduce takeaway", type: "takeaway"),
        .init(id: "emergency", title: "Build an emergency fund", type: "emergency")
    ]

    var body: some View {
        VStack(spacing: 16) {
            Text("Choose your goals")
                .font(.title.bold())
                .padding(.top, 24)

            ScrollView {
                VStack(spacing: 12) {
                    ForEach(options) { option in
                        GoalCard(option: option, isSelected: selections.contains(option.id))
                            .onTapGesture { toggle(option.id) }
                    }
                }
                .padding(.horizontal, 20)
            }

            Button(action: submit) {
                Text(isLoading ? "Saving..." : "Start with these goals")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .padding(.horizontal, 24)
            .padding(.bottom, 24)
            .disabled(isLoading || selections.isEmpty)

            if let errorMessage {
                Text(errorMessage)
                    .font(.footnote)
                    .foregroundColor(.red)
                    .padding(.bottom, 12)
            }
        }
    }

    private func toggle(_ id: String) {
        if selections.contains(id) {
            selections.remove(id)
        } else {
            selections.insert(id)
        }
    }

    private func submit() {
        isLoading = true
        errorMessage = nil
        Task {
            do {
                for option in options where selections.contains(option.id) {
                    _ = try await APIClient.shared.createGoal(name: option.title, type: option.type)
                }
                await session.refreshSession()
                session.onboardingState = .ready
            } catch {
                errorMessage = "Could not save goals."
            }
            isLoading = false
        }
    }
}

struct GoalOption: Identifiable, Hashable {
    let id: String
    let title: String
    let type: String
}

struct GoalCard: View {
    let option: GoalOption
    let isSelected: Bool

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(option.title)
                    .font(.headline)
                Text(isSelected ? "Selected" : "Tap to select")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            Spacer()
            Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")
                .foregroundColor(isSelected ? .accentColor : .secondary)
        }
        .padding()
        .background(RoundedRectangle(cornerRadius: 16).fill(Color(.secondarySystemBackground)))
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(isSelected ? Color.accentColor : Color.clear, lineWidth: 2)
        )
    }
}
