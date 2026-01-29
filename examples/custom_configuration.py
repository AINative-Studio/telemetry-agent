#!/usr/bin/env python3
"""
Custom Configuration Example

Demonstrates different ways to configure the Context Agent.
"""

from context_agent import ContextAgent
import os
import json
import time


def example_1_inline_config():
    """Example 1: Inline configuration dictionary"""
    print("\n" + "=" * 50)
    print("Example 1: Inline Configuration")
    print("=" * 50)

    config = {
        "polling_interval": 3,
        "context_threshold": 85,
        "sensor_timeout": 5,
        "enable_zerodb": False
    }

    agent = ContextAgent(config=config)
    agent.start()

    print(f"Polling interval: {config['polling_interval']}s")
    print(f"Context threshold: {config['context_threshold']}%")

    time.sleep(4)
    state = agent.get_state()
    print(f"Current state: {state.display}")

    agent.stop()


def example_2_environment_vars():
    """Example 2: Configuration from environment variables"""
    print("\n" + "=" * 50)
    print("Example 2: Environment Variables")
    print("=" * 50)

    # Set environment variables
    os.environ["AGENT_POLLING_INTERVAL"] = "10"
    os.environ["AGENT_CONTEXT_THRESHOLD"] = "90"

    # Environment variables are read automatically
    agent = ContextAgent()
    agent.start()

    print(f"Configuration loaded from environment variables")
    time.sleep(2)

    state = agent.get_state()
    print(f"Current state: {state.display}")

    agent.stop()


def example_3_json_file():
    """Example 3: Configuration from JSON file"""
    print("\n" + "=" * 50)
    print("Example 3: JSON Configuration File")
    print("=" * 50)

    # Create temporary config file
    config_data = {
        "polling_interval": 5,
        "context_threshold": 80,
        "sensor_timeout": 5,
        "enable_zerodb": False
    }

    config_file = "/tmp/agent_config.json"
    with open(config_file, "w") as f:
        json.dump(config_data, f, indent=2)

    # Load configuration from file
    with open(config_file) as f:
        config = json.load(f)

    agent = ContextAgent(config=config)
    agent.start()

    print(f"Configuration loaded from: {config_file}")
    time.sleep(2)

    state = agent.get_state()
    print(f"Current state: {state.display}")

    agent.stop()

    # Cleanup
    os.remove(config_file)


def example_4_merged_config():
    """Example 4: Merged configuration from multiple sources"""
    print("\n" + "=" * 50)
    print("Example 4: Merged Configuration")
    print("=" * 50)

    # Default configuration
    config = {
        "polling_interval": 5,
        "context_threshold": 80,
        "sensor_timeout": 5
    }

    # Override with environment variables if present
    if os.getenv("AGENT_POLLING_INTERVAL"):
        config["polling_interval"] = int(os.getenv("AGENT_POLLING_INTERVAL"))

    # Override with specific values
    config.update({
        "context_threshold": 90  # This takes precedence
    })

    agent = ContextAgent(config=config)
    agent.start()

    print(f"Merged configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")

    time.sleep(2)
    state = agent.get_state()
    print(f"Current state: {state.display}")

    agent.stop()


def example_5_development_vs_production():
    """Example 5: Environment-specific configuration"""
    print("\n" + "=" * 50)
    print("Example 5: Environment-Specific Configuration")
    print("=" * 50)

    # Detect environment
    env = os.getenv("ENVIRONMENT", "development")
    print(f"Environment: {env}")

    # Development configuration
    dev_config = {
        "polling_interval": 2,
        "context_threshold": 70,
        "sensor_timeout": 10,
        "enable_zerodb": False
    }

    # Production configuration
    prod_config = {
        "polling_interval": 10,
        "context_threshold": 85,
        "sensor_timeout": 5,
        "enable_zerodb": True,
        "zerodb_batch_size": 50
    }

    # Select configuration based on environment
    config = dev_config if env == "development" else prod_config

    agent = ContextAgent(config=config)
    agent.start()

    print(f"Using {env} configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")

    time.sleep(2)
    state = agent.get_state()
    print(f"Current state: {state.display}")

    agent.stop()


def main():
    """Run all configuration examples"""
    print("Context Agent - Custom Configuration Examples")

    example_1_inline_config()
    example_2_environment_vars()
    example_3_json_file()
    example_4_merged_config()
    example_5_development_vs_production()

    print("\n" + "=" * 50)
    print("All examples completed!")
    print("=" * 50)


if __name__ == "__main__":
    main()
