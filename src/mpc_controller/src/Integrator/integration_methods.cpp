#include "integration_methods.h"

namespace integration {

Eigen::MatrixXd predictTrajectory(
    const Eigen::VectorXd& initial_state,
    const Eigen::MatrixXd& controls,
    std::function<Eigen::VectorXd(const Eigen::VectorXd&, const Eigen::VectorXd&)> state_derivative_fn,
    double dt,
    bool use_rk4) {
    
    int num_steps = controls.rows();
    int state_dim = initial_state.size();
    
    Eigen::MatrixXd trajectory(num_steps + 1, state_dim);
    trajectory.row(0) = initial_state.transpose();
    
    for (int i = 0; i < num_steps; ++i) {
        Eigen::VectorXd current_state = trajectory.row(i).transpose();
        Eigen::VectorXd current_control = controls.row(i).transpose();
        
        Eigen::VectorXd next_state;
        if (use_rk4) {
            next_state = rungeKutta4<5, 2>(
                current_state,
                current_control,
                state_derivative_fn,
                dt
            );
        } else {
            next_state = eulerForward<5, 2>(
                current_state,
                current_control,
                state_derivative_fn,
                dt
            );
        }
        
        trajectory.row(i + 1) = next_state.transpose();
    }
    
    return trajectory;
}

} // namespace integration
