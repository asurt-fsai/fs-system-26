#pragma once

#include <Eigen/Dense>
#include "../config.h"
#include "../Spline/Arc_Spline.h"
#include "../Params/params.h"

namespace mpc_controller{
    
    class ConstraintSet {
    private:
        const Params& params_;
        
    public:
        explicit ConstraintSet(const Params& params);
        
        ///////////////////////////////////////////////////////////////////////////
        // State Bounds [x, y, theta, delta] - 4D
        ///////////////////////////////////////////////////////////////////////////
        Eigen::Vector4d getStateLowerBounds() const;
        Eigen::Vector4d getStateUpperBounds() const;
        
        ///////////////////////////////////////////////////////////////////////////
        // Input Bounds [v, delta_dot] - 2D
        ///////////////////////////////////////////////////////////////////////////
        Eigen::Vector2d getInputLowerBounds() const;
        Eigen::Vector2d getInputUpperBounds() const;
        
        ///////////////////////////////////////////////////////////////////////////
        // Matrix versions for MPC horizon (convenience methods)
        ///////////////////////////////////////////////////////////////////////////
        std::pair<Eigen::MatrixXd, Eigen::MatrixXd> getInputBounds() const;
        std::pair<Eigen::MatrixXd, Eigen::MatrixXd> getStateBounds() const;
        
        ///////////////////////////////////////////////////////////////////////////
        // Feasibility Check
        ///////////////////////////////////////////////////////////////////////////
        bool checkFeasibility(const Eigen::Vector4d& state,
                            const Eigen::Vector2d& control) const;
    };
    
}