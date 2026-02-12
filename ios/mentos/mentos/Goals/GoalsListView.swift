import SwiftUI

struct GoalsListView: View {
    @State private var goals: [Goal] = []
    @State private var isLoading = false

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 12) {
                    ForEach(goals) { goal in
                        VStack(alignment: .leading, spacing: 6) {
                            Text(goal.name)
                                .font(.headline)
                            Text(goal.type.capitalized)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding()
                        .background(RoundedRectangle(cornerRadius: 16).fill(Color(.secondarySystemBackground)))
                    }

                    if goals.isEmpty {
                        Text("No goals yet")
                            .font(.footnote)
                            .foregroundColor(.secondary)
                            .padding(.top, 12)
                    }
                }
                .padding()
            }
            .navigationTitle("Goals")
            .task { await loadGoals() }
            .refreshable { await loadGoals() }
        }
    }

    private func loadGoals() async {
        guard !isLoading else { return }
        isLoading = true
        do {
            goals = try await APIClient.shared.getGoals()
        } catch {
            goals = []
        }
        isLoading = false
    }
}
