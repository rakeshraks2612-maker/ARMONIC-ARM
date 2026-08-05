# Contributing to ARMONIC

Thank you for your interest in making ARMONIC better.

## Getting Started

git clone https://github.com/rakeshraks2612-maker/ARMONIC-ARM.git
cd ARMONIC-ARM
make install
make test

## Adding a New Workload

1. Place your Python file in workloads/
2. Add a run_test() function that returns a deterministic string
3. Update config.yaml with the new target path
4. Run make run

## Adding LLM Providers

Edit src/refactor_engine/agent_core.py and extend fetch_llm_optimization() with your provider's API client.

## Code Style

- Follow PEP 8
- Run make lint before committing
- Add tests in tests/ for new modules

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
