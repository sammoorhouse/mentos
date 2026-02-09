import SwiftUI
import UIKit

struct DSChip: View {
    let title: String
    var selected: Bool
    var action: () -> Void

    var body: some View {
        Button {
            UISelectionFeedbackGenerator().selectionChanged()
            action()
        } label: {
            Text(title)
                .font(.dsBody)
                .padding(.vertical, DSSpacing.s)
                .padding(.horizontal, DSSpacing.l)
                .background(background, in: Capsule())
                .overlay(Capsule().stroke(border, lineWidth: 1))
        }
        .buttonStyle(.plain)
    }

    private var background: Color { selected ? .accentColor.opacity(0.18) : DS.Color.surface }
    private var border: Color { selected ? .accentColor.opacity(0.35) : DS.Color.separator.opacity(0.4) }
}
