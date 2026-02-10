import SwiftUI

struct GoalPicker: View {
    let options: [GoalItem]
    @Binding var selection: Set<GoalItem>

    var body: some View {
        VStack(spacing: Tokens.Spacing.s) {
            ForEach(options) { option in
                let isSelected = selection.contains(option)
                Button {
                    if isSelected { selection.remove(option) } else { selection.insert(option) }
                } label: {
                    HStack {
                        Label(option.title, systemImage: option.icon)
                            .font(Typography.body)
                            .foregroundStyle(Tokens.Color.textPrimary)
                        Spacer()
                        if isSelected {
                            Image(systemName: "checkmark")
                                .foregroundStyle(Tokens.Color.accent)
                        }
                    }
                    .padding(Tokens.Spacing.m)
                    .frame(maxWidth: .infinity)
                    .background(isSelected ? Tokens.Color.accent.opacity(0.2) : Tokens.Color.surface2)
                    .overlay {
                        RoundedRectangle(cornerRadius: Tokens.Radius.small, style: .continuous)
                            .stroke(Tokens.Color.separator, lineWidth: 1)
                    }
                    .clipShape(RoundedRectangle(cornerRadius: Tokens.Radius.small, style: .continuous))
                }
                .buttonStyle(.plain)
            }
        }
    }
}
