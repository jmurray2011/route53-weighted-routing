# AWS Route 53 Weighted Routing Lambda

This project includes a Python script designed to toggle the weight of DNS records using AWS Route 53's API. The script is meant to be deployed as an AWS Lambda function, triggered by CloudWatch alarms, responding to changes in system health or other criteria.

## Features

- **Dynamic DNS Weight Adjustment**: Automatically adjust the weight of DNS records to reroute traffic between primary and secondary resources based on system health.
- **Logging**: Comprehensive logging for tracking the script's operation and errors.
- **AWS Integration**: Designed to work with AWS Lambda, Route53, and SNS messages.

## Prerequisites

Before you deploy this script, ensure you have:

- AWS account with access to Route53, Lambda, and CloudWatch.
- The necessary permissions to create and manage Lambda functions and Route53 records.
- A lambda function with the necessary permissions to modify Route53 records.
- A DNS record set in Route53 with the desired primary and secondary resources.
  - Ensure that the record set is a weighted routing policy.
  - The primary and secondary resources should have different weights (e.g. 0 and 1, where 0 is the secondary resource and 1 is the primary resource).
    - Note that records weighted 0 will not receive traffic.
  - The primary and secondary resources should have unique identifiers.

### IAM Permissions

Ensure that the Lambda function has the necessary permissions to modify Route53 records. You can attach the following policy to a role and assign it to the Lambda.

#### Trust Policy

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

#### Permissions Policy

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "route53:ListResourceRecordSets",
                "route53:ChangeResourceRecordSets"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}
```

## Environment Variables

Set the following local environment variables. You can use the example.env, just rename to .env and source it. FUNCTIONS_NAME is the name of the lambda function you created in the AWS console.

- `FUNCTION_NAME=test-failover-dns`
- `SOURCE_FILE=lambda_function.py`
- `AWS_PROFILE=default`
- `AWS_REGION=us-east-1`

Set the following environment variables in your Lambda configuration:

- `HOSTED_ZONE_ID`: The ID of the hosted zone in AWS Route53.
- `RECORD_SET_NAME`: The name of the record set (ensure this ends with a dot).
- `PRIMARY_IDENTIFIER`: Identifier for the primary resource.
- `SECONDARY_IDENTIFIER`: Identifier for the secondary resource.
- `RECORD_TYPE`: The type of DNS record, e.g., A, AAAA, CNAME.

## Deployment

1. Package the script and any dependencies into a deployment package.
2. Create a new Lambda function in the AWS Management Console.
3. Configure the trigger to be the desired CloudWatch alarm.
4. Set the necessary environment variables in the Lambda configuration.
5. Upload and deploy the package.

## Usage

Once deployed and configured with the correct triggers and environment variables, the Lambda function will automatically run and adjust DNS weights in response to CloudWatch alarm state changes.

- **ALARM State**: Redirects traffic from the primary to the secondary resource by adjusting weights.
- **OK State**: Shifts traffic back to the primary resource.

Ensure that your CloudWatch alarms are correctly set up to trigger the function based on your specific use case.
