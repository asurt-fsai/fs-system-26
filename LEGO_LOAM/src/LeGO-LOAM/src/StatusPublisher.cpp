/**
 * StatusPublisher class to provide an easy way to publish a heartbeat
 */
#include "StatusPublisher.h"
#include "rmw/rmw.h"  // ✅ CORRECT for Humble
#include <algorithm>
#include <stdexcept>


// Static member initialization
std::vector<std::string> StatusPublisher::topicNamesCreated = {};

/**
 * Class used to publish a heartbeat.
 * Each node should have one and only one StatusPublisher
 * The following are the statuses that can be published:
 *     - Starting
 *     - Ready
 *     - Running
 *     - Error
 * 
 * Parameters
 * ----------
 * topicName: std::string
 *     Name of the topic to publish the heartbeat on
 *     IMPORTANT: must be unique, otherwise an exception will be thrown
 */
StatusPublisher::StatusPublisher(const std::string &topicName, rclcpp::Node::SharedPtr nodeObject)
{
    if (std::find(topicNamesCreated.begin(), topicNamesCreated.end(), topicName) != topicNamesCreated.end())
    {
        throw std::invalid_argument(
            "StatusPublisher: Topic name already exists, "
            "can't publish a heartbeat on the same topic twice"
        );
    }

    auto latchingQOS = rclcpp::QoS(rclcpp::KeepLast(1)).transient_local().reliable();  // ✅ Replace here
    this->nodeObject = nodeObject;
    this->publisher = this->nodeObject->create_publisher<asurt_msgs::msg::NodeStatus>(topicName, latchingQOS);
    topicNamesCreated.push_back(topicName);
}


/**
 * Creates a base NodeStatus message with a timestamp
 * 
 * Returns
 * -------
 * asurt_msgs::msg::NodeStatus
 *     Base NodeStatus message
 */
asurt_msgs::msg::NodeStatus StatusPublisher::baseMessage()
{
    asurt_msgs::msg::NodeStatus msg;
    msg.header.stamp = this->nodeObject->get_clock()->now();
    return msg;
}

/**
 * Publishes a NodeStatus message with the state "Starting"
 */
void StatusPublisher::starting()
{
    std::lock_guard<std::mutex> guard(lock);
    auto msg = this->baseMessage();
    msg.status = 0;
    this->publisher->publish(msg);
}

/**
 * Publishes a NodeStatus message with the state "Ready"
 */
void StatusPublisher::ready()
{
    std::lock_guard<std::mutex> guard(lock);
    auto msg = this->baseMessage();
    msg.status = 1;
    this->publisher->publish(msg);
}

/**
 * Publishes a NodeStatus message with the state "Running"
 */
void StatusPublisher::running()
{
    std::lock_guard<std::mutex> guard(lock);
    auto msg = this->baseMessage();
    msg.status = 2;
    this->publisher->publish(msg);
}

/**
 * Publishes a NodeStatus message with the state "Error"
 * 
 * Parameters
 * ----------
 * errMsg: std::string
 *     Error message to include with the NodeStatus message
 */
void StatusPublisher::error(const std::string &errMsg)
{
    std::lock_guard<std::mutex> guard(lock);
    auto msg = this->baseMessage();
    msg.status = 3;
    msg.message = errMsg;
    this->publisher->publish(msg);
}
