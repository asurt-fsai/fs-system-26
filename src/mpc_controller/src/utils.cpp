#include "utils.h"

namespace mpc_utils {

double wrapAngle(double angle) {
    while (angle > M_PI) {
        angle -= 2.0 * M_PI;
    }
    while (angle < -M_PI) {
        angle += 2.0 * M_PI;
    }
    return angle;
}

Eigen::Vector4d getReferenceError(const Eigen::Vector4d& state,
                                  const Eigen::Vector4d& reference) {
    Eigen::Vector4d error = state - reference;
    error(2) = wrapAngle(error(2));  // Wrap heading error
    error(3) = wrapAngle(error(3));  // Wrap steering error
    return error;
}

double saturate(double value, double min_val, double max_val) {
    if (value < min_val) return min_val;
    if (value > max_val) return max_val;
    return value;
}

double rateLimit(double current, double desired, double rate_limit, double dt) {
    double max_change = rate_limit * dt;
    double change = std::max(std::min(desired - current, max_change), -max_change);
    return current + change;
}

}  // namespace mpc_utils
