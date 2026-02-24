// mpc_solver_nlopt.cpp.example
// This shows how to integrate NLOPT for advanced optimization
// Much faster than gradient descent!

/*
To use this, install NLOPT:
  sudo apt-get install libnlopt-dev libnlopt-cxx-dev

Then add to CMakeLists.txt:
  find_package(nlopt REQUIRED)
  target_link_libraries(mpc_lib nlopt::nlopt)

And replace the solve() function in mpc_solver.cpp with this implementation:
*/

#include <nlopt.hpp>
#include "mpc_controller/mpc_solver.h"
#include "mpc_controller/utils.h"

class NLoptObjective {
public:
    NLoptObjective(
        const Eigen::Vector4d& x0,
        const Eigen::MatrixXd& ref_traj,
        const MPCSolver* solver,
        const BicycleModel* model)
        : x0_(x0), ref_traj_(ref_traj), solver_(solver), model_(model) {}
    
    double operator()(const std::vector<double>& u, std::vector<double>& grad) const {
        // Convert flat control vector to matrix
        Eigen::MatrixXd controls = Eigen::Map<const Eigen::MatrixXd>(
            u.data(), solver_->config_.horizon, 2);
        
        // Compute trajectory
        Eigen::MatrixXd trajectory = model_->predictTrajectory(x0_, controls);
        
        // Compute cost
        double cost = solver_->computeCost(trajectory, controls, ref_traj_);
        
        // Compute gradient (numerical)
        if (!grad.empty()) {
            double eps = 1e-5;
            for (size_t i = 0; i < u.size(); ++i) {
                std::vector<double> u_pert = u;
                u_pert[i] += eps;
                
                Eigen::MatrixXd controls_pert = Eigen::Map<const Eigen::MatrixXd>(
                    u_pert.data(), solver_->config_.horizon, 2);
                Eigen::MatrixXd traj_pert = model_->predictTrajectory(x0_, controls_pert);
                double cost_pert = solver_->computeCost(traj_pert, controls_pert, ref_traj_);
                
                grad[i] = (cost_pert - cost) / eps;
            }
        }
        
        return cost;
    }

private:
    const Eigen::Vector4d& x0_;
    const Eigen::MatrixXd& ref_traj_;
    const MPCSolver* solver_;
    const BicycleModel* model_;
};

// Alternative: Better approach using NLOPT directly in solve()
/*
MPCSolver::SolveInfo MPCSolver::solve(
    const Eigen::Vector4d& x0,
    const Eigen::MatrixXd& reference_trajectory,
    Eigen::MatrixXd& optimal_controls,
    Eigen::MatrixXd& predicted_trajectory,
    const Eigen::MatrixXd& x0_control) {
    
    SolveInfo info;
    int n_vars = config_.horizon * 2;  // horizon control steps with 2 inputs each
    
    // Setup NLOPT optimizer
    nlopt::opt opt(nlopt::LD_SLSQP, n_vars);
    
    // Set bounds
    auto [u_lower, u_upper] = ConstraintSet(config_).getInputBounds();
    std::vector<double> lower_bounds, upper_bounds;
    
    for (int i = 0; i < config_.horizon; ++i) {
        lower_bounds.push_back(u_lower(i, 0));  // v_min
        lower_bounds.push_back(u_lower(i, 1));  // delta_dot_min
        upper_bounds.push_back(u_upper(i, 0));  // v_max
        upper_bounds.push_back(u_upper(i, 1));  // delta_dot_max
    }
    
    opt.set_lower_bounds(lower_bounds);
    opt.set_upper_bounds(upper_bounds);
    
    // Set objective function
    // Lambda captures model and config
    opt.set_min_objective([this, &x0, &reference_trajectory](
        const std::vector<double>& u, std::vector<double>& grad) {
        
        Eigen::MatrixXd controls = Eigen::Map<const Eigen::MatrixXd>(
            const_cast<double*>(u.data()), config_.horizon, 2);
        Eigen::MatrixXd trajectory = model_.predictTrajectory(x0, controls);
        
        double cost = computeCost(trajectory, controls, reference_trajectory);
        
        if (!grad.empty()) {
            // Compute gradient numerically
            double eps = 1e-5;
            for (size_t i = 0; i < u.size(); ++i) {
                std::vector<double> u_pert = u;
                u_pert[i] += eps;
                
                Eigen::MatrixXd controls_pert = Eigen::Map<const Eigen::MatrixXd>(
                    u_pert.data(), config_.horizon, 2);
                Eigen::MatrixXd traj_pert = model_.predictTrajectory(x0, controls_pert);
                double cost_pert = computeCost(traj_pert, controls_pert, reference_trajectory);
                
                grad[i] = (cost_pert - cost) / eps;
            }
        }
        
        return cost;
    });
    
    // Set tolerances
    opt.set_ftol_rel(1e-6);
    opt.set_ftol_abs(1e-8);
    opt.set_xtol_rel(1e-6);
    opt.set_maxtime(0.01);  // 10ms maximum solve time
    
    // Warm start with last solution
    std::vector<double> u_init(n_vars);
    Eigen::Map<Eigen::MatrixXd>(u_init.data(), config_.horizon, 2) = last_control_sequence_;
    
    // Optimize
    double opt_cost;
    nlopt::result result = opt.optimize(u_init, opt_cost);
    
    // Extract solution
    optimal_controls = Eigen::Map<Eigen::MatrixXd>(u_init.data(), config_.horizon, 2);
    predicted_trajectory = model_.predictTrajectory(x0, optimal_controls);
    
    // Store for warm-start
    last_control_sequence_ = optimal_controls;
    last_trajectory_ = predicted_trajectory;
    
    // Fill info struct
    info.success = (result > 0);
    info.cost = opt_cost;
    info.iterations = 0;  // NLOPT doesn't track this easily
    info.message = "Solved with NLOPT";
    
    last_solve_info_ = info;
    return info;
}
*/

// Key advantages of NLOPT:
// 1. Convergence ~10-100x faster than gradient descent
// 2. Supports multiple algorithms (SLSQP, MMA, AUGLAG, etc.)
// 3. Built-in stopping criteria (time, tolerance, iterations)
// 4. Better constraint handling
// 5. Production-grade solver used in industry

// Algorithm recommendations:
// - LD_SLSQP: Good for small problems (~10-100 variables), fast
// - LD_MMA: Good for nonlinear problems, slightly slower
// - LD_AUGLAG: Robust for constrained problems, slower but reliable

// Performance tips:
// - Set opt.set_maxtime(0.01) to limit solve time to 10ms
// - Use warm-starting (previous solution as initial guess)
// - Tune weights Q and R to avoid ill-conditioned problems
// - Consider linear MPC for even faster solving (but less accurate)
