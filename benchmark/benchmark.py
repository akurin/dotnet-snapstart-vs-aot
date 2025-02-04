import boto3
import concurrent.futures
import time
import re
import logging
from datetime import datetime, UTC
from tabulate import tabulate

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# AWS clients
lambda_client = boto3.client('lambda')
logs_client = boto3.client('logs')

# Configuration
functions = [
    {"name": "test-DotnetSnapstartVsAotStack-LambdaNet8", "alias": "$LATEST"},
    {"name": "test-DotnetSnapstartVsAotStack-LambdaNet8", "alias": "SnapStart"},
    {"name": "test-DotnetSnapstartVsAotStack-LambdaNet8Aot", "alias": "$LATEST"}
]

concurrency_factor = 10
log_group_prefix = "/aws/lambda/"


# Helper to invoke Lambda function concurrently
def invoke_function_concurrently(function_name, alias):
    def invoke():
        try:
            lambda_client.invoke(
                FunctionName=f"{function_name}:{alias}",
                InvocationType="RequestResponse",
                LogType="Tail",
                Payload=b'"hello"'
            )
        except Exception as e:
            logger.error(f"Error invoking Lambda function: {e}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency_factor) as executor:
        futures = [executor.submit(invoke) for _ in range(concurrency_factor)]
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
def parse_logs(logs, pattern):
    results = []
    for _, log in enumerate(logs, 1):
        match = pattern.search(log)
        if match:
            results.append(tuple(map(float, match.groups())))
    return results


restore_re = re.compile(r".*Duration: ([\d.]+) ms.*Restore Duration: ([\d.]+) ms")
init_re = re.compile(r"REPORT.*Duration: ([\d.]+) ms.*Init Duration: ([\d.]+) ms")

# Main script
for index, func in enumerate(functions, 1):
    logger.info(f"=== Processing Function {index}: {func['name']}, alias {func['alias']} ===")
    start_time = datetime.now(UTC)

    time.sleep(5)

    logger.info("Invoking function concurrently...")
    invoke_function_concurrently(func['name'], func['alias'])

    time.sleep(30)  # Wait for logs to be available

    logger.info("Fetching logs...")
    logs = get_logs(func['name'], start_time)

    logger.info("Parsing logs...")

    if func['alias'] == "SnapStart":
        results = parse_logs(logs, restore_re)
        headers = ["Duration", "Restore Duration"]
    else:
        results = parse_logs(logs, init_re)
        headers = ["Duration", "Init Duration"]

    if not results:
        logger.error("No cold start logs found")
        continue

    print(tabulate(results, headers=headers, tablefmt="github"))

    for i in range(len(headers)):
        # get the ith element of each tuple
        ith_elements = [x[i] for x in results]
        min_val = min(ith_elements)
        max_val = max(ith_elements)
        avg_val = sum(ith_elements) / len(ith_elements)
        sorted_elements = sorted(ith_elements)
        mid = len(sorted_elements) // 2
        median_val = (sorted_elements[mid] + sorted_elements[~mid]) / 2

        print(f"{headers[i]}: min={min_val}, max={max_val}, avg={avg_val}, median={median_val}")

