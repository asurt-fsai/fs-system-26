#include "cubic_spline.h"

namespace mpc_controller{

    struct points{
        double x;
        double y;
    };

    struct PathData{
        Eigen::VectorXd x;
        Eigen::VectorXd y;
        Eigen::vectroXd s; // cumulative distance along the path
        int n; // number of points
    };

    class ArcSpline{
        public:
            Eigen::vector2d getPoint(double s_query) const;
            Eigen::vector2d getDerivative(double s_query) const;
            Eigen::vector2d getSecondDerivative(double s_query) const;
            void generateSpline(const Eigen::VectorXd& x, const Eigen::VectorXd& y);
            double getTotalLength() const { return splineData.s(splineData.n - 1); }
            double projectOntoSpline(const Eigen::Vector2d& point) const; // projects a point onto the spline and returns the corresponding s value
    
        private:
            void setregularSpacing(const Eigen::VectorXd& x, const Eigen::VectorXd& y,const double spacing); 
            void setirregularSpacing(const Eigen::VectorXd& x, const Eigen::VectorXd& y,const double spacing);
            double unwrapinput(const double x_query) const;
            Eigen::vectorXd computeArcLength() const; // computes the cumulative distance along the path
            void fitSplineToArcLength(); // computes the cumulative distance along the path and fits a spline to s vs x and s vs y
            points outlierDetection(const Eigen::VectorXd& x, const Eigen::VectorXd& y) const; // detects outliers in the input data and returns the indices of the outliers 
            PathData resamplePath(const CubicSpline& spline_x, const CubicSpline& spline_y, const double max_s) const; // resamples the path at regular intervals of s and returns the resampled path data
            PathData splineData;
            CubicSpline params_x; // spline parameters for x(s)
            CubicSpline params_y; // spline parameters for y(s)
    
    }

}