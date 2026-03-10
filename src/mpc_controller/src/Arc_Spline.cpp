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
        // remove points which are not at all equally spaced, to avoid fitting problems

        // compute mean distance between points and then process the points such that points
        // are not closer than 0.75 the mean distance

        double dx, dy, dx2, dy2;       // difference between points in x and y
        Eigen::VectorXd distances;     // vector with all the distances
        double mean_distance;          // mean distance
        double distance, distance2;    // temp variable for distance
        Points resamplePath;
        int k = 0;                     // indices
        int j = 0;

        // Validate input sizes match
        if (x.size() != y.size()) {
            std::cerr << "Error: X and Y arrays must have same size in outlierDetection" << std::endl;
            Points empty_path;
            empty_path.x.resize(0);
            empty_path.y.resize(0);
            return empty_path;
        }

        int n = x.size();

        // Handle edge case: empty input
        if (n == 0) {
            Points empty_path;
            empty_path.x.resize(0);
            empty_path.y.resize(0);
            return empty_path;
        }

        // Handle edge case: single point (cannot compute distances)
        if (n == 1) {
            Points single_point;
            single_point.x = x;
            single_point.y = y;
            return single_point;
        }

        // initialize with zero
        resamplePath.x.setZero(n);
        resamplePath.y.setZero(n);

        // compute distance between points in X-Y data
        distances.setZero(n-1);
        for(int i=0; i<n-1; i++) {
            dx = x(i+1) - x(i);
            dy = y(i+1) - y(i);
            distances(i) = std::sqrt(dx*dx + dy*dy);
        }
        
        // compute mean distance between points
        mean_distance = distances.sum()/(n-1);

        // compute the new points
        // start point is the original start point
        resamplePath.x(k) = x(k);
        resamplePath.y(k) = y(k);
        k++;
        for(int i=1; i<n-1; i++) {
            // compute distance between currently checked point and the one last added to the new X-Y path
            dx = x(i) - x(j);
            dy = y(i) - y(j);
            distance = std::sqrt(dx*dx + dy*dy);
            dx2 = x(i+1) - x(j);
            dy2 = y(i+1) - y(j);
            distance2 = std::sqrt(dx2*dx2 + dy2*dy2);

            // Skip point if: distance to last accepted < 0.7*mean AND distance to next point < 1.3*mean
            if(distance <= 0.7*mean_distance && distance2 <= 1.3*mean_distance)
            {
                continue;
            }
            resamplePath.x(k) = x(i);
            resamplePath.y(k) = y(i);
            k++;
            j = i;
        }
        // always add the last point
        resamplePath.x(k) = x(n-1);
        resamplePath.y(k) = y(n-1);
        k++;

        // set the new X-Y data
        resamplePath.x.conservativeResize(k);
        resamplePath.y.conservativeResize(k);

        return resamplePath;
    }