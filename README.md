# InfraWatch

InfraWatch is a Windows and Linux infrastructure monitoring and security platform developed as a portfolio project.

The goal of the project is to provide centralized visibility into hosts, system metrics, network services, availability, and security-related events across small IT infrastructures.

## Current Status

InfraWatch is currently in early development.

Available functionality:

- FastAPI backend
- Health-check endpoint
- Automated API testing with pytest
- Code quality checks with Ruff
- Python package configuration through `pyproject.toml`

## Planned Features

- Windows and Linux host inventory
- PostgreSQL persistence
- Host availability monitoring
- TCP service checks
- CPU, memory, disk, and uptime collection
- Windows/Linux monitoring agent
- Historical metrics
- Rule-based alerts
- Authentication and API security
- Audit logging
- Web dashboard
- Docker-based deployment
- Continuous Integration with GitHub Actions

## Architecture

The planned architecture is:

```text
Windows/Linux Agents
        |
        v
     FastAPI
        |
        v
   PostgreSQL
        |
        v
 Monitoring and
  Alert Engine
        |
        v
 Web Dashboard

