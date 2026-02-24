#include "mpc_controller/mpc_solver.h"
#include "mpc_controller/utils.h"
#include "mpc_controller/constraints.h"
#include <iostream>
#include <algorithm>
#include <casadi/casadi.hpp>

MPCSolver::MPCSolver(const MPCConfig& config)
    : config_(config), model_(config) {
    config_.initializeDefaults();
    last_control_sequence_ = Eigen::MatrixXd::Zero(config_.horizon, 2);
}

MPCSolver::SolveInfo MPCSolver::solve(
    const Eigen::Vector4d& x0,
    const Eigen::MatrixXd& reference_trajectory,
    Eigen::MatrixXd& optimal_controls,
    Eigen::MatrixXd& predicted_trajectory,
    const Eigen::MatrixXd& x0_control) {
    
    using namespace casadi;
    
    SolveInfo info;
    
    // Use warm start or provided initial guess
    Eigen::VectorXd u0;
    if (x0_control.size() == 0) {
        u0 = Eigen::Map<Eigen::VectorXd>(
            last_control_sequence_.data(),
            last_control_sequence_.size()
        );
    } else {
        u0 = Eigen::Map<Eigen::VectorXd>(
            const_cast<Eigen::MatrixXd&>(x0_control).data(),
            x0_control.size()
        );
    }
    
    // Expand x0 to 5D state (add velocity = 0)
    Eigen::VectorXd x0_5d = Eigen::VectorXd::Zero(5);
    x0_5d.head(4) = x0;
    x0_5d(4) = 0.0;  // Initial velocity
    
    try {
        // Decision variables: control sequence (horizon x 2)
        MX u = MX::sym("u", config_.horizon * 2);
        
        // Build cost function
        MX cost = 0.0;
        
        // Create dynamics function for CasADi
        // State: [x, y, theta, delta, v]
        // Control: [a, delta_dot]
        MX state = MX::sym("state", 5);
        MX control = MX::sym("control", 2);
        
        // Bicycle model dynamics
        MX state_dot = MX::zeros(5);
        state_dot(0) = state(4) * cos(state(2));
        state_dot(1) = state(4) * sin(state(2));
        state_dot(2) = (state(4) / config_.wheelbase) * tan(state(3));
        state_dot(3) = control(1);
        state_dot(4) = control(0);
        
        Function dynamics_fn = Function("dynamics", {state, control}, {state_dot});
        
        // Forward simulation with cost accumulation
        // Initialize current state with x0_5d
        DM current_state_val = DM::zeros(5, 1);
        for (int i = 0; i < 5; ++i) {
            current_state_val(i) = x0_5d(i);
        }
        
        // Simulate trajectory and compute cost
        for (int i = 0; i < config_.horizon; ++i) {
            // Extract control
            MX v_control = u(i * 2);
            MX delta_dot_control = u(i * 2 + 1);
            MX control_input = vertcat(v_control, delta_dot_control);
            
            // Create a symbolic state for this step
            MX sym_state = MX(current_state_val);
            
            // RK4 integration step (using symbolic computation)
            std::vector<MX> k_results(4);
            
            k_results[0] = dynamics_fn(std::vector<MX>{sym_state, control_input})[0];
            k_results[1] = dynamics_fn(std::vector<MX>{sym_state + 0.5 * config_.dt * k_results[0], control_input})[0];
            k_results[2] = dynamics_fn(std::vector<MX>{sym_state + 0.5 * config_.dt * k_results[1], control_input})[0];
            k_results[3] = dynamics_fn(std::vector<MX>{sym_state + config_.dt * k_results[2], control_input})[0];
            
            MX next_state = sym_state + (config_.dt / 6.0) * 
                           (k_results[0] + 2*k_results[1] + 2*k_results[2] + k_results[3]);
            
            // Compute state cost (compare with reference)
            std::vector<double> ref_i(4);
            for (int j = 0; j < 4; ++j) {
                ref_i[j] = reference_trajectory(i + 1, j);
            }
            
            MX state_error = vertcat(
                next_state(0) - ref_i[0],
                next_state(1) - ref_i[1],
                next_state(2) - ref_i[2],
                next_state(3) - ref_i[3]
            );
            
            // Wrap angle error
            state_error(2) = state_error(2) - 2*M_PI*floor((state_error(2) + M_PI)/(2*M_PI));
            
            // Stage cost: state error + control effort
            for (int j = 0; j < 4; ++j) {
                for (int k = 0; k < 4; ++k) {
                    cost = cost + state_error(j) * config_.Q(j, k) * state_error(k);
                }
            }
            
            cost = cost + v_control * config_.R(0, 0) * v_control + 
                         delta_dot_control * config_.R(1, 1) * delta_dot_control;
            
            // Update state for next iteration - use next_state in MX form
            current_state_val = DM::zeros(5, 1);  // Reset for next iteration
            sym_state = next_state;  // Carry forward the symbolic state
        }
        
        // Terminal cost using final symbolic state
        std::vector<double> ref_terminal(4);
        for (int j = 0; j < 4; ++j) {
            ref_terminal[j] = reference_trajectory(config_.horizon, j);
        }
        
        MX terminal_error = vertcat(
            current_state_val(0) - ref_terminal[0],
            current_state_val(1) - ref_terminal[1],
            current_state_val(2) - ref_terminal[2],
            current_state_val(3) - ref_terminal[3]
        );
        terminal_error(2) = terminal_error(2) - 2*M_PI*floor((terminal_error(2) + M_PI)/(2*M_PI));
        
        for (int j = 0; j < 4; ++j) {
            for (int k = 0; k < 4; ++k) {
                cost = cost + terminal_error(j) * config_.Q_terminal(j, k) * terminal_error(k);
            }
        }
        
        // Input bounds constraints
        auto bounds = buildBounds();
        std::vector<double> lbx(config_.horizon * 2), ubx(config_.horizon * 2);
        for (size_t i = 0; i < bounds.size(); ++i) {
            lbx[i] = bounds[i].first;
            ubx[i] = bounds[i].second;
        }
        
        // Create NLP
        MXDict nlp = {{"x", u}, {"f", cost}};
        
        // Create solver with IPOPT and options
        Dict opts;
        opts["ipopt.max_iter"] = 100;
        opts["ipopt.print_level"] = 0;
        opts["print_time"] = false;
        
        Function solver = nlpsol("solver", "ipopt", nlp, opts);
        
        // Prepare initial guess
        std::vector<double> u0_vec(config_.horizon * 2);
        for (int i = 0; i < config_.horizon; ++i) {
            u0_vec[i * 2] = u0(i * 2);
            u0_vec[i * 2 + 1] = u0(i * 2 + 1);
        }
        
        // Solve
        DMDict arg;
        arg["x0"] = u0_vec;
        arg["lbx"] = lbx;
        arg["ubx"] = ubx;
        
        DMDict res = solver(arg);
        
        // Extract solution - convert DM to vector
        DM u_opt_dm = res.at("x");
        std::vector<double> u_opt;
        for (int i = 0; i < u_opt_dm.size1(); ++i) {
            u_opt.push_back(static_cast<double>(u_opt_dm(i)));
        }
        
        optimal_controls = Eigen::MatrixXd::Zero(config_.horizon, 2);
        for (int i = 0; i < config_.horizon; ++i) {
            optimal_controls(i, 0) = u_opt[i * 2];
            optimal_controls(i, 1) = u_opt[i * 2 + 1];
        }
        
        predicted_trajectory = model_.predictTrajectory(x0_5d, optimal_controls);
        
        // Convert 5D trajectory to 4D for output (drop velocity)
        Eigen::MatrixXd traj_4d = predicted_trajectory.leftCols(4);
        predicted_trajectory = traj_4d;
        
        // Store for warm-starting next solve
        last_control_sequence_ = optimal_controls;
        last_trajectory_ = predicted_trajectory;
        
        double final_cost = computeCost(predicted_trajectory, optimal_controls, reference_trajectory);
        
        info.success = true;
        info.cost = final_cost;
        info.iterations = 0;
        info.message = "Solved with CasADi IPOPT";
        
    } catch (const std::exception& e) {
        std::cerr << "CasADi solver error: " << e.what() << std::endl;
        
        // Fallback to warm start if optimization fails
        optimal_controls = last_control_sequence_;
        Eigen::VectorXd x0_5d_fallback = Eigen::VectorXd::Zero(5);
        x0_5d_fallback.head(4) = x0;
        predicted_trajectory = model_.predictTrajectory(x0_5d_fallback, optimal_controls);
        predicted_trajectory = predicted_trajectory.leftCols(4);
        
        info.success = false;
        info.cost = computeCost(predicted_trajectory, optimal_controls, reference_trajectory);
        info.message = "Fallback: CasADi failed, using warm start";
    }
    
    last_solve_info_ = info;
    return info;
}

Eigen::Vector2d MPCSolver::getControl(
    const Eigen::Vector4d& x0,
    const Eigen::MatrixXd& reference_trajectory) {
    
    Eigen::MatrixXd controls;
    Eigen::MatrixXd trajectory;
    solve(x0, reference_trajectory, controls, trajectory);
    
    return controls.row(0).transpose();
}

double MPCSolver::computeCost(
    const Eigen::MatrixXd& trajectory,
    const Eigen::MatrixXd& controls,
    const Eigen::MatrixXd& reference_trajectory) const {
    
    double cost = 0.0;
    int N = controls.rows();
    
    // Stage costs
    for (int i = 0; i < N; ++i) {
        Eigen::Vector4d error = trajectory.row(i).transpose() -
                                reference_trajectory.row(i).transpose();
        error(2) = mpc_utils::wrapAngle(error(2));
        
        double state_cost = error.transpose() * config_.Q * error;
        double control_cost = controls.row(i) * config_.R * controls.row(i).transpose();
        
        cost += state_cost + control_cost;
    }
    
    // Terminal cost
    Eigen::Vector4d terminal_error = trajectory.row(N).transpose() -
                                     reference_trajectory.row(N).transpose();
    terminal_error(2) = mpc_utils::wrapAngle(terminal_error(2));
    double terminal_cost = terminal_error.transpose() * config_.Q_terminal * terminal_error;
    cost += terminal_cost;
    
    return cost;
}

std::vector<std::pair<double, double>> MPCSolver::buildBounds() const {
    auto bounds_pair = ConstraintSet(config_).getInputBounds();
    Eigen::MatrixXd u_lower = bounds_pair.first;
    Eigen::MatrixXd u_upper = bounds_pair.second;
    
    std::vector<std::pair<double, double>> bounds;
    for (int i = 0; i < config_.horizon; ++i) {
        bounds.push_back(std::make_pair(u_lower(i, 0), u_upper(i, 0)));  // velocity
        bounds.push_back(std::make_pair(u_lower(i, 1), u_upper(i, 1)));  // steering rate
    }
    
    return bounds;
}

void MPCSolver::setWeights(const Eigen::Matrix4d& Q,
                          const Eigen::Matrix2d& R,
                          const Eigen::Matrix4d& Q_terminal) {
    config_.Q = Q;
    config_.R = R;
    if (Q_terminal.norm() > 0) {
        config_.Q_terminal = Q_terminal;
    } else {
        config_.Q_terminal = Q * 2.0;
    }
}

void MPCSolver::resetWarmStart() {
    last_control_sequence_ = Eigen::MatrixXd::Zero(config_.horizon, 2);
    last_trajectory_ = Eigen::MatrixXd::Zero(config_.horizon + 1, 4);
}
