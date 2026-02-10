import SwiftUI

enum Motion {
    static let fast: Double = 0.12
    static let base: Double = 0.18
    static let slow: Double = 0.28
    static let `default` = Animation.spring(response: 0.35, dampingFraction: 0.85)
}
