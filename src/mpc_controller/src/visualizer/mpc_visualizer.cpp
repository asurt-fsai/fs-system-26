#include "mpc_visualizer.h"
#include <cmath>
#include <geometry_msgs/msg/transform_stamped.hpp>

// ─────────────────────────────────────────────────────────────────────────────
MPCVisualizer::MPCVisualizer()
    : Node("mpc_visualizer")
{
    /* ---------- parameters ---------- */
    declare_parameter("car_length",   car_length_);
    declare_parameter("car_width",    car_width_);
    declare_parameter("wheelbase",    wheelbase_);
    declare_parameter("track_width",  track_width_);
    declare_parameter("r_inner",      r_inner_);
    declare_parameter("r_outer",      r_outer_);
    declare_parameter("cone_spacing", cone_spacing_);
    car_length_   = get_parameter("car_length").as_double();
    car_width_    = get_parameter("car_width").as_double();
    wheelbase_    = get_parameter("wheelbase").as_double();
    track_width_  = get_parameter("track_width").as_double();
    r_inner_      = get_parameter("r_inner").as_double();
    r_outer_      = get_parameter("r_outer").as_double();
    cone_spacing_ = get_parameter("cone_spacing").as_int();

    /* ---------- subscribers ---------- */
    odom_sub_ = create_subscription<nav_msgs::msg::Odometry>(
        "/carmaker/Odometry", 10,
        std::bind(&MPCVisualizer::odomCallback, this, std::placeholders::_1));
    ref_path_sub_ = create_subscription<nav_msgs::msg::Path>(
        "/path", rclcpp::QoS(10).transient_local(),
        std::bind(&MPCVisualizer::pathCallback, this, std::placeholders::_1));
    pred_path_sub_ = create_subscription<nav_msgs::msg::Path>(
        "/mpc/predicted_path", 10,
        std::bind(&MPCVisualizer::predictedPathCallback, this, std::placeholders::_1));

    /* ---------- publishers ---------- */
    marker_pub_     = create_publisher<visualization_msgs::msg::MarkerArray>(
        "/mpc/track_markers", 10);
    heading_pub_    = create_publisher<visualization_msgs::msg::Marker>(
        "/mpc/heading_arrow", 10);
    footprint_pub_  = create_publisher<visualization_msgs::msg::Marker>(
        "/mpc/vehicle_footprint", 10);
    constraint_pub_ = create_publisher<visualization_msgs::msg::MarkerArray>(
        "/mpc/constraint_markers", 10);
    pred_viz_pub_   = create_publisher<visualization_msgs::msg::MarkerArray>(
        "/mpc/predicted_path_viz", 10);

    tf_broadcaster_ = std::make_unique<tf2_ros::TransformBroadcaster>(*this);

    /* 20 Hz visualisation timer */
    vis_timer_ = create_wall_timer(
        std::chrono::milliseconds(50),
        std::bind(&MPCVisualizer::timerCallback, this));

    RCLCPP_INFO(get_logger(), "MPC Visualizer started  car=%.1f×%.1fm  track_hw=%.1fm",
                car_length_, car_width_, track_width_);
}

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────
double MPCVisualizer::getYawFromQuat(const geometry_msgs::msg::Quaternion& q) const
{
    tf2::Quaternion tq(q.x, q.y, q.z, q.w);
    double r, p, y;
    tf2::Matrix3x3(tq).getRPY(r, p, y);
    return y;
}

size_t MPCVisualizer::findClosestIndex(double px, double py) const
{
    double best_dist = 1e20;
    size_t best = 0;
    for (size_t j = 0; j < reference_path_->poses.size(); ++j) {
        double dx = reference_path_->poses[j].pose.position.x - px;
        double dy = reference_path_->poses[j].pose.position.y - py;
        double d  = dx * dx + dy * dy;
        if (d < best_dist) { best_dist = d; best = j; }
    }
    return best;
}

// ─────────────────────────────────────────────────────────────────────────────
// Callbacks
// ─────────────────────────────────────────────────────────────────────────────
void MPCVisualizer::odomCallback(const nav_msgs::msg::Odometry::SharedPtr msg)
{
    latest_odom_ = msg;
    has_odom_    = true;
}

void MPCVisualizer::pathCallback(const nav_msgs::msg::Path::SharedPtr msg)
{
    reference_path_ = msg;
    has_ref_path_   = true;
    publishTrackMarkers();
}

void MPCVisualizer::predictedPathCallback(const nav_msgs::msg::Path::SharedPtr msg)
{
    predicted_path_ = msg;
    has_pred_path_  = true;
}

void MPCVisualizer::timerCallback()
{
    if (has_odom_) {
        publishHeadingArrow(*latest_odom_);
        publishVehicleFootprint(*latest_odom_);
        broadcastTF(*latest_odom_);
    }
    // Republish track markers at ~1 Hz so late-joining RViz always sees them
    if (has_ref_path_) {
        static int track_counter = 0;
        if (++track_counter >= 20) {  // 20 × 50 ms = 1 s
            publishTrackMarkers();
            track_counter = 0;
        }
    }
    if (has_pred_path_) {
        publishPredictedPath();
        publishTrackConstraints();
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Track centerline + boundaries + cones
// Uses the orientation quaternion from each PoseStamped for accurate normals
// ─────────────────────────────────────────────────────────────────────────────
void MPCVisualizer::publishTrackMarkers()
{
    if (!has_ref_path_ || reference_path_->poses.empty()) return;

    visualization_msgs::msg::MarkerArray ma;
    auto stamp = now();
    const size_t n = reference_path_->poses.size();

    // ━━ Centerline (LINE_STRIP, bright green) ━━━━━━━━━━━━━━━━━━━━━━━━━━
    visualization_msgs::msg::Marker center;
    center.header.frame_id = "map";
    center.header.stamp    = stamp;
    center.ns       = "track_center";
    center.id       = 0;
    center.type     = visualization_msgs::msg::Marker::LINE_STRIP;
    center.action   = visualization_msgs::msg::Marker::ADD;
    center.scale.x  = 0.06;
    center.color.r  = 0.2f; center.color.g = 0.9f; center.color.b = 0.2f; center.color.a = 1.0f;
    center.pose.orientation.w = 1.0;

    // ━━ Left boundary (LINE_STRIP, red) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    visualization_msgs::msg::Marker left_wall = center;
    left_wall.ns = "track_left";  left_wall.id = 1;
    left_wall.scale.x = 0.04;
    left_wall.color.r = 1.0f; left_wall.color.g = 0.15f; left_wall.color.b = 0.15f; left_wall.color.a = 1.0f;

    // ━━ Right boundary (LINE_STRIP, blue) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    visualization_msgs::msg::Marker right_wall = center;
    right_wall.ns = "track_right"; right_wall.id = 2;
    right_wall.scale.x = 0.04;
    right_wall.color.r = 0.15f; right_wall.color.g = 0.3f; right_wall.color.b = 1.0f; right_wall.color.a = 1.0f;

    // ━━ Left cones (SPHERE_LIST, red-orange) ━━━━━━━━━━━━━━━━━━━━━━━━━━
    visualization_msgs::msg::Marker left_cones;
    left_cones.header.frame_id = "map";
    left_cones.header.stamp    = stamp;
    left_cones.ns      = "cones_left";
    left_cones.id      = 3;
    left_cones.type    = visualization_msgs::msg::Marker::SPHERE_LIST;
    left_cones.action  = visualization_msgs::msg::Marker::ADD;
    left_cones.scale.x = 0.35; left_cones.scale.y = 0.35; left_cones.scale.z = 0.5;
    left_cones.color.r = 1.0f; left_cones.color.g = 0.4f; left_cones.color.b = 0.0f; left_cones.color.a = 1.0f;
    left_cones.pose.orientation.w = 1.0;

    // ━━ Right cones (SPHERE_LIST, blue) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    visualization_msgs::msg::Marker right_cones = left_cones;
    right_cones.ns = "cones_right"; right_cones.id = 4;
    right_cones.color.r = 0.0f; right_cones.color.g = 0.3f; right_cones.color.b = 1.0f;

    for (size_t i = 0; i < n; ++i) {
        const auto& ps = reference_path_->poses[i];
        double px = ps.pose.position.x;
        double py = ps.pose.position.y;

        geometry_msgs::msg::Point pc;
        pc.x = px; pc.y = py; pc.z = 0.0;
        center.points.push_back(pc);

        // Use the heading quaternion from the path for accurate normal computation
        double yaw = getYawFromQuat(ps.pose.orientation);
        // Left normal: 90° CCW from heading (inner boundary — to the left of travel)
        double nx = -std::sin(yaw);
        double ny =  std::cos(yaw);

        geometry_msgs::msg::Point pl, pr;
        pl.x = px + nx * r_inner_;  pl.y = py + ny * r_inner_;  pl.z = 0.0;
        pr.x = px - nx * r_outer_;  pr.y = py - ny * r_outer_;  pr.z = 0.0;
        left_wall.points.push_back(pl);
        right_wall.points.push_back(pr);

        // Cones every N points
        if (static_cast<int>(i) % cone_spacing_ == 0) {
            geometry_msgs::msg::Point cl, cr;
            cl.x = pl.x; cl.y = pl.y; cl.z = 0.15;
            cr.x = pr.x; cr.y = pr.y; cr.z = 0.15;
            left_cones.points.push_back(cl);
            right_cones.points.push_back(cr);
        }
    }

    ma.markers.push_back(center);
    ma.markers.push_back(left_wall);
    ma.markers.push_back(right_wall);
    ma.markers.push_back(left_cones);
    ma.markers.push_back(right_cones);
    marker_pub_->publish(ma);
}

// ─────────────────────────────────────────────────────────────────────────────
// Heading + velocity arrow
// ─────────────────────────────────────────────────────────────────────────────
void MPCVisualizer::publishHeadingArrow(const nav_msgs::msg::Odometry& odom)
{
    double yaw = getYawFromQuat(odom.pose.pose.orientation);
    double v   = odom.twist.twist.linear.x;
    double arrow_len = std::max(1.0, std::min(v * 0.5, 4.0));  // scale with speed

    visualization_msgs::msg::Marker arrow;
    arrow.header.frame_id = "map";
    arrow.header.stamp    = now();
    arrow.ns   = "heading";
    arrow.id   = 0;
    arrow.type = visualization_msgs::msg::Marker::ARROW;
    arrow.action = visualization_msgs::msg::Marker::ADD;

    geometry_msgs::msg::Point start, end;
    start.x = odom.pose.pose.position.x;
    start.y = odom.pose.pose.position.y;
    start.z = 0.2;
    end.x = start.x + arrow_len * std::cos(yaw);
    end.y = start.y + arrow_len * std::sin(yaw);
    end.z = 0.2;

    arrow.points.push_back(start);
    arrow.points.push_back(end);
    arrow.scale.x = 0.10;  // shaft diameter
    arrow.scale.y = 0.20;  // head diameter
    arrow.scale.z = 0.25;  // head length
    arrow.color.r = 1.0f; arrow.color.g = 0.9f; arrow.color.b = 0.0f; arrow.color.a = 1.0f;

    heading_pub_->publish(arrow);
}

// ─────────────────────────────────────────────────────────────────────────────
// Vehicle footprint — wireframe rectangle with 4 wheels (LINE_LIST in base_link)
// ─────────────────────────────────────────────────────────────────────────────
void MPCVisualizer::publishVehicleFootprint(const nav_msgs::msg::Odometry& /*odom*/)
{
    visualization_msgs::msg::Marker m;
    m.header.frame_id = "base_link";
    m.header.stamp    = now();
    m.ns   = "vehicle_body";
    m.id   = 0;
    m.type = visualization_msgs::msg::Marker::LINE_LIST;
    m.action = visualization_msgs::msg::Marker::ADD;
    m.scale.x = 0.04;  // line width
    m.color.r = 0.0f; m.color.g = 0.85f; m.color.b = 1.0f; m.color.a = 1.0f;
    m.pose.orientation.w = 1.0;

    // Body corners (rear axle at origin, CG between axles)
    double rear_overhang  = (car_length_ - wheelbase_) * 0.35;
    double front_overhang = car_length_ - wheelbase_ - rear_overhang;
    double x_rear  = -rear_overhang;
    double x_front = wheelbase_ + front_overhang;
    double hw = car_width_ / 2.0;

    // Helper lambda
    auto pt = [](double x, double y, double z) {
        geometry_msgs::msg::Point p;
        p.x = x; p.y = y; p.z = z;
        return p;
    };
    double bz = 0.15;  // body z height

    // 4 edges of the body rectangle
    m.points.push_back(pt(x_rear,  -hw, bz)); m.points.push_back(pt(x_front, -hw, bz));
    m.points.push_back(pt(x_front, -hw, bz)); m.points.push_back(pt(x_front,  hw, bz));
    m.points.push_back(pt(x_front,  hw, bz)); m.points.push_back(pt(x_rear,   hw, bz));
    m.points.push_back(pt(x_rear,   hw, bz)); m.points.push_back(pt(x_rear,  -hw, bz));

    // Center line (rear axle → front axle)
    m.points.push_back(pt(0.0, 0.0, bz)); m.points.push_back(pt(wheelbase_, 0.0, bz));

    // Wheel markers: small rectangles at each axle corner
    double wl = 0.30;  // wheel length
    double ww = 0.06;  // wheel width offset
    // Rear-left
    m.points.push_back(pt(-wl/2, -hw - ww, bz)); m.points.push_back(pt(wl/2, -hw - ww, bz));
    m.points.push_back(pt(-wl/2,  -hw + ww, bz)); m.points.push_back(pt(wl/2, -hw + ww, bz));
    m.points.push_back(pt(-wl/2, -hw - ww, bz)); m.points.push_back(pt(-wl/2, -hw + ww, bz));
    m.points.push_back(pt( wl/2, -hw - ww, bz)); m.points.push_back(pt( wl/2, -hw + ww, bz));
    // Rear-right
    m.points.push_back(pt(-wl/2,  hw - ww, bz)); m.points.push_back(pt(wl/2,  hw - ww, bz));
    m.points.push_back(pt(-wl/2,  hw + ww, bz)); m.points.push_back(pt(wl/2,  hw + ww, bz));
    m.points.push_back(pt(-wl/2,  hw - ww, bz)); m.points.push_back(pt(-wl/2, hw + ww, bz));
    m.points.push_back(pt( wl/2,  hw - ww, bz)); m.points.push_back(pt( wl/2, hw + ww, bz));
    // Front-left
    double fx = wheelbase_;
    m.points.push_back(pt(fx-wl/2, -hw - ww, bz)); m.points.push_back(pt(fx+wl/2, -hw - ww, bz));
    m.points.push_back(pt(fx-wl/2, -hw + ww, bz)); m.points.push_back(pt(fx+wl/2, -hw + ww, bz));
    m.points.push_back(pt(fx-wl/2, -hw - ww, bz)); m.points.push_back(pt(fx-wl/2, -hw + ww, bz));
    m.points.push_back(pt(fx+wl/2, -hw - ww, bz)); m.points.push_back(pt(fx+wl/2, -hw + ww, bz));
    // Front-right
    m.points.push_back(pt(fx-wl/2,  hw - ww, bz)); m.points.push_back(pt(fx+wl/2,  hw - ww, bz));
    m.points.push_back(pt(fx-wl/2,  hw + ww, bz)); m.points.push_back(pt(fx+wl/2,  hw + ww, bz));
    m.points.push_back(pt(fx-wl/2,  hw - ww, bz)); m.points.push_back(pt(fx-wl/2, hw + ww, bz));
    m.points.push_back(pt(fx+wl/2,  hw - ww, bz)); m.points.push_back(pt(fx+wl/2, hw + ww, bz));

    footprint_pub_->publish(m);
}

// ─────────────────────────────────────────────────────────────────────────────
// Predicted path — line + spheres at each step for clarity
// ─────────────────────────────────────────────────────────────────────────────
void MPCVisualizer::publishPredictedPath()
{
    if (!has_pred_path_ || predicted_path_->poses.empty()) return;

    visualization_msgs::msg::MarkerArray ma;
    auto stamp = now();

    // Predicted trajectory line
    visualization_msgs::msg::Marker line;
    line.header.frame_id = "map";
    line.header.stamp    = stamp;
    line.ns   = "predicted_line";
    line.id   = 0;
    line.type = visualization_msgs::msg::Marker::LINE_STRIP;
    line.action = visualization_msgs::msg::Marker::ADD;
    line.scale.x = 0.08;
    line.color.r = 1.0f; line.color.g = 0.0f; line.color.b = 0.8f; line.color.a = 1.0f;
    line.pose.orientation.w = 1.0;

    // Step markers (spheres)
    visualization_msgs::msg::Marker spheres;
    spheres.header.frame_id = "map";
    spheres.header.stamp    = stamp;
    spheres.ns   = "predicted_steps";
    spheres.id   = 1;
    spheres.type = visualization_msgs::msg::Marker::SPHERE_LIST;
    spheres.action = visualization_msgs::msg::Marker::ADD;
    spheres.scale.x = 0.18; spheres.scale.y = 0.18; spheres.scale.z = 0.18;
    spheres.color.r = 1.0f; spheres.color.g = 0.2f; spheres.color.b = 1.0f; spheres.color.a = 0.9f;
    spheres.pose.orientation.w = 1.0;

    for (const auto& ps : predicted_path_->poses) {
        geometry_msgs::msg::Point p;
        p.x = ps.pose.position.x;
        p.y = ps.pose.position.y;
        p.z = 0.1;
        line.points.push_back(p);
        spheres.points.push_back(p);
    }

    ma.markers.push_back(line);
    ma.markers.push_back(spheres);
    pred_viz_pub_->publish(ma);
}

// ─────────────────────────────────────────────────────────────────────────────
// Track constraints at predicted path poses
// ─────────────────────────────────────────────────────────────────────────────
void MPCVisualizer::publishTrackConstraints()
{
    if (!has_pred_path_ || predicted_path_->poses.empty()) return;
    if (!has_ref_path_  || reference_path_->poses.empty()) return;

    visualization_msgs::msg::MarkerArray ma;
    auto stamp = now();

    // Delete old markers first
    visualization_msgs::msg::Marker del;
    del.header.frame_id = "map";
    del.header.stamp    = stamp;
    del.action = visualization_msgs::msg::Marker::DELETEALL;
    del.ns     = "constraints";
    ma.markers.push_back(del);

    for (size_t i = 0; i < predicted_path_->poses.size(); ++i) {
        double px = predicted_path_->poses[i].pose.position.x;
        double py = predicted_path_->poses[i].pose.position.y;

        size_t ci = findClosestIndex(px, py);

        // Use the heading quaternion from the reference path for the normal
        double yaw = getYawFromQuat(reference_path_->poses[ci].pose.orientation);
        double nx = -std::sin(yaw);
        double ny =  std::cos(yaw);

        // Constraint normal line: inner boundary on left side, outer on right side
        double cx = reference_path_->poses[ci].pose.position.x;
        double cy = reference_path_->poses[ci].pose.position.y;

        visualization_msgs::msg::Marker line;
        line.header.frame_id = "map";
        line.header.stamp    = stamp;
        line.ns   = "constraints";
        line.id   = static_cast<int>(i);
        line.type = visualization_msgs::msg::Marker::LINE_STRIP;
        line.action = visualization_msgs::msg::Marker::ADD;
        line.scale.x = 0.04;
        line.color.r = 1.0f; line.color.g = 0.5f; line.color.b = 0.0f; line.color.a = 0.6f;
        line.pose.orientation.w = 1.0;

        geometry_msgs::msg::Point p1, p2;
        p1.x = cx - nx * r_outer_;  p1.y = cy - ny * r_outer_;  p1.z = 0.05;
        p2.x = cx + nx * r_inner_;  p2.y = cy + ny * r_inner_;  p2.z = 0.05;
        line.points.push_back(p1);
        line.points.push_back(p2);
        ma.markers.push_back(line);
    }

    constraint_pub_->publish(ma);
}

// ─────────────────────────────────────────────────────────────────────────────
// TF: map → base_link
// ─────────────────────────────────────────────────────────────────────────────
void MPCVisualizer::broadcastTF(const nav_msgs::msg::Odometry& odom)
{
    geometry_msgs::msg::TransformStamped t;
    t.header.stamp    = now();
    t.header.frame_id = "map";
    t.child_frame_id  = "base_link";
    t.transform.translation.x = odom.pose.pose.position.x;
    t.transform.translation.y = odom.pose.pose.position.y;
    t.transform.translation.z = 0.0;
    t.transform.rotation      = odom.pose.pose.orientation;
    tf_broadcaster_->sendTransform(t);
}
