#include "constraints.h"
#include <cmath>

ConstraintSet::ConstraintSet(const MPCConfig& config) : config_(config) {}

/**
 * @brief Simplified Magic Formula tire model
 * 
 * Calculates tire lateral force coefficient based on slip angle
 * F_y = D * sin(C * arctan(B * alpha - E * (B * alpha - arctan(B * alpha))))
 * 
 * Where:
 * - alpha: slip angle (radians)
 * - B: stiffness factor
 * - C: shape factor  
 * - D: peak friction coefficient
 * - E: curvature factor
 */
static double magicFormulaLateralCoeff(double slip_angle) {
    const double B = 10.0;  // Stiffness
    const double C = 1.3;   // Shape factor
    const double D = 1.0;   // Peak friction (1.0 = normalized)
    const double E = 0.97;  // Curvature
    
    double alpha = slip_angle;
    double numerator = B * alpha - E * (B * alpha - std::atan(B * alpha));
    double Fy = D * std::sin(C * std::atan(numerator));
    
    return std::abs(Fy);  // Return coefficient (0 to 1.0)
}

/**
 * @brief Calculate maximum velocity based on traction limit and curve radius
 * 
 * Uses combined traction circle:
 * (a_lateral / a_max)² + (a_long / a_max)² <= 1
 * 
 * Where a_max is limited by tire friction and vehicle mass
 */
static double calculateVmaxFromTraction(double delta, double wheelbase, 
                                       double mu_max, double /*mass*/) {
    // Calculate slip angle (simplified - assuming small angles, slip ≈ delta)
    double slip_angle = delta;
    
    // Get tire lateral force coefficient from Magic Formula
    double tire_coeff_lateral = magicFormulaLateralCoeff(slip_angle);
    
    // Maximum lateral acceleration available from tires
    const double g = 9.81;  // Gravity
    double a_max_lateral = mu_max * g * tire_coeff_lateral;
    
    // Calculate turning radius
    double tan_delta = std::tan(delta);
    double radius = (std::abs(tan_delta) > 1e-6) 
                   ? wheelbase / std::abs(tan_delta)
                   : 1e9;
    
    // From circular motion: a_lat = v² / R
    // Therefore: v_max = sqrt(a_lat_available * R)
    double v_max = std::sqrt(a_max_lateral * radius);
    
    return v_max;
}

std::pair<Eigen::MatrixXd, Eigen::MatrixXd> ConstraintSet::getInputBounds() const {
    int horizon = config_.horizon;
    
    Eigen::MatrixXd lower = Eigen::MatrixXd::Zero(horizon, 2);
    Eigen::MatrixXd upper = Eigen::MatrixXd::Zero(horizon, 2);
    
    // Static bounds (same for all steps)
    for (int i = 0; i < horizon; ++i) {
        lower(i, 0) = config_.v_min;        // Velocity min
        upper(i, 0) = config_.v_max;        // Velocity max
        
        lower(i, 1) = -config_.delta_dot_max;
        upper(i, 1) = config_.delta_dot_max;
    }
    
    return {lower, upper};
}

std::pair<Eigen::MatrixXd, Eigen::MatrixXd> ConstraintSet::getDynamicInputBounds(
    const Eigen::MatrixXd& trajectory) const {
    int horizon = config_.horizon;
    
    Eigen::MatrixXd lower = Eigen::MatrixXd::Zero(horizon, 2);
    Eigen::MatrixXd upper = Eigen::MatrixXd::Zero(horizon, 2);
    
    // Tire parameters for Magic Formula
    const double mu_max = 1.0;      // Maximum friction coefficient (~1.0 for dry asphalt)
    const double vehicle_mass = 200.0;  // Vehicle mass in kg (tune for your car)
    
    // Dynamic bounds based on tire model and curve radius
    for (int i = 0; i < horizon; ++i) {
        double delta = trajectory(i, 3);  // Steering angle from column 3
        
        // Calculate max velocity based on Magic Formula tire model and traction limit
        double v_max_traction = calculateVmaxFromTraction(delta, config_.wheelbase, 
                                                         mu_max, vehicle_mass);
        
        // Also consider simple saturation at config max
        double effective_v_max = std::min(v_max_traction, config_.v_max);
        
        // Ensure minimum velocity
        effective_v_max = std::max(effective_v_max, config_.v_min);
        
        lower(i, 0) = config_.v_min;
        upper(i, 0) = effective_v_max;  // Speed limited by tire traction
        
        lower(i, 1) = -config_.delta_dot_max;
        upper(i, 1) = config_.delta_dot_max;
    }
    
    return {lower, upper};
}

std::pair<Eigen::MatrixXd, Eigen::MatrixXd> ConstraintSet::getStateBounds() const {
    int horizon = config_.getPredictionSize();
    
    Eigen::MatrixXd lower = Eigen::MatrixXd::Constant(horizon, 4, -1e9);
    Eigen::MatrixXd upper = Eigen::MatrixXd::Constant(horizon, 4, 1e9);
    
    // Steering angle constraint: -delta_max <= delta <= delta_max
    lower.col(3).setConstant(-config_.delta_max);
    upper.col(3).setConstant(config_.delta_max);
    
    return {lower, upper};
}

bool ConstraintSet::checkFeasibility(const Eigen::Vector4d& state,
                                     const Eigen::Vector2d& control) const {
    // Steering angle constraint
    if (state(3) < -config_.delta_max || state(3) > config_.delta_max) {
        return false;
    }
    
    // Velocity constraint
    if (control(0) < config_.v_min || control(0) > config_.v_max) {
        return false;
    }
    
    // Steering rate constraint
    if (control(1) < -config_.delta_dot_max || control(1) > config_.delta_dot_max) {
        return false;
    }
    
    return true;
}
