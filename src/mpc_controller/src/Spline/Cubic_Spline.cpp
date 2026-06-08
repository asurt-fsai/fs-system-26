/*
Cubic Spline Interpolation Implementation
Burden and Faires - Numerical Analysis, 9th Edition
Chapter : 3, Section: 3.5
*/


#include "Cubic_Spline.h"


namespace mpc_controller{
    CubicSpline::CubicSpline() : spline_data_set_(false) {}

    void CubicSpline::setregularSpacing(const Eigen::VectorXd& x, const Eigen::VectorXd& y,const double spacing){
        
        if (x.size() == y.size()) 
        {
            splineData.x = x;
            splineData.y = y;
            splineData.n = x.size();
            splineData.is_evenly_spaced = true;
            splineData.spacing = spacing;
            spline_data_set_ = true;
        } 
        else 
        {
            std::cout << "Input vectors x and y must have the same size." << std::endl;
            //throw std::invalid_argument("Input vectors x and y must have the same size.");
        }
    }

    void CubicSpline::setirregularSpacing(const Eigen::VectorXd& x, const Eigen::VectorXd& y,const double spacing)
    {
        if (x.size() == y.size()) 
        {
            splineData.x = x;
            splineData.y = y;
            splineData.n = x.size();
            splineData.is_evenly_spaced = false;
            spline_data_set_ = true;
        } 
        else 
        {
            std::cout << "Input vectors x and y must have the same size." << std::endl;
            //throw std::invalid_argument("Input vectors x and y must have the same size.");
        }
    }

    bool CubicSpline::computeCoefficients() 
    {
        //compute the coefficients of the cubic spline based on the input data
        if (!spline_data_set_) {
            std::cout << "Data not set. Please set data before computing coefficients." << std::endl;
            return false;
        }

        //set spline parameters to zero
        params_.a.setZero(splineData.n);
        params_.b.setZero(splineData.n - 1);
        params_.c.setZero(splineData.n);
        params_.d.setZero(splineData.n - 1);

        // Helping variables used to compute the coefficients
        Eigen::VectorXd h, alpha, l, mu, z;
        // sets the variables to zero for the size of the data
        h.setZero(splineData.n - 1);
        alpha.setZero(splineData.n - 1);
        l.setZero(splineData.n);
        mu.setZero(splineData.n);
        z.setZero(splineData.n);
        
        int n = splineData.n;
        params_.a = splineData.y; // a_i = y_i
        
        // for loop to compute h_i = x_{i+1} - x_i = dx for i = 0, 1, ..., n-2
        for (int i = 0; i < n - 1; ++i) {
            h(i) = splineData.x(i + 1) - splineData.x(i);
        }
        
        // Set up the system of equations
        // (alpha already declared and sized above via setZero)
        for (int i = 1; i < n - 1; ++i) {
            // calculate the alpha values based on the differences in y values and the spacing h
            alpha(i) = (3.0 / h(i)) * (params_.a(i + 1) - params_.a(i)) - (3.0 / h(i - 1)) * (params_.a(i) - params_.a(i - 1));
        }
        
        // Initialize the system of equations
        l(0) = 1.0;
        mu(0) = z(0) = 0.0;
        
        for (int i = 1; i < n - 1; ++i) {
            // calculate the l, mu, and z values for the system of equations based on the alpha values and the spacing h 
            l(i) = 2.0 * (splineData.x(i + 1) - splineData.x(i - 1)) - h(i - 1) * mu(i - 1);
            mu(i) = h(i) / l(i);
            z(i) = (alpha(i) - h(i - 1) * z(i - 1)) / l(i);
        }
        // Set the boundary conditions for a natural spline (second derivative at endpoints is zero)
        l(n - 1) = 1.0;
        z(n - 1) = params_.c(n - 1) = 0.0;
        
        // Back substitution to solve for c
        for (int j = n - 2; j >= 0; --j) {
            params_.c(j) = z(j) - mu(j) * params_.c(j + 1);
            params_.b(j) = (params_.a(j + 1) - params_.a(j)) / h(j) - h(j) * (params_.c(j + 1) + 2.0 * params_.c(j)) / 3.0;
            params_.d(j) = (params_.c(j + 1) - params_.c(j)) / (3.0 * h(j));
        }
        return true;
    }

    int CubicSpline::findSegment(const double x) const {
        // given a x value find the closest point in the spline to evaluate it
        // special case if x is regularly spaced
        // assumes wrapped data!

        // if special case of end points
        if(x == splineData.x(splineData.n - 1))
        {
            return splineData.n - 1;
        }
        // if regular index can be found by rounding
        if(splineData.is_evenly_spaced)
        {
            return static_cast<int>(std::floor(x / splineData.spacing));
        }
        // if irregular index need to be searched
        else
        {
            auto it = std::upper_bound(splineData.x.data(), splineData.x.data() + splineData.n, x);
            if(it == splineData.x.data() + splineData.n)
                return -1;
            else{
                return std::distance(splineData.x.data(), it) - 1;
            }
        }
    }

    // For Wrap around input for periodic data if the car has to go around the track multiple times, we can use this function to wrap the input back to the range of the data
    double CubicSpline::unwrapinput(const double x) const {
        double x_max = splineData.x(splineData.n - 1);
        return x - x_max * std::floor(x / x_max);
    }

    void CubicSpline::generateSpline(const Eigen::VectorXd& x, const Eigen::VectorXd& y, bool is_evenly_spaced)
    {
        if(is_evenly_spaced)
        {
            double spacing = x(1) - x(0);
            setregularSpacing(x, y, spacing);
        }
        else
        {
            setirregularSpacing(x, y, 0.0);
        }
        computeCoefficients();
    }

    double CubicSpline::getPoint(double x_query) const
    {
        // unwrap the input if necessary, find the segment, and evaluate the spline at the query point
        double x_unwrapped = unwrapinput(x_query);
        int segment = findSegment(x_unwrapped);
        if(segment == -1)
        {
            std::cout << "Query point is out of bounds." << std::endl;
            // TODO make it return the closest point on the spline instead of just returning 0
            return 0.0; // or throw an exception
        }
        double dx = x_unwrapped - splineData.x(segment);
        return params_.a(segment) + params_.b(segment) * dx + params_.c(segment) * dx * dx + params_.d(segment) * dx * dx * dx;
    }

    double CubicSpline::getDerivative(double x_query) const
    {
        double x_unwrapped = unwrapinput(x_query);
        int segment = findSegment(x_unwrapped);
        if(segment == -1)
        {
            std::cout << "Query point is out of bounds." << std::endl;
            // TODO make it return the closest point on the spline instead of just returning 0
            return 0.0; // or throw an exception
        }
        double dx = x_unwrapped - splineData.x(segment);
        return params_.b(segment) + 2.0 * params_.c(segment) * dx + 3.0 * params_.d(segment) * dx * dx;
    }

    double CubicSpline::getSecondDerivative(double x_query) const
    {
        double x_unwrapped = unwrapinput(x_query);
        int segment = findSegment(x_unwrapped);
        if(segment == -1)
        {
            std::cout << "Query point is out of bounds." << std::endl;
            // TODO make it return the closest point on the spline instead of just returning 0
            return 0.0; // or throw an exception
        }
        double dx = x_unwrapped - splineData.x(segment);
        return 2.0 * params_.c(segment) + 6.0 * params_.d(segment) * dx;
    }
    } // namespace mpc_controller)
        