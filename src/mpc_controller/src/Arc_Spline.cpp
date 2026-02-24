#include "Arc_Spline.h"


static constexpr int N_SPLINE = 5000;


namespace mpc_controller{

    void ArcSpline::setregularSpacing(const Eigen::VectorXd& x, const Eigen::VectorXd& y){
        if (x.size() == y.size()) 
        {
            splineData.x = x;
            splineData.y = y;
            splineData.n = x.size();
            splineData.s = getTotalLength();
        } 
        else 
        {
            std::cout << "Input vectors x and y must have the same size." << std::endl;
            //throw std::invalid_argument("Input vectors x and y must have the same size.");
        }
    }

    void ArcSpline::setirregularSpacing(const Eigen::VectorXd& x, const Eigen::VectorXd& y, const Eigen::VectorXd& s)
    {
        if (x.size() == y.size()) 
        {
            splineData.x = x;
            splineData.y = y;
            splineData.n = x.size();
            splineData.s = s;
        } 
        else 
        {
            std::cout << "Input vectors x and y must have the same size." << std::endl;
            //throw std::invalid_argument("Input vectors x and y must have the same size.");
        }
    }

    Eigen::vectorXd ArcSpline::computeArcLength(const Eigen::VectorXd& x, const Eigen::VectorXd& y) const
    {
        // compute the arc lenght based on the straight line distance between the points, this is not the true arc length but it is a good approximation for closely spaced points
        // TODO implement a more accurate arc length computation method that takes into account the curvature of the path
        double dx, dy;
        double distance;

        int n = x.size();
        Eigen::vectorXd s(n);
        s(0) = 0.0;
        for(int i = 1; i < n - 1; ++i)
        {
            dx = x(i + 1) - x(i);
            dy = y(i + 1) - y(i);
            distance = std::sqrt(dx * dx + dy * dy);
            s(i + 1) = s(i) + distance;
        }
        return s;
    }

    PathData ArcSpline::resamplePath(const CubicSpline& spline_x, const CubicSpline& spline_y, const double max_s) const
    {
        // the function resampled path is the path that is resampled at regular intervals of s, this is done by evaluating the spline at regular intervals of s and storing the resulting x and y values in a new PathData struct
        PathData resampledData;
        // N_SPLINE is the number of points to resample the path to, this is a hyperparameter that can be tuned based on the desired resolution of the path 
        resampledData.n = N_SPLINE;
        resampledData.x.setZero(N_SPLINE);
        resampledData.y.setZero(N_SPLINE);
        resampledData.s.setLinSpaced(N_SPLINE, 0.0, max_s); // sets a linearly spaced vector of s values from 0 to max_s with N_SPLINE points
        for(int i = 0; i < N_SPLINE; ++i)
        {
            resampledData.x(i) = spline_x.getPoint(resampledData.s(i));
            resampledData.y(i) = spline_y.getPoint(resampledData.s(i));
        }
        return resampledData;
    }

    Points ArcSpline::outlierDetection(const Eigen::VectorXd& x, const Eigen::VectorXd& y) const
    {
        double dx, dy;
        Eigen::VectorXd distances;
        double mean_distance;
        double distance;
        Points resamplePath;
        int k = 0; 
        int j = 0;

        if (x.size() != y.size()) 
        {
            // TODO throw an exception or return an empty vector
            std::cout << "Input vectors x and y must have the same size." << std::endl;
            //throw std::invalid_argument("Input vectors x and y must have the same size.");
        }

        int n = x.size();

        resamplePath.x.setZero(n);
        resamplePath.y.setZero(n);
        distances.setZero(n);

        for (int i=0; i < n; i++)
        {
            dx = x(i+1) - x(i);
            dy = y(i+1) - y(i);
            // distance = std::sqrt(dx * dx + dy * dy);
            distances(i) = std::sqrt(dx * dx + dy * dy);
        }
        // find if the mean function is faster than if i use a for loop to compute the mean distance
        mean_distance = distances.mean();
        
        // compute the new points
        // the start point is the original start point
        // TODO dive deep more into how this works
        resamplePath.x(k) = x(k);
        resamplePath.y(k) = y(k);
        k++;


    }