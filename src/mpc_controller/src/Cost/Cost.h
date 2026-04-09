#ifndef COST_H
#define COST_H

#include <Eigen/Dense>
#include "../config.h"
#include "../Params/params.h"
#include "../Spline/Arc_Spline.h"

namespace mpc_controller {

struct CostMatrix{
    Eigen::MatrixXd Q;
    Eigen::MatrixXd R;
    Eigen::MatrixXd S;
    Eigen::VectorXd q;
    Eigen::VectorXd r;
    Eigen::MatrixXd Z;
    Eigen::VectorXd z;
};

struct TrackPoint{
    const double x_ref;
    const double y_ref;
    const double dx_ref;
    const double dy_ref;
    const double theta_ref;
    const double dtheta_ref;
};

struct ErrorInfo{
    const Eigen::Vector2d error;
    const Eigen::MatrixXd d_error;
};

class Cost {
public:
    CostMatrix getCost(const mpc_controller::ArcSpline &track, const Eigen::VectorXd &x, int k) const;

    Cost(const Params &config);

private:
    TrackPoint getRefPoint(const mpc_controller::ArcSpline &track, const mpc_controller::state &x) const;
    ErrorInfo  getErrorInfo(const mpc_controller::ArcSpline &track,  const mpc_controller::state &x) const;

    CostMatrix getContouringCost(const mpc_controller::ArcSpline &track, const mpc_controller::state &x, int k) const;
    CostMatrix getHeadingCost(const mpc_controller::ArcSpline &track, const mpc_controller::state &x, int k) const;
    CostMatrix getInputCost() const;
    CostMatrix getBetaCost(const mpc_controller::state &x) const;
    CostMatrix getBetaKinCost(const mpc_controller::state &x) const;
    CostMatrix getSoftConstraintCost() const;

    const Params& config_;
};

} // namespace mpc_controller

#endif // COST_H
