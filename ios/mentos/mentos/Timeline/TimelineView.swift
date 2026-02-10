import SwiftUI

struct TimelineView: View {
    @StateObject private var store = TimelineStore()
    @State private var showRealign = false
    @State private var goalDraft: [GoalItem] = []
    @State private var showFireworks = false
    @State private var celebratedBreakthroughIDs: Set<String> = []

    var body: some View {
        RailScreen(title: "Mentos", statusText: "Monzo connected • Last sync 2h ago") {
            LazyVStack(alignment: .leading, spacing: Tokens.Spacing.l) {
                ForEach(store.events) { event in
                    TimelineCardFactory.makeCard(
                        for: event,
                        onInsightTap: { store.selectedInsight = $0 },
                        onEditGoals: { payload in
                            goalDraft = payload.goals
                            showRealign = true
                        },
                        onRealignGoals: {
                            goalDraft = goalDraft.isEmpty ? defaultGoals : goalDraft
                            showRealign = true
                        }
                    )
                    .modifier(CardMotionModifier())
                    .onAppear {
                        guard event.type == .breakthrough else { return }
                        celebrateBreakthroughIfNeeded(id: event.id)
                    }
                }
            }
            .padding(.horizontal, Tokens.Spacing.l)
        }
        .overlay {
            FireworksOverlay(isActive: showFireworks)
                .opacity(showFireworks ? 1 : 0)
                .animation(.easeOut(duration: Motion.fast), value: showFireworks)
        }
        .task { await store.load() }
        .refreshable { await store.refresh() }
        .sheet(item: $store.selectedInsight) { insight in
            NavigationStack {
                InsightDetailView(title: insight.title, bodyText: insight.detail)
            }
        }
        .sheet(isPresented: $showRealign) {
            GoalRealignSheet(availableGoals: defaultGoals) { updatedGoals in
                Task { await store.saveGoals(updatedGoals) }
            }
        }
        .navigationTitle("")
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                NavigationLink(destination: SettingsView()) {
                    Image(systemName: "gearshape")
                        .foregroundStyle(Tokens.Color.textPrimary)
                }
            }
        }
    }

    private var defaultGoals: [GoalItem] {
        [
            .init(id: "save", title: "Save more money", icon: "sterlingsign.circle", progressText: "8 / 12", progress: 0.66),
            .init(id: "invest", title: "Invest consistently", icon: "chart.line.uptrend.xyaxis", progressText: "2 / 4", progress: 0.5),
            .init(id: "home", title: "Cook at home", icon: "fork.knife", progressText: "4 / 6", progress: 0.75),
            .init(id: "health", title: "Eat healthier", icon: "apple.logo", progressText: "3 / 7", progress: 0.42)
        ]
    }

    private func celebrateBreakthroughIfNeeded(id: String) {
        if celebratedBreakthroughIDs.isEmpty {
            celebratedBreakthroughIDs = Set(UserDefaults.standard.stringArray(forKey: "celebratedBreakthroughIDs") ?? [])
        }
        guard !celebratedBreakthroughIDs.contains(id) else { return }

        celebratedBreakthroughIDs.insert(id)
        UserDefaults.standard.set(Array(celebratedBreakthroughIDs), forKey: "celebratedBreakthroughIDs")

        showFireworks = true
        Haptics.mediumImpact()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
            Haptics.mediumImpact()
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.2) {
            showFireworks = false
        }
    }
}

private struct CardMotionModifier: ViewModifier {
    @State private var appeared = false

    func body(content: Content) -> some View {
        if #available(iOS 17.0, *) {
            content
                .scrollTransition(.animated(.bouncy(duration: Motion.base)), axis: .vertical) { view, phase in
                    view
                        .opacity(phase.isIdentity ? 1 : 0.82)
                        .scaleEffect(phase.isIdentity ? 1 : 0.98)
                        .offset(y: phase.isIdentity ? 0 : 8)
                }
        } else {
            content
                .opacity(appeared ? 1 : 0)
                .offset(y: appeared ? 0 : 8)
                .animation(Motion.default, value: appeared)
                .onAppear { appeared = true }
        }
    }
}

extension InsightPayload: Identifiable {
    var id: String { title + body }
}
