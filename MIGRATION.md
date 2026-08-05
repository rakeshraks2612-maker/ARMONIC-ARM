# Migrating Your Workload to ARMONIC

## Step 1: Prepare your workload
Ensure your workload is a single Python file with a main() entry point.

## Step 2: Place in workloads/
cp your_workload.py workloads/my_workload.py

## Step 3: Update config
Edit config.yaml:
pipeline:
  target_workload: "workloads/my_workload.py"

## Step 4: Run
make run

## Step 5: Review the branch
ARMONIC creates armonic/auto-refactor-<timestamp>. Review the diff before merging.
