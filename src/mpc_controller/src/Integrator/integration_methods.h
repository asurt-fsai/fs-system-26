#pragma once

#include <Eigen/Dense>
#include <functional>

/**
 * @file integration_methods.h
 * @brief Numerical Integration Methods for Continuous-Time Dynamics
 * 
 * Provides Euler Forward (EF) and Runge-Kutta 4th Order (RK4) integration.
 * - EF: O(dt²) error, simple and fast
 * - RK4: O(dt⁵) error, more accurate, ~3x computation overhead
 * 
 * DynamicsFn is a template parameter (zero-cost) to avoid std::function
 * heap allocation in the hot MPC loop.
 */

namespace integration {

/**
 * @brief Euler Forward integration step
 * 
 * Formula: x_{k+1} = x_k + f(x_k, u_k) * dt
 */
template <int STATE_DIM, int CONTROL_DIM, typename DynamicsFn>
Eigen::VectorXd eulerForward(
    const Eigen::VectorXd& state,
    const Eigen::VectorXd& control,
    DynamicsFn state_derivative_fn,
    double dt) {
    
    Eigen::VectorXd state_dot = state_derivative_fn(state, control);
    return state + state_dot * dt;
}

/**
 * @brief Runge-Kutta 4th Order integration step
 * 
 * Formula:
 *     k1 = f(x_k, u_k)
 *     k2 = f(x_k + 0.5*dt*k1, u_k)
 *     k3 = f(x_k + 0.5*dt*k2, u_k)
 *     k4 = f(x_k + dt*k3, u_k)
 *     x_{k+1} = x_k + (dt/6) * (k1 + 2*k2 + 2*k3 + k4)
 */
template <int STATE_DIM, int CONTROL_DIM, typename DynamicsFn>
Eigen::VectorXd rungeKutta4(
    const Eigen::VectorXd& state,
    const Eigen::VectorXd& control,
    DynamicsFn state_derivative_fn,
    double dt) {
    
    Eigen::VectorXd k1 = state_derivative_fn(state, control);
    Eigen::VectorXd k2 = state_derivative_fn(state + 0.5 * dt * k1, control);
    Eigen::VectorXd k3 = state_derivative_fn(state + 0.5 * dt * k2, control);
    Eigen::VectorXd k4 = state_derivative_fn(state + dt * k3, control);
    
    return state + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4);
}

/**
 * @brief Predict trajectory over multiple steps
 * 
 * @param initial_state Starting state
 * @param controls Sequence of controls, shape (num_steps, CONTROL_DIM)
 * @param state_derivative_fn Dynamics function f(x, u)
 * @param dt Time step (seconds)
 * @param use_rk4 Use RK4 if true, Euler Forward if false (default: true)
 * @return Trajectory matrix, shape (num_steps+1, STATE_DIM)
 */
Eigen::MatrixXd predictTrajectory(
    const Eigen::VectorXd& initial_state,
    const Eigen::MatrixXd& controls,
    std::function<Eigen::VectorXd(const Eigen::VectorXd&, const Eigen::VectorXd&)> state_derivative_fn,
    double dt,
    bool use_rk4 = true);

} // namespace integration
