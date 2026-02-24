

#ifndef MPC_CONTROLLER_CUBIC_SPLINE_H
#define MPC_CONTROLLER_CUBIC_SPLINE_H

#include "config.h"


namespace mpc_controller{
    // Cubic Spline Interpolation Parameters and Data Structures y  = a + b dx + c dx^2 + d dx^3
    struct SplineParams
    {
        Eigen::VectorXd a;
        Eigen::VectorXd b;
        Eigen::VectorXd c;
        Eigen::VectorXd d;
    };

    struct SplineData

    {
        Eigen::VectorXd x;
        Eigen::VectorXd y;
        int n;
        bool is_evenly_spaced;
        double spacing;
        std::vector<double> t;
    };

    class CubicSpline{    
        public:
            // Constructors and evaluation methods
            CubicSpline() = default;
            CubicSpline(const Eigen::VectorXd& x, const Eigen::VectorXd& y, bool is_evenly_spaced = false);
            // Evaluate spline and its derivatives at a query point
            double evaluate(double x_query);
            double evaluateDerivative(double x_query);
            double evaluateSecondDerivative(double x_query);
            
        private:
            SplineParams params_;
            SplineData splineData;
            bool spline_data_set_;
            
            
            void setregularSpacing(const Eigen::VectorXd& x, const Eigen::VectorXd& y,const double spacing); 
            void setirregularSpacing(const Eigen::VectorXd& x, const Eigen::VectorXd& y,const double spacing);
            bool computeCoefficients();
            int findSegment(const double x_query) const;
            double unwrapinput(const double x_query) const;
    };

    
}

#endif // MPC_CONTROLLER_CUBIC_SPLINE_H