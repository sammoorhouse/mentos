import SwiftUI

struct GoalRealignSheet: View {
    let availableGoals: [GoalItem]
    let onSave: ([GoalItem]) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var selection: Set<GoalItem>

    init(availableGoals: [GoalItem], onSave: @escaping ([GoalItem]) -> Void) {
        self.availableGoals = availableGoals
        self.onSave = onSave
        _selection = State(initialValue: Set(availableGoals))
    }

    var body: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: Tokens.Spacing.l) {
                Text("Pick what matters right now.")
                    .font(Typography.body)
                    .foregroundStyle(Tokens.Color.textSecondary)

                GoalPicker(options: availableGoals, selection: $selection)

                HStack(spacing: Tokens.Spacing.s) {
                    Button("Cancel") { dismiss() }
                        .foregroundStyle(Tokens.Color.textSecondary)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, Tokens.Spacing.m)
                        .background(Tokens.Color.surface2)
                        .clipShape(Capsule())
                    Button("Save") {
                        onSave(Array(selection))
                        dismiss()
                    }
                    .foregroundStyle(Tokens.Color.background)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, Tokens.Spacing.m)
                    .background(Tokens.Color.accent)
                    .clipShape(Capsule())
                }
            }
            .padding(Tokens.Spacing.l)
            .background(Tokens.Color.background.ignoresSafeArea())
            .navigationTitle("Realign goals")
            .navigationBarTitleDisplayMode(.inline)
        }
        .presentationDetents([.medium, .large])
    }
}
