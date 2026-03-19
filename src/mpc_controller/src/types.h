#ifndef MPC_TYPES_H
#define MPC_TYPES_H

#include "config.h"
namespace mpc_controller{
    struct state{
        double x; // Global X position (meters)
        double y; // Global Y position (meters)
        double vx; // Longitudinal velocity (m/s)
        double vy; // Lateral velocity (m/s)
        double theta; // Heading/yaw angle (radians)
        double r; // Yaw rate (rad/s)
        double delta; // Steering angle of front wheel (radians)
        double v; // Longitudinal velocity (m/s)
        double Throttle; // The pedal position, which is used to limit the jerk of the acceleration, it is not directly used in the dynamics but it is used to compute the acceleration using the throttleToAcceleration function in the BicycleModel class
        double s; // arc length along the track

        void setZero(){
            x = 0.0;
            y = 0.0;
            vx = 0.0;
            vy = 0.0;
            theta = 0.0;
            r = 0.0;
            delta = 0.0;
            v = 0.0;
            s = 0.0;
        }
        void unwrapTheta(){
            if (theta > M_PI) {
                theta -= 2 * M_PI;
            } else if (theta < -M_PI) {
                theta += 2 * M_PI;
            }
        }
        void unwrapS(double track_length){
            if (s > track_length) {
                s -= track_length;
            } else if (s < 0) {
                s += track_length;
            }
        }
    };

    struct control{
        double D_dot; // Delta Throttle of perssing the pedal (m/s²)
        double delta_dot; // steering angle rate
        double dV_ghost; // Ghost velocity rate, used to compute the ghost error in the cost function, it is not directly used in the dynamics but it is used to compute the ghost error using the getErrorInfo function in the Cost class

        void setZero(){
            D_dot = 0.0;
            delta_dot = 0.0;
            dV_ghost = 0.0;
        }
    };
    
    struct PathToJson{
        // a struct to hold the paths to the json files for model parameters, bounds, costs, and normalization parameters
        const std::string model_path;
        const std::string bounds_path;
        const std::string costs_path;
        const std::string normalization_path;
    };


    typedef Eigen::Matrix<double, 9, 1> StateVector;
    typedef Eigen::Matrix<double, 3, 1> ControlVector;

    StateVector StateToVector(const state& X);
    ControlVector ControlToVector(const control& U);

    state VectorToState(const StateVector& X_vec);
    control VectorToControl(const ControlVector& U_vec);

}
#endif //MPC_Types_H