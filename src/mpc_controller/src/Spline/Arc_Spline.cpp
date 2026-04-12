#include "Arc_Spline.h"


static constexpr int N_SPLINE = 5000;


namespace mpc_controller{

    void ArcSpline::setregularSpacing(const Eigen::VectorXd& x, const Eigen::VectorXd& y, const double spacing){
        if (x.size() == y.size()) 
        {
            splineData.x = x;
            splineData.y = y;
            splineData.n = x.size();
            splineData.s = computeArcLength();
        } 
        else 
        {
            std::cout << "Input vectors x and y must have the same size." << std::endl;
            //throw std::invalid_argument("Input vectors x and y must have the same size.");
        }
    }

    void ArcSpline::setirregularSpacing(const Eigen::VectorXd& x, const Eigen::VectorXd& y, const double spacing)
    {
        if (x.size() == y.size()) 
        {
            splineData.x = x;
            splineData.y = y;
            splineData.n = x.size();
            // TODO: Use spacing parameter to set splineData.s appropriately
        } 
        else 
        {
            std::cout << "Input vectors x and y must have the same size." << std::endl;
            //throw std::invalid_argument("Input vectors x and y must have the same size.");
        }
    }

    Eigen::VectorXd ArcSpline::computeArcLength() const
    {
        // compute the arc lenght based on the straight line distance between the points, this is not the true arc length but it is a good approximation for closely spaced points
        // TODO implement a more accurate arc length computation method that takes into account the curvature of the path
        double dx, dy;
        double distance;

        int n = splineData.x.size();
        Eigen::VectorXd s(n);
        s(0) = 0.0;
        for(int i = 1; i < n - 1; ++i)
        {
            dx = splineData.x(i + 1) - splineData.x(i);
            dy = splineData.y(i + 1) - splineData.y(i);
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

    points ArcSpline::outlierDetection(const Eigen::VectorXd& x, const Eigen::VectorXd& y) const
    {
        // NOTE: The points struct only holds a single x,y pair, not vectors
        // This function needs to be redesigned or the return type changed to PathData
        // For now, returning the first point as a placeholder
        
        points result;
        if (x.size() > 0 && y.size() > 0) {
            result.x = x(0);
            result.y = y(0);
        } else {
            result.x = 0.0;
            result.y = 0.0;
        }
        return result;
    }

    PathData ArcSpline::outlierRemoval(const Eigen::VectorXd& x, const Eigen::VectorXd& y) const
    {
        // Remove outliers, depending on how irregular the points are this can help
        // For now, return input data without modification
        // TODO: Implement proper outlier removal algorithm
        PathData clean_path;
        clean_path.x = x;
        clean_path.y = y;
        clean_path.n = x.size();
        return clean_path;
    }

    void ArcSpline::generateSpline(const Eigen::VectorXd& x, const Eigen::VectorXd& y)
    {
        // Generate 2-D arc length parametrized spline given x-y data

        // Remove outliers, depending on how irregular the points are this can help
        PathData clean_path;
        clean_path = outlierRemoval(x, y);
        // Successively fit spline and re-sample
        fitSpline(clean_path.x, clean_path.y);
    }

    Eigen::Vector2d ArcSpline::getPosition(double s_query) const
    {
        double x = params_x.getPoint(s_query);
        double y = params_y.getPoint(s_query);
        return Eigen::Vector2d(x, y);
    }

    Eigen::Vector2d ArcSpline::getDerivative(double s_query) const
    {
        double dx = params_x.getDerivative(s_query);
        double dy = params_y.getDerivative(s_query);
        return Eigen::Vector2d(dx, dy);
    }

    Eigen::Vector2d ArcSpline::getSecondDerivative(double s_query) const
    {
        double ddx = params_x.getSecondDerivative(s_query);
        double ddy = params_y.getSecondDerivative(s_query);
        return Eigen::Vector2d(ddx, ddy);
    }

    void ArcSpline::fitSpline(const Eigen::VectorXd& x, const Eigen::VectorXd& y)
    {
        // Successively fit spline -> re-sample path -> compute arc length
        // Temporary spline class only used for fitting
        Eigen::VectorXd s_approximation;
        PathData first_refined_path, second_refined_path;
        double total_arc_length;

        // Store input data temporarily to compute arc length
        splineData.x = x;
        splineData.y = y;
        splineData.n = x.size();
        s_approximation = computeArcLength();
        total_arc_length = s_approximation(s_approximation.size() - 1);

        CubicSpline first_spline_x, first_spline_y;
        CubicSpline second_spline_x, second_spline_y;
        
        // 1. spline fit
        first_spline_x.generateSpline(s_approximation, x, false);
        first_spline_y.generateSpline(s_approximation, y, false);
        
        // 1. re-sample
        first_refined_path = resamplePath(first_spline_x, first_spline_y, total_arc_length);
        
        // Update splineData to compute arc length of refined path
        splineData.x = first_refined_path.x;
        splineData.y = first_refined_path.y;
        splineData.n = first_refined_path.x.size();
        s_approximation = computeArcLength();

        total_arc_length = s_approximation(s_approximation.size() - 1);
        
        // 2. spline fit
        second_spline_x.generateSpline(s_approximation, first_refined_path.x, false);
        second_spline_y.generateSpline(s_approximation, first_refined_path.y, false);
        
        // 2. re-sample
        second_refined_path = resamplePath(second_spline_x, second_spline_y, total_arc_length);
        
        // Store the refined path data in splineData
        splineData.x = second_refined_path.x;
        splineData.y = second_refined_path.y;
        splineData.s = second_refined_path.s;
        splineData.n = second_refined_path.n;
        
        // Final spline fit with fixed Delta_s
        params_x.generateSpline(splineData.s, splineData.x, true);
        params_y.generateSpline(splineData.s, splineData.y, true);
    }

    double ArcSpline::projectOntoSpline(const Eigen::Vector2d& point) const
    {
        // Project a point onto the spline and return the corresponding s value
        // Using Newton's method to minimize the distance between the point and the spline
        
        // Initial guess: use middle of spline or find closest point in path data
        double s_guess = 0.0;
        if (splineData.n > 0 && splineData.s.size() > 0) {
            s_guess = splineData.s(splineData.n - 1) / 2.0;  // Start at middle
        }
        
        Eigen::Vector2d pos_path = getPosition(s_guess);
        double s_opt = s_guess;
        double dist = (point - pos_path).norm();
        
        // Maximum distance threshold for projection (in meters or appropriate units)
        const double max_dist_proj = 5.0;  // Threshold for considering initial guess valid
        
        if (dist >= max_dist_proj)
        {
            std::cout << "dist too large" << std::endl;
            // Find closest point in the discrete path data
            Eigen::ArrayXd diff_x_all = splineData.x.array() - point(0);
            Eigen::ArrayXd diff_y_all = splineData.y.array() - point(1);
            Eigen::ArrayXd dist_square = diff_x_all.square() + diff_y_all.square();
            std::vector<double> dist_square_vec(dist_square.data(), dist_square.data() + dist_square.size());
            auto min_iter = std::min_element(dist_square_vec.begin(), dist_square_vec.end());
            s_opt = splineData.s(std::distance(dist_square_vec.begin(), min_iter));
        }
        
        double s_old = s_opt;
        // Newton's method for optimization
        for(int i = 0; i < 20; i++)
        {
            pos_path = getPosition(s_opt);
            Eigen::Vector2d ds_path = getDerivative(s_opt);
            Eigen::Vector2d dds_path = getSecondDerivative(s_opt);
            Eigen::Vector2d diff = pos_path - point;
            double jac = 2.0 * diff(0) * ds_path(0) + 2.0 * diff(1) * ds_path(1);
            double hessian = 2.0 * ds_path(0) * ds_path(0) + 2.0 * diff(0) * dds_path(0) +
                             2.0 * ds_path(1) * ds_path(1) + 2.0 * diff(1) * dds_path(1);
            // Newton method
            s_opt -= jac / hessian;
            s_opt = unwrapinput(s_opt);
            
            if(std::abs(s_old - s_opt) <= 1e-5)
                return s_opt;
            s_old = s_opt;
        }
        
        // Something is strange if it did not converge within 20 iterations, give back the initial guess
        return s_guess;
    }

    double ArcSpline::unwrapinput(const double s_query) const {
        double s_max = splineData.s(splineData.n - 1);
        if (s_max <= 0.0) return s_query;
        return s_query - s_max * std::floor(s_query / s_max);
    }

} // namespace mpc_controller