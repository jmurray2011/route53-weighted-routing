import logging
import boto3
import json
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AWS clients
route53_client = boto3.client('route53')

# Define the necessary resources
hosted_zone_id = os.environ['HOSTED_ZONE_ID']
# the record set name (read, DNS name, e.g. "example.com") must contain the trailing dot, e.g. "example.com."
record_set_name = os.environ['RECORD_SET_NAME']
primary_identifier = os.environ['PRIMARY_IDENTIFIER']
secondary_identifier = os.environ['SECONDARY_IDENTIFIER']
record_type = os.environ['RECORD_TYPE']

def get_alias_target_dns_name(identifier):
    """
    Retrieve the DNS name of the Alias target for a DNS record.
    Args:
        hosted_zone_id: The ID of the hosted zone that contains the DNS records.
        record_set_name: The name of the DNS record set to retrieve.
        record_type: The type of the DNS record set to retrieve.
    Returns:
        The DNS name of the Alias target if found, None otherwise.
    """
    try:
        # Retrieve the current record set details
        response = route53_client.list_resource_record_sets(
            HostedZoneId=hosted_zone_id
        )
        
        # Filter the record sets to find the matching one
        for record_set in response['ResourceRecordSets']:
            if record_set['Name'] == record_set_name and record_set['SetIdentifier'] == identifier and record_set['Type'] == record_type and 'AliasTarget' in record_set:
                return record_set['AliasTarget']['DNSName'], record_set['AliasTarget']['HostedZoneId']
        logger.error(f"Alias target not found for {record_set_name} with type {record_type}.")
    except Exception as e:
        logger.error(f"Error retrieving alias target DNS name: {e}", exc_info=True)
    return None

def set_dns_record_weight(identifier, weight, alias_dns_name, alias_hosted_zone_id):
    """
    Set the weight of a DNS record set (assumes it's an Alias).
    Args:
        identifier: A string identifying the DNS record set.
        weight: The new weight for the DNS record.
        alias_dns_name: The DNS name of the Alias target.
        alias_hosted_zone_id: The hosted zone ID of the Alias target.
    """
    try:
        # Construct the change batch for updating the DNS weight
        change_batch = {
            'Changes': [{
                'Action': 'UPSERT',
                'ResourceRecordSet': {
                    'Name': record_set_name,
                    'Type': record_type,
                    'Weight': weight,
                    'SetIdentifier': identifier,
                    'AliasTarget': {
                        'DNSName': alias_dns_name,
                        'HostedZoneId': alias_hosted_zone_id,
                        'EvaluateTargetHealth': False
                    }
                }
            }]
        }

        # Update the DNS record set
        response = route53_client.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch=change_batch
        )
        logger.info(f"DNS record {record_set_name} - {identifier} weight toggled to {weight}. Response: {response}")
    except Exception as e:
        logger.error(f"Error setting DNS record weight: {e}", exc_info=True)

def lambda_handler(event, context):
    """
    AWS Lambda handler function triggered by a CloudWatch alarm.
    Args:
        event: The event dict that contains information about the CloudWatch Alarm state change.
        context: The context runtime information.
    """
    print(event)
    # Parse the SNS message
    sns_message = json.loads(event['Records'][0]['Sns']['Message'])
    
    # Extract the "NewStateValue" from the SNS message
    new_state = sns_message['NewStateValue']
    
    # Retrieve the DNS name of the Alias target
    pri_alias_dns_name, pri_alias_hosted_zone_id = get_alias_target_dns_name(primary_identifier)
    sec_alias_dns_name, sec_alias_hosted_zone_id = get_alias_target_dns_name(secondary_identifier)

    if pri_alias_dns_name and sec_alias_dns_name:
        if new_state == 'ALARM':
            set_dns_record_weight(primary_identifier, 0, pri_alias_dns_name, pri_alias_hosted_zone_id)
            set_dns_record_weight(secondary_identifier, 1, sec_alias_dns_name, sec_alias_hosted_zone_id)
        elif new_state == 'OK':
            set_dns_record_weight(primary_identifier, 1, pri_alias_dns_name, pri_alias_hosted_zone_id)
            set_dns_record_weight(secondary_identifier, 0, sec_alias_dns_name, sec_alias_hosted_zone_id)
        else:
            logger.warning(f"Unhandled alarm state: {new_state}")
    else:
        logger.error("Failed to retrieve the alias DNS name. No changes made.")

if __name__ == "__main__":
    # Example event payload for testing
    test_event = {
        "body": json.dumps({
            "Records": [
                {"Sns": {
                    "Message": {
                        "NewStateValue": "ALARM"
                    }
                }
            }]
        })
    }
    lambda_handler(test_event, None)
