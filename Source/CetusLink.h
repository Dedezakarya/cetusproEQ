#pragma once
#include <array>
#include <atomic>
#include <cstdint>

// In-process detector links (not audio streaming). One sending instance per bus.
// The transmitter publishes a monotonically increasing block counter; receivers
// use only a fresh value. No locks/heap allocations on the audio thread.
namespace CetusLink {
struct Slot {
    std::atomic<float> level { 0.0f };
    std::atomic<uint64_t> updates { 0 };
};
inline std::array<Slot, 4>& buses() noexcept {
    static std::array<Slot, 4> slots;
    return slots;
}
inline void send(int bus, float level) noexcept {
    if (bus < 1 || bus > 4) return;
    auto& s = buses()[static_cast<size_t>(bus - 1)];
    s.level.store(level, std::memory_order_relaxed);
    s.updates.fetch_add(1, std::memory_order_release);
}
inline float read(int bus, uint64_t& lastUpdate, bool& fresh) noexcept {
    fresh = false;
    if (bus < 1 || bus > 4) return 0.0f;
    auto& s = buses()[static_cast<size_t>(bus - 1)];
    auto count = s.updates.load(std::memory_order_acquire);
    fresh = count != lastUpdate;
    lastUpdate = count;
    return fresh ? s.level.load(std::memory_order_relaxed) : 0.0f;
}
}
