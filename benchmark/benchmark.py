import boto3
import concurrent.futures
import time
import re
from datetime import datetime, UTC

# AWS clients
lambda_client = boto3.client('lambda')
logs_client = boto3.client('logs')

# Configuration
functions = [
    {"name": "test-DotnetSnapstartVsAotStack-LambdaNet8", "alias": "$LATEST"},
    {"name": "test-DotnetSnapstartVsAotStack-LambdaNet8", "alias": "SnapStart"},
    {"name": "test-DotnetSnapstartVsAotStack-LambdaNet8Aot", "alias": "$LATEST"}
]
concurrency_factor = 100
log_group_prefix = "/aws/lambda/"
log_patterns = {
    "Init Duration": re.compile(r"Init Duration: ([\d.]+) ms"),
    "Restore Duration": re.compile(r"Restore Duration: ([\d.]+) ms"),
    "Duration": re.compile(r"Duration: ([\d.]+) ms")
}


# Helper to invoke Lambda function concurrently
def invoke_function_concurrently(function_name, alias):
    def invoke2():
        try:
            lambda_client.invoke(
                FunctionName=f"{function_name}:{alias}",
                InvocationType="RequestResponse",
                LogType="Tail",
                Payload=b'"hello"'
            )
        except Exception as e:
            print(f"Error invoking Lambda function: {e}")

    def invoke():
        lambda_client.invoke(FunctionName=f"{function_name}:{alias}", InvocationType="RequestResponse", LogType="Tail",
                             Payload=b'"hello"')

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency_factor) as executor:
        futures = [executor.submit(invoke2) for _ in range(concurrency_factor)]
        concurrent.futures.wait(futures)


# Helper to get logs from CloudWatch
def get_logs(function_name, start_time):
    log_group_name = f"{log_group_prefix}{function_name}"
    logs = []
    paginator = logs_client.get_paginator('filter_log_events')
    for page in paginator.paginate(
            logGroupName=log_group_name,
            startTime=int(start_time.timestamp() * 1000),
            filterPattern="REPORT"
    ):
        for event in page['events']:
            logs.append(event['message'])
    return logs


# Parse log for specific metrics
def parse_logs(logs, patterns):
    results = []
    for i, log in enumerate(logs, 1):
        parsed = {"#": i}
        for key, pattern in patterns.items():
            if pattern:  # Ensure the pattern is not None
                match = pattern.search(log)
                if match:
                    parsed[key] = float(match.group(1))
        results.append(parsed)
    return results


# Display results in table format
def display_table(results, columns, title):
    print(f"\n{title}")
    # Print header
    header = " | ".join(f"{col:^12}" for col in columns)
    print("-" * len(header))
    print(header)
    print("-" * len(header))
    # Print rows
    for row in results:
        row_data = " | ".join(
            f"{row.get(col, '-'):>12.2f}" if isinstance(row.get(col), float) else f"{row.get(col, '-'):>12}" for col in
            columns)
        print(row_data)
    print("-" * len(header))


# Main script
for index, func in enumerate(functions, 1):
    print(f"\n=== Processing Function {index}: {func['name']}, alias {func['alias']} ===")
    start_time = datetime.now(UTC)

    time.sleep(5)

    print("Invoking function concurrently...")
    invoke_function_concurrently(func['name'], func['alias'])

    time.sleep(30)  # Wait for logs to be available

    print("Fetching logs...")
    logs = get_logs(func['name'], start_time)

    print("Parsing logs...")
    if func['alias'] == "SnapStart":
        results = parse_logs(logs, {"#": None, "Duration": log_patterns["Duration"],
                                    "Restore Duration": log_patterns["Restore Duration"]})
        display_table(results, ["#", "Duration", "Restore Duration"], f"Function {index} Results")
    else:
        results = parse_logs(logs, {"#": None, "Duration": log_patterns["Duration"],
                                    "Init Duration": log_patterns["Init Duration"]})
        display_table(results, ["#", "Duration", "Init Duration"], f"Function {index} Results")
